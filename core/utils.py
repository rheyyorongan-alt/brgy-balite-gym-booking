"""
utils.py  –  Barangay Gym Court Booking System
════════════════════════════════════════════════════════════════
Printing architecture:
    Django ──HTTP POST──► ESP32 ──UART TTL──► GOOJPRT 58mm Printer

Setup steps:
    1. Flash gym_printer.ino to the ESP32.
    2. Open Serial Monitor at 115200 baud to find the ESP32's IP.
    3. Set ESP32_IP below to that address.
    4. Run: pip install requests
════════════════════════════════════════════════════════════════
"""

import requests
import json
import logging
from .models import SystemConfiguration
from django.utils import timezone as dj_timezone
import socket

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
#  DEFAULTS  –  Can be overridden in SystemConfiguration
# ──────────────────────────────────────────────────────────────
DEFAULT_ESP32_IP         = "192.168.233.167"
DEFAULT_ESP32_PORT       = 80
DEFAULT_ESP32_AUTH_TOKEN = "brgy_gym_printer_2026"
PRINT_TIMEOUT            = 10
# ──────────────────────────────────────────────────────────────


def get_esp32_config():
    config = SystemConfiguration.objects.first()
    if not config:
        config = SystemConfiguration.objects.create()
    return config


def _build_esp32_url(config, endpoint):
    ip = config.esp32_ip or DEFAULT_ESP32_IP
    port = config.esp32_port or DEFAULT_ESP32_PORT
    return f"http://{ip}:{port}/{endpoint.lstrip('/')}"


def _build_auth_headers(config):
    return {
        "Content-Type": "application/json",
        "X-Printer-Token": config.esp32_auth_token or DEFAULT_ESP32_AUTH_TOKEN,
    }


def check_printer_status(config=None):
    """
    Ping the ESP32 to verify it is online.
    Returns (bool online, str message, dict status_data).
    """
    config = config or get_esp32_config()
    status_url = _build_esp32_url(config, "status")
    headers = _build_auth_headers(config)
    try:
        r = requests.get(status_url, headers=headers, timeout=3)
        if r.status_code == 200:
            d = r.json()
            ip = d.get('ip', config.esp32_ip or DEFAULT_ESP32_IP)
            ssid = d.get('ssid', '')
            status = d.get('status', 'ready')
            message = f"Online | IP: {ip} | {status}"
            if ssid:
                message += f" | SSID: {ssid}"
            return True, message, {
                'ip': ip,
                'ssid': ssid,
                'status': status,
            }
        if r.status_code == 403:
            return False, "ESP32 returned 403 Forbidden. Check the auth token.", {
                'ip': config.esp32_ip or DEFAULT_ESP32_IP,
                'ssid': '',
                'status': 'forbidden',
            }
        return False, f"ESP32 returned HTTP {r.status_code}: {r.text[:200]}", {
            'ip': config.esp32_ip or DEFAULT_ESP32_IP,
            'ssid': '',
            'status': 'error',
        }
    except requests.exceptions.ConnectionError:
        return False, f"Cannot reach ESP32 at {config.esp32_ip or DEFAULT_ESP32_IP}:{config.esp32_port or DEFAULT_ESP32_PORT}", {
            'ip': config.esp32_ip or DEFAULT_ESP32_IP,
            'ssid': '',
            'status': 'offline',
        }
    except Exception as exc:
        return False, str(exc), {
            'ip': config.esp32_ip or DEFAULT_ESP32_IP,
            'ssid': '',
            'status': 'error',
        }


def scan_esp32_wifi_networks(config=None):
    config = config or get_esp32_config()
    scan_url = _build_esp32_url(config, "scan")
    headers = _build_auth_headers(config)
    try:
        response = requests.get(scan_url, headers=headers, timeout=PRINT_TIMEOUT)
    except requests.exceptions.ConnectionError:
        return False, f"Cannot reach ESP32 at {config.esp32_ip or DEFAULT_ESP32_IP}:{config.esp32_port or DEFAULT_ESP32_PORT}"
    except Exception as exc:
        return False, str(exc)

    if response.status_code != 200:
        return False, f"ESP32 scan failed with HTTP {response.status_code}: {response.text[:200]}"

    try:
        data = response.json()
    except ValueError:
        return False, "ESP32 returned invalid JSON for Wi-Fi scan."

    if not isinstance(data, list):
        return False, "ESP32 scan response is not a list."

    networks = []
    for item in data:
        ssid = item.get('ssid', '')
        if not ssid:
            continue
        frequency = item.get('frequency')
        channel = item.get('channel')
        band = str(item.get('band', '')).lower()
        is_24ghz = False
        if '2.4' in band:
            is_24ghz = True
        elif frequency is not None:
            try:
                is_24ghz = int(frequency) < 3000
            except (ValueError, TypeError):
                pass
        elif channel is not None:
            try:
                is_24ghz = int(channel) <= 14
            except (ValueError, TypeError):
                pass

        if not is_24ghz:
            continue

        networks.append({
            'ssid': ssid,
            'rssi': item.get('rssi'),
            'encryption': item.get('encryption', 'unknown'),
            'frequency': frequency,
            'channel': channel,
            'band': item.get('band', '2.4GHz'),
        })

    networks.sort(key=lambda x: x.get('rssi', -999), reverse=True)
    return True, networks


