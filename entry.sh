#!/bin/bash
set -e

check_internet() {
  curl --silent --head --fail --connect-timeout 5 "http://www.google.com" >/dev/null 2>&1
}

if check_internet; then
  echo "Internetverbindung ist vorhanden. Starte die Hauptanwendung..."
  cd /app
  exec poetry run python3 led_matrix_application/main.py

else
  echo "Keine Internetverbindung. Starte WiFi Connect im Setup-Modus..."
  cd /app

  poetry run python3 led_matrix_application/run_setup_mode.py &

  /usr/local/sbin/wifi-connect --portal-passphrase "12345678" --ui-directory /app/ui || true

  echo "WLAN konfiguriert! Starte den Container neu..."
  reboot
fi