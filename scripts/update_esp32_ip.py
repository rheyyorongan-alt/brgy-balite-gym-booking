# Script to update SystemConfiguration.esp32_ip
from core.models import SystemConfiguration

c = SystemConfiguration.objects.first()
if not c:
    c = SystemConfiguration()

c.esp32_ip = '192.168.1.51'
c.save()
print('Saved esp32_ip:', c.esp32_ip)
