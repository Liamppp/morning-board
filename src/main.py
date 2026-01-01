import os, sys, pygame, requests, feedparser, threading, ctypes
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image, ImageFont, ImageDraw
from email.utils import parsedate_to_datetime

# ENVIRONMENTS
load_dotenv()
service_key = os.environ.get('service_key')

# PYGAME SETTINGS
pygame.init()
screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)

# PIL
background_dir = os.path.join(os.getcwd(), 'assets', 'background')
background = Image.open(os.path.join(background_dir, 'news.png'))

# FONTS
font_dir = os.path.join(os.getcwd(), 'assets', 'font')

news_font = ImageFont.truetype(os.path.join(font_dir, 'NotoSansKR-Medium.ttf'), 50)
weather_font = ImageFont.truetype(os.path.join(font_dir, 'Pretendard-ExtraBold.ttf'), 70)
dust_font = ImageFont.truetype(os.path.join(font_dir, 'Pretendard-Regular.ttf'), 45)

date_font = ImageFont.truetype(os.path.join(font_dir, 'Pretendard-Black.ttf'), 225)
time_font = ImageFont.truetype(os.path.join(font_dir, 'Pretendard-Bold.ttf'), 75)

# DICTIONARIES
pty_dict = {
  '0': '맑음',
  '1': '비',
  '2': '비/눈',
  '3': '눈',
  '5': '빗방울',
  '6': '진눈깨비',
  '7': '눈날림'
}

pm10_grade_dict = {
  '1': '좋음',
  '2': '보통',
  '3': '나쁨',
  '4': '매우 나쁨'
}

# FUNCTIONS
def exception_msg(where: str, exception: Exception) -> str:
  return f'[{datetime.now().strftime('%H:%M')}] [EXCEPTION|{where}] {type(exception).__name__}: {exception}'

def exception_print(where: str, exception: Exception):
  print(exception_msg(where=where, exception=exception))

def info_msg(where: str, message: str):
  return f'[{datetime.now().strftime('%H:%M')}] [INFO|{where}] {message}'

def info_print(where: str, message: str):
  print(info_msg(where, message))

def draw_info(image):
  # DEFAULT
  now = datetime.now()
  draw = ImageDraw.Draw(image)

  # POSITIONS
  news_positions = [(475, 990), (475, 920), (475, 850)]
  temp_position = (150, 715)
  pty_position = (830, 715)
  pm10_positions = [(1485, 715), (1615, 735)]

  # FILLS
  news_fill = '#ffffff'
  weather_fill = '#000000'
  error_fill = '#808080'

  # NEWS
  try:
    url = "https://www.yna.co.kr/rss/news.xml"
    feed = feedparser.parse(url)

    for i, entry in enumerate(feed.entries[:3], 0):
      published = parsedate_to_datetime(entry.published).strftime('%H:%M')
      headline = f"[{published}] {entry.title}"

      draw.text(xy=news_positions[i], text=headline, fill=news_fill, font=news_font)

  except Exception as e:
    for i in range(3):
      draw.text(xy=news_positions[i], text='정보 없음', fill=error_fill, font=news_font)

    exception_print(where='NEWS', exception=e)

  # WEATHER    
  try:
    url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst'
    params = {
      'serviceKey': service_key,
      'pageNo': '1',
      'numOfRows': '10',
      'dataType': 'JSON',
      'base_date': now.strftime('%Y%m%d'),
      'base_time': now.strftime('%H00'),
      'nx': '60',
      'ny': '110'
    }
    data = requests.get(url=url, params=params).json()
    items = data['response']['body']['items']['item']

    weather_info = { item['category']: item['obsrValue'] for item in items }

    temp = weather_info['T1H']
    pty = weather_info['PTY']

    draw.text(xy=temp_position, text=f"{temp}℃", fill=weather_fill, font=weather_font)
    draw.text(xy=pty_position, text=pty_dict.get(pty), fill=weather_fill, font=weather_font)

  except Exception as e:
    draw.text(xy=temp_position, text="정보 없음", fill=error_fill, font=weather_font)
    draw.text(xy=pty_position, text="정보 없음", fill=error_fill, font=weather_font)

    exception_print(where='WEATHER', exception=e)

  # FINE_DUST
  try:
    url = 'http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMsrstnAcctoRltmMesureDnsty'
    params = {
      'serviceKey': service_key,
      'returnType': 'json',
      'numOfRows': '10',
      'pageNo': '1',
      'stationName': '모종동',
      'dataTerm': 'DAILY'
    }
    data = requests.get(url=url, params=params).json()
    items = data['response']['body']['items'][0]

    pm10_grade = pm10_grade_dict.get(items['pm10Grade'])
    pm10_value = items['pm10Value']

    draw.text(xy=pm10_positions[0], text=pm10_grade, fill=weather_fill, font=weather_font)
    
    if pm10_grade != '매우 나쁨':
      draw.text(xy=pm10_positions[1], text=f'({pm10_value}㎍/㎥)', fill=weather_fill, font=dust_font)

  except Exception as e:
    draw.text(xy=pm10_positions[0], text="정보 없음", fill=error_fill, font=weather_font)

    exception_print(where='FINE_DUST', exception=e)
  
  return image

def draw_datetime(image):
  # DEFAULT
  now = datetime.now()
  draw = ImageDraw.Draw(image)

  # FILLS
  default_fill = '#000000'

  # DATE
  draw.text(xy=(960, 225), text=now.strftime('%H:%M:%S'), fill=default_fill, font=date_font, anchor='mm')

  # TIME
  draw.text(xy=(960, 375), text=now.strftime('%Y년 %m월 %d일'), fill=default_fill, font=time_font, anchor='mm')

  return image

# RESOLUTION SETTING
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception as e:
    ctypes.windll.user32.SetProcessDPIAware()
    exception_print('RESOLUTION', e)

# PYGAME
clock = pygame.time.Clock()
updated = 0

info_image: Image.Image = draw_info(background.copy())

def update_info():
  global info_image
  try:
    info_image = draw_info(background.copy())
    info_print('UPDATE_INFO', '백그라운드에서 API 정보가 업데이트 되었습니다.')

  except Exception as e:
    exception_print('UPDATE_INFO', e)

while True:
  for event in pygame.event.get():
    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
      pygame.quit()
      sys.exit()

  if updated >= 120:
    threading.Thread(target=update_info, daemon=True).start()
    updated = 0
  
  image = draw_datetime(info_image.copy())
  screen.blit(pygame.image.fromstring(image.tobytes("raw", "RGBA"), (1920, 1080), "RGBA"), (0, 0))
  pygame.display.flip()

  clock.tick(1)
  updated += 1