def discover_esp32_on_local_network(config=None, timeout=0.6):
    """Scan the local /24 subnet for an ESP32 responding to /status with the configured token.

    Returns (True, ip) if found, otherwise (False, error_message).
    """
    config = config or get_esp32_config()
    port = config.esp32_port or DEFAULT_ESP32_PORT
    headers = _build_auth_headers(config)

    # Determine local IP to derive subnet
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # doesn't need to be reachable
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        return False, 'Unable to determine local network interface IP.'

    parts = local_ip.split('.')
    if len(parts) != 4:
        return False, f'Unexpected local IP format: {local_ip}'

    subnet = '.'.join(parts[:3])

    import requests
    for i in range(1, 255):
        ip = f"{subnet}.{i}"
        # skip our own host
        if ip == local_ip:
            continue
        url = f'http://{ip}:{port}/status'
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            if r.status_code == 200:
                # quick validation of expected JSON
                try:
                    d = r.json()
                    if isinstance(d, dict) and d.get('ok', True):
                        return True, ip
                except Exception:
                    return True, ip
        except Exception:
            continue

    return False, 'No ESP32 status endpoint found on local /24 subnet.'


def connect_esp32_wifi(ssid, password, config=None):
    if not ssid:
        return False, "SSID is required for ESP32 Wi-Fi connection."

    config = config or get_esp32_config()
    wifi_url = _build_esp32_url(config, "wifi")
    headers = _build_auth_headers(config)
    payload = {
        'ssid': ssid,
        'password': password or '',
    }
    try:
        response = requests.post(wifi_url, headers=headers, json=payload, timeout=PRINT_TIMEOUT)
    except requests.exceptions.ConnectionError:
        return False, f"Cannot reach ESP32 at {config.esp32_ip or DEFAULT_ESP32_IP}:{config.esp32_port or DEFAULT_ESP32_PORT}"
    except Exception as exc:
        return False, str(exc)

    if response.status_code != 200:
        return False, f"ESP32 connect failed with HTTP {response.status_code}: {response.text[:200]}"

    try:
        result = response.json()
    except ValueError:
        return False, "ESP32 returned invalid JSON when attempting to connect."

    if result.get('success'):
        return True, result.get('message', 'ESP32 Wi-Fi connect request sent successfully.')
    return False, result.get('message', f"ESP32 returned an error: {result}")


def _build_payload(booking) -> dict:
    """
    Assemble the JSON payload sent to the ESP32.
    """
    config = SystemConfiguration.objects.first()
    if not config:
        raise ValueError(
            "System Configuration not found. "
            "Please add one via Django Admin → System Configuration."
        )

    return {
        # ── Header ───────────────────────────────────────────
        "barangay_name":  config.barangay_name,
        "contact":        config.contact_info,
        "receipt_header": config.receipt_header,

        # ── Receipt meta ─────────────────────────────────────
        "receipt_number": booking.receipt_number,
        # Use localtime() so the issued timestamp reflects the server's local timezone
        "date_issued":    dj_timezone.localtime(booking.created_at).strftime("%b %d, %Y  %I:%M %p"),

        # ── Booking details ───────────────────────────────────
        "event_name":     booking.event_name,
        "customer_name":  booking.customer_name,
        "contact_number": booking.contact_number,
        "date_of_event":  booking.date_display_with_day,
        "time_info": (
            f"{booking.start_time.strftime('%I:%M %p')}  "
            f"({booking.duration_hours} hr{'s' if booking.duration_hours != 1 else ''})"
        ),

        # ── Payment status only ───────────────────────────────
        "payment_status": booking.get_payment_status_display(),

        # ── Footer ────────────────────────────────────────────
        "receipt_footer": config.receipt_footer,
    }


def print_to_hardware(booking):
    """
    Send a receipt print job to the ESP32 printer bridge.

    Returns:
        (True,  "success message")
        (False, "error message")
    """
    try:
        payload = _build_payload(booking)
    except ValueError as exc:
        return False, str(exc)

    config = get_esp32_config()
    headers = _build_auth_headers(config)
    print_url = _build_esp32_url(config, "print")

    logger.info(
        "[print] Sending to ESP32 – Receipt: %s | Customer: %s | URL: %s",
        booking.receipt_number, booking.customer_name, print_url,
    )

    try:
        response = requests.post(
            print_url,
            data=json.dumps(payload),
            headers=headers,
            timeout=PRINT_TIMEOUT,
        )

    except requests.exceptions.ConnectionError:
        msg = (
            f"Cannot connect to ESP32 at {config.esp32_ip or DEFAULT_ESP32_IP}:{config.esp32_port or DEFAULT_ESP32_PORT}. "
            "Checklist:\n"
            "  1. Is the ESP32 powered on?\n"
            "  2. Is ESP32 on the same WiFi as this server?\n"
            "  3. Is the ESP32 IP address and port in System Configuration correct?\n"
        )
        logger.error("[print] ConnectionError – %s", msg)
        return False, msg

    except requests.exceptions.Timeout:
        msg = (
            f"ESP32 did not respond within {PRINT_TIMEOUT}s. "
            "The printer may be busy. Try again."
        )
        logger.error("[print] Timeout – %s", msg)
        return False, msg

    except Exception as exc:
        logger.exception("[print] Unexpected error")
        return False, f"Unexpected error: {exc}"

    if response.status_code == 200:
        logger.info("[print] Success – %s", booking.receipt_number)
        return True, "Receipt sent to printer successfully."

    if response.status_code == 403:
        return False, (
            "ESP32 rejected the request (wrong token). "
            "Make sure the ESP32 auth token saved in System Configuration "
            "matches AUTH_TOKEN in the firmware."
        )

    return False, (
        f"ESP32 returned HTTP {response.status_code}: {response.text[:200]}"
    )