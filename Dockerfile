FROM --platform=linux/arm/v6 balenalib/raspberry-pi-python:3.8-buster-run

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    make \
    git \
    python3-dev \
    cython3 \
    libgraphicsmagick++-dev \
    libsdl2-dev \
    libssl-dev \
    pkg-config \
    curl \
    && curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    export PATH="$HOME/.cargo/bin:$PATH" && \
    rustc --version && \
    cargo --version && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.cargo/bin:${PATH}"

ENV OPENSSL_DIR="/usr"
ENV OPENSSL_LIB_DIR="/usr/lib/arm-linux-gnueabihf"
ENV OPENSSL_INCLUDE_DIR="/usr/include"

RUN git clone --depth 1 https://github.com/hzeller/rpi-rgb-led-matrix.git && \
    cd rpi-rgb-led-matrix && \
    make build-python && \
    make install-python && \
    cd ..

RUN pip install --no-cache-dir poetry==1.5.1

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --no-dev --no-root

COPY . .

ENV LED_CONFIG="production"

CMD ["python3", "led_matrix_application/main.py"]
