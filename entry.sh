#!/bin/bash
set -e

check_internet() {
  curl --silent --head --fail --connect-timeout 5 "http://www.google.com" >/dev/null 2>&1
}

if check_internet; then
  echo "Internet connection is available. Starting the main application..."
  cd /app
  exec poetry run python3 led_matrix_application/main.py

else
  echo "No internet connection. Starting WiFi Connect in setup mode..."
  cd /app

  poetry run python3 led_matrix_application/run_setup_mode.py &

  /usr/local/sbin/wifi-connect --portal-passphrase "12345678" --ui-directory /app/ui || true

  echo "WiFi configured! Restarting the container..."
  reboot
fi