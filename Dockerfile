# --- Stage 1: Build-Abhängigkeiten und Kompilation ---
FROM --platform=linux/arm/v6 balenalib/raspberry-pi-python:3.11-bullseye AS builder

WORKDIR /app

# Erst nur pip und Python-Tools, damit Wheels genutzt werden
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3

# requirements.txt installieren (numpy wird jetzt aus Wheel gezogen)
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt

# Jetzt Build-Tools für native Module installieren
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    make \
    git \
    python3-dev \
    pkg-config \
    libssl-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Rest der App kopieren
COPY src/led_matrix_application /app/led_matrix_application

# rpi-rgb-led-matrix bauen
RUN git clone --depth 1 https://github.com/hzeller/rpi-rgb-led-matrix.git && \
    cd rpi-rgb-led-matrix/bindings/python && \
    make build-python && \
    mkdir "/app/led_matrix_application/rgbmatrix" && \
    cp -r rgbmatrix/* /app/led_matrix_application/rgbmatrix
RUN git clone --depth 1 https://github.com/hzeller/rpi-rgb-led-matrix.git && \
    cd rpi-rgb-led-matrix/bindings/python && \
    make build-python && \
    mkdir "/app/led_matrix_application/rgbmatrix" && \
    cp -r rgbmatrix/* /app/led_matrix_application/rgbmatrix

# --- Stage 2: Finales schlankes Image (use buster later?)---
FROM --platform=linux/arm/v6 balenalib/raspberry-pi-python:3.11-bullseye-run

# Arbeitsverzeichnis
WORKDIR /app

# Installiere fehlende Runtime-Abhängigkeiten
RUN apt-get update && apt-get install -o Acquire::Retries=5 -y --no-install-recommends \
    libtiff5 \
    libopenjp2-7 \
    libxcb1 \
    libxcb-render0 \
    libxcb-shm0 \
    libopenblas0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Kopiere nur die minimal notwendigen Dateien aus der Build-Stage
COPY --from=builder /app/led_matrix_application .
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11

# Setze ENV für OpenSSL
ENV OPENSSL_DIR="/usr"
ENV OPENSSL_LIB_DIR="/usr/lib/arm-linux-gnueabihf"
ENV OPENSSL_INCLUDE_DIR="/usr/include"

# Startbefehl für den Container
CMD ["python3", "main.py"]
