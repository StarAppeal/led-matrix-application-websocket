FROM --platform=linux/arm/v6 balenalib/raspberry-pi-python:3.9-bullseye

# Arbeitsverzeichnis für Installationen und temporäre Dateien
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
    libtiff5 \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Repariere und aktualisiere Pip
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3

# Installiere eine neuere Version von Cython
RUN python3 -m pip install --no-cache-dir --ignore-installed "Cython>=0.29.30" && \
    ln -s $(command -v cython) /usr/bin/cython3

# Kopiere den Source Code und installiere Python-Abhängigkeiten
COPY src/ /app/
RUN pip install --no-cache-dir -r requirements.txt

# RPI-RGB-LED-Matrix bauen und rgbmatrix kopieren
RUN git clone --depth 1 https://github.com/hzeller/rpi-rgb-led-matrix.git && \
    cd rpi-rgb-led-matrix/bindings/python && \
    make build-python && \
    mkdir "/app/led_matrix_application/rgbmatrix" && \
    cp -r rgbmatrix/* /app/led_matrix_application/rgbmatrix

# Arbeitsverzeichnis wechseln für den Start des Codes
WORKDIR /app/led_matrix_application

# Startbefehl für den Container
CMD ["python3", "main.py"]
