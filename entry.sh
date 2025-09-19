#!/bin/bash
set -e

if [ "$ENV_TYPE" = "development" ]; then
  echo "INFO: Läuft im Entwicklungsmodus, verwende 'poetry run'."
  PYTHON_CMD="poetry run python3"
else
  echo "INFO: Läuft im Produktionsmodus, verwende 'python3'."
  PYTHON_CMD="python3"
fi

check_internet() {
  curl --silent --head --fail --connect-timeout 5 "http://www.google.com" >/dev/null 2>&1
}

if check_internet; then
  echo "Internet connection is available. Starting the main application..."
  cd /app
  exec $PYTHON_CMD led_matrix_application/main.py

else
  echo "No internet connection. Starting WiFi Connect in setup mode..."
  cd /app

  echo "starting setup mode led"
  $PYTHON_CMD led_matrix_application/run_setup_mode.py &

  echo "starting WiFi-Connect "
  /usr/local/sbin/wifi-connect portal-ssid "LED-Matrix-Setup" --portal-passphrase "12345678" --ui-directory /app/ui || true

  echo "WiFi configured! Restarting the container..."
  reboot
fi