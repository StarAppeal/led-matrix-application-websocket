# --- Stage 1: Build-Abhängigkeiten und Kompilation ---
FROM --platform=linux/arm/v6 balenalib/raspberry-pi-python:3.9-bullseye AS builder

# Arbeitsverzeichnis
WORKDIR /app

# Systempakete installieren
RUN apt-get update && apt-get install -o Acquire::Retries=5 -o Acquire::http::Timeout="60" -y --no-install-recommends \
    build-essential \
    make \
    git \
    python3-dev \
    python3-pip \
    pkg-config \
    libssl-dev \
    libgraphicsmagick++-dev \
    libsdl2-dev \
    libopenjp2-7 \
    libopenblas-dev \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Aktualisiere Pip und installiere Cython
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3
RUN python3 -m pip install --no-cache-dir "Cython>=0.29.30" && \
    ln -s $(command -v cython) /usr/bin/cython3

# Kopiere den Source Code und installiere Python-Abhängigkeiten
COPY src/ /app/
RUN pip install --no-cache-dir -r requirements.txt

# RPI-RGB-LED-Matrix bauen
RUN git clone --depth 1 https://github.com/hzeller/rpi-rgb-led-matrix.git && \
    cd rpi-rgb-led-matrix/bindings/python && \
    make build-python && \
    mkdir "/app/led_matrix_application/rgbmatrix" && \
    cp -r rgbmatrix/* /app/led_matrix_application/rgbmatrix

# --- Stage 2: Finales schlankes Image ---
FROM --platform=linux/arm/v6 balenalib/raspberry-pi-python:3.9-bullseye-run

# Arbeitsverzeichnis
WORKDIR /app

# Kopiere nur die minimal notwendigen Dateien aus der Build-Stage
COPY --from=builder /app/led_matrix_application /app/led_matrix_application
COPY --from=builder /usr/local/lib/python3.9 /usr/local/lib/python3.9

# Setze ENV für OpenSSL
ENV OPENSSL_DIR="/usr"
ENV OPENSSL_LIB_DIR="/usr/lib/arm-linux-gnueabihf"
ENV OPENSSL_INCLUDE_DIR="/usr/include"

# Startbefehl für den Container
WORKDIR /app/led_matrix_application
CMD ["python3", "main.py"]
