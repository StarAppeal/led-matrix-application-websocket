# --- Stage 1: Build-Abhängigkeiten und Kompilation ---
FROM balenalib/raspberry-pi-python:3.9-bullseye AS builder
# ^ Tipp: KEIN --platform im Dockerfile erzwingen. Buildx setzt das pro Zielarchitektur.

WORKDIR /app

RUN apt-get update && apt-get install -o Acquire::Retries=5 -o Acquire::http::Timeout="60" -y --no-install-recommends \
    build-essential make git python3-dev pkg-config libssl-dev python3-pip curl \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Frisches pip + Cython
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3
RUN python3 -m pip install --no-cache-dir "Cython>=0.29.30" && ln -s $(command -v cython) /usr/bin/cython3

# --- Wichtig: Das vorbereitete Wheel in den Container holen ---
# Damit COPY funktioniert, erzeugen wir im Workflow IMMER einen 'wheels'-Ordner.
COPY wheels/ /tmp/wheels/

# Installiere Pillow NUR aus dem lokalen Wheel. Falls keins da: fail hart und sichtbar.
RUN set -eux; \
    if ls /tmp/wheels/Pillow-*.whl >/dev/null 2>&1; then \
        python3 -m pip install --no-cache-dir /tmp/wheels/Pillow-*.whl; \
    else \
        echo "ERROR: Kein lokales Pillow-Wheel gefunden (wheels/Pillow-*.whl). Abbruch."; \
        exit 42; \
    fi

# Jetzt erst die restlichen Requirements
COPY src/requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt && rm requirements.txt

# App rein
COPY src/led_matrix_application /app/led_matrix_application

# RGB-LED-Matrix bauen
RUN git clone --depth 1 https://github.com/hzeller/rpi-rgb-led-matrix.git && \
    cd rpi-rgb-led-matrix/bindings/python && \
    make build-python && \
    mkdir -p "/app/led_matrix_application/rgbmatrix" && \
    cp -r rgbmatrix/* /app/led_matrix_application/rgbmatrix

# --- Stage 2: Runtime-Image ---
FROM balenalib/raspberry-pi-python:3.9-bullseye-run
WORKDIR /app

RUN apt-get update && apt-get install -o Acquire::Retries=5 -y --no-install-recommends \
    libjpeg62-turbo libtiff5 libopenjp2-7 libfreetype6 \
    libxcb1 libxcb-render0 libxcb-shm0 libopenblas0 \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/led_matrix_application .
COPY --from=builder /usr/local/lib/python3.9 /usr/local/lib/python3.9

ENV OPENSSL_DIR="/usr"
ENV OPENSSL_LIB_DIR="/usr/lib/arm-linux-gnueabihf"
ENV OPENSSL_INCLUDE_DIR="/usr/include"

CMD ["python3", "main.py"]
