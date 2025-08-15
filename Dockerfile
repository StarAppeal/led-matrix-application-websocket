# --- Stage 1: Build-Abhängigkeiten und Kompilation ---
FROM --platform=linux/arm/v6 balenalib/raspberry-pi-python:3.9-bullseye AS builder

ENV NPY_BLAS_ORDER=none
ENV NPY_LAPACK_ORDER=none

WORKDIR /app

RUN apt-get update && apt-get install -o Acquire::Retries=5 -o Acquire::http::Timeout="60" -y --no-install-recommends \
    build-essential make git python3-dev pkg-config libssl-dev python3-pip curl \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Frisches pip + Cython
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3
RUN python3 -m pip install --no-cache-dir "Cython>=0.29.30" && ln -s $(command -v cython) /usr/bin/cython3

# >>> Hier: VOR requirements das ARMv6-Pillow-Wheel installieren
#    wheels/ liegt im Build Context (Repo-Root) durch den Workflow
COPY wheels/ /tmp/wheels/
RUN ls -l /tmp/wheels && python3 -m pip install --no-cache-dir /tmp/wheels/Pillow-*.whl

# Jetzt erst requirements installieren (Pillow ist bereits satisfied)
COPY src/requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt && rm requirements.txt

# App kopieren
COPY src/led_matrix_application /app/led_matrix_application

# RPI-RGB-LED-Matrix bauen
RUN git clone --depth 1 https://github.com/hzeller/rpi-rgb-led-matrix.git && \
    cd rpi-rgb-led-matrix/bindings/python && \
    make build-python && \
    mkdir -p "/app/led_matrix_application/rgbmatrix" && \
    cp -r rgbmatrix/* /app/led_matrix_application/rgbmatrix

# --- Stage 2: Finales schlankes Image ---
FROM --platform=linux/arm/v6 balenalib/raspberry-pi-python:3.9-bullseye-run

WORKDIR /app

# Runtime-Libs für Pillow (damit das Wheel sauber lädt)
RUN apt-get update && apt-get install -o Acquire::Retries=5 -y --no-install-recommends \
    libjpeg62-turbo libtiff5 libopenjp2-7 libfreetype6 \
    libxcb1 libxcb-render0 libxcb-shm0 libopenblas0 \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Nur das Nötigste aus der Build-Stage
COPY --from=builder /app/led_matrix_application .
COPY --from=builder /usr/local/lib/python3.9 /usr/local/lib/python3.9

ENV OPENSSL_DIR="/usr"
ENV OPENSSL_LIB_DIR="/usr/lib/arm-linux-gnueabihf"
ENV OPENSSL_INCLUDE_DIR="/usr/include"

CMD ["python3", "main.py"]
