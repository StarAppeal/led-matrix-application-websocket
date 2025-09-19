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
        echo "ERROR: No local Pillow wheel found (wheels/pillow-*.whl). Aborting."; \
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

FROM balenalib/raspberry-pi-python:3.11-bullseye-run AS final
WORKDIR /app

RUN apt-get update && apt-get install -o Acquire::Retries=5 -y --no-install-recommends \
    libjpeg62-turbo libtiff5 libopenjp2-7 libfreetype6 network-manager curl libdbus-1-3 \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

ARG WIFICONNECT_VERSION=4.11.84
RUN set -eux; \
    ARCH=$(dpkg --print-architecture); \
    if [ "$ARCH" = "amd64" ]; then \
      WIFI_CONNECT_FILE="wifi-connect-x86_64-unknown-linux-gnu.tar.gz"; \
    elif [ "$ARCH" = "armhf" ] || [ "$ARCH" = "armel" ]; then \
      WIFI_CONNECT_FILE="wifi-connect-armv7-unknown-linux-gnueabihf.tar.gz"; \
    else \
      echo "Unsupported architecture: $ARCH"; exit 1; \
    fi; \
    curl -L -o /tmp/wifi-connect.tar.gz "https://github.com/balena-io/wifi-connect/releases/download/v${WIFICONNECT_VERSION}/${WIFI_CONNECT_FILE}"; \
    tar -xzf /tmp/wifi-connect.tar.gz -C /usr/local/sbin; \
    rm /tmp/wifi-connect.tar.gz

COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /app/led_matrix_application /app/
COPY --from=builder /app/rgbmatrix /app/rgbmatrix

COPY src/entry.sh /usr/bin/entry.sh
COPY src/led_matrix_application/run_setup_mode.py /app/led_matrix_application/run_setup_mode.py
COPY ui/ /app/ui

RUN chmod +x /usr/bin/entry.sh

ENV DBUS_SYSTEM_BUS_ADDRESS unix:path=/host/run/dbus/system_bus_socket

RUN sed -i 's/\r$//' /usr/bin/entry.sh

CMD ["/usr/bin/entry.sh"]