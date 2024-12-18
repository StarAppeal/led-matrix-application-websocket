FROM --platform=linux/arm/v6 balenalib/raspberry-pi-python:3.9-bullseye-run

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
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Repariere und aktualisiere Pip
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3

# Installiere eine neuere Version von Cython
RUN python3 -m pip install --no-cache-dir --ignore-installed "Cython>=0.29.30" && \
    ln -s $(command -v cython) /usr/bin/cython3

# Setze Pfade für Rust und OpenSSL
ENV PATH="/root/.cargo/bin:${PATH}"
ENV OPENSSL_DIR="/usr"
ENV OPENSSL_LIB_DIR="/usr/lib/arm-linux-gnueabihf"
ENV OPENSSL_INCLUDE_DIR="/usr/include"

# Source Code in das Image kopieren
COPY src/ /app/

RUN cat requirements.txt
RUN pip install -r requirements.txt

# RPI-RGB-LED-Matrix bauen und rgbmatrix kopieren
RUN git clone --depth 1 https://github.com/hzeller/rpi-rgb-led-matrix.git && \
    cd rpi-rgb-led-matrix/bindings/python && \
    make build-python && \
    make install-python && \
    mkdir "/app/led_matrix_application/rgbmatrix" && \
    echo "Copying rgbmatrix to /app/led_matrix_application/rgbmatrix" && \
    cp -r rgbmatrix/* /app/led_matrix_application/rgbmatrix

# Arbeitsverzeichnis wechseln für den Start des Codes
WORKDIR /app/led_matrix_application

RUN rm /app/requirements.txt && \
    rm -rf /app/rpi-rgb-led-matrix && \
    rm -rf /app/poetry.lock && \
    rm -rf /app/pyproject.toml

# Startbefehl für den Container
CMD ["python3", "main.py"]
