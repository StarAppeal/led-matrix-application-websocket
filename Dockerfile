FROM balenalib/raspberry-pi-python:3.11-bullseye AS builder

RUN apt-get update && apt-get install -o Acquire::Retries=5 -y --no-install-recommends \
    build-essential make git python3-dev pkg-config libssl-dev curl \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python3 -m pip install --no-cache-dir --upgrade pip wheel setuptools
RUN python3 -m pip install --no-cache-dir "Cython>=0.29.30" && \
ln -s $(command -v cython) /usr/local/bin/cython3

COPY wheels/ /tmp/wheels/
RUN set -eux; \
    if ls /tmp/wheels/pillow-*.whl >/dev/null 2&>1; then \
        python3 -m pip install --no-cache-dir /tmp/wheels/pillow-*.whl; \
    else \
        echo "ERROR: Kein lokales Pillow-Wheel gefunden (wheels/pillow-*.whl). Abbruch."; \
        exit 42; \
    fi

COPY src/requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

RUN git clone --depth 1 https://github.com/hzeller/rpi-rgb-led-matrix.git && \
    cd rpi-rgb-led-matrix/bindings/python && \
    make build-python && \
    mkdir -p /app/rgbmatrix && \
    cp -r rgbmatrix/* /app/rgbmatrix

COPY src/led_matrix_application /app/led_matrix_application

FROM balenalib/raspberry-pi-python:3.11-bullseye-run
WORKDIR /app

RUN apt-get update && apt-get install -o Acquire::Retries=5 -y --no-install-recommends \
    libjpeg62-turbo libtiff5 libopenjp2-7 libfreetype6 \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.11/site-packages/

COPY --from=builder /app/led_matrix_application /app/
COPY --from=builder /app/rgbmatrix /app/rgbmatrix

ENV OPENSSL_DIR="/usr"
ENV OPENSSL_LIB_DIR="/usr/lib/arm-linux-gnueabihf"
ENV OPENSSL_INCLUDE_DIR="/usr/include"

# 4. Startbefehl
CMD ["python3", "main.py"]