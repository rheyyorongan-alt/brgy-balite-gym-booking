import os
import sys
import django
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_booking.settings')
django.setup()
from django.utils import timezone as dj_timezone
from django.conf import settings
now = dj_timezone.now()
print('TIME_ZONE:', settings.TIME_ZONE)
print('USE_TZ:', settings.USE_TZ)
print('now (aware):', now)
print('localtime:', dj_timezone.localtime(now).strftime('%b %d, %Y  %I:%M %p'))
