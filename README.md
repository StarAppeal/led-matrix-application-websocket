# LED Matrix Application WebSocket

## Overview
This project provides a WebSocket-based LED Matrix Application that can display content on RGB LED matrices. The application is designed to run on Raspberry Pi hardware or locally using an emulator for development purposes.

## Features
- WebSocket communication for real-time control
- RGB LED matrix support via rpi-rgb-led-matrix library
- Local development with emulator support
- Docker containerization for easy deployment
- Poetry-based dependency management

## Development Setup

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Poetry (for dependency management)

### Docker Compose Development Environment

The easiest way to develop is using Docker Compose, which provides a complete development environment:

1. **Start the development container:**
   ```bash
   docker-compose up -d
   ```

2. **Access the container shell:**
   ```bash
   docker-compose exec led-matrix-dev bash
   ```

3. **Run the application inside the container:**
   ```bash
   poetry run python3 led_matrix_application/main.py
   ```

4. **Stop the development environment:**
   ```bash
   docker-compose down
   ```

### Local Development (without Docker)

1. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Install dependencies:**
   ```bash
   cd src
   poetry install
   ```

3. **Run the application:**
   ```bash
   poetry run python3 led_matrix_application/main.py
   ```

## Production Deployment

### Pulling the Docker Image
To pull the latest Docker image from the GitHub Container Registry (GHCR):

```bash
podman pull ghcr.io/starappeal/led-matrix-application-websocket:latest
```

### Running on Raspberry Pi
When running on a Raspberry Pi, you **must run the container as privileged** to access hardware resources:

```bash
podman run --rm -it --privileged --env-file .env ghcr.io/starappeal/led-matrix-application-websocket:latest
```

### Running Locally with Emulator
For local testing with the emulator:

```bash
podman run --rm -it --env-file .env -p 8888:8888 ghcr.io/starappeal/led-matrix-application-websocket:latest
```

## Configuration

### Environment Variables
Create a `.env` file with the following variables:

- `USE_EMULATOR`: Set to `True` when running locally to use the RGBMatrixEmulator
- `WEBSOCKET_URL`: The URL of the WebSocket server the application will connect to
- `JWT_TOKEN`: The JWT token used for authentication

### Example `.env` File
```env
USE_EMULATOR=True
WEBSOCKET_URL=wss://example.com/socket
JWT_TOKEN=your-jwt-token-here
```

## Project Structure
```
led-matrix-application-websocket/
├── src/
│   ├── led_matrix_application/
│   │   ├── main.py              # Application entry point
│   │   ├── controller/          # LED matrix controller logic
│   │   ├── ws/                  # WebSocket client implementation
│   │   ├── utils/               # Utility functions
│   │   └── fonts/               # Font files for text rendering
│   ├── pyproject.toml           # Poetry configuration
│   └── poetry.lock              # Locked dependencies
├── wheels/                      # Pre-built wheels (for Raspberry Pi)
├── Dockerfile                   # Production Docker image
├── Dockerfile.dev               # Development Docker image
├── docker-compose.yml           # Development environment
└── README.md                    # This file
```

## Dependencies
- **Python 3.11+**: Core runtime
- **websockets**: WebSocket client communication
- **Pillow**: Image processing for LED matrix
- **python-dotenv**: Environment variable management
- **rpi-rgb-led-matrix**: Hardware interface for RGB LED matrices
- **rgbmatrixemulator**: Development emulator (dev dependency)

## Troubleshooting

### Common Issues
1. **Permission errors on Raspberry Pi**: Ensure the container runs with `--privileged` flag
2. **WebSocket connection issues**: Verify `WEBSOCKET_URL` and `JWT_TOKEN` are correct
3. **Emulator not working**: Ensure `USE_EMULATOR=True` is set in your `.env` file

### Debugging
- Check container logs: `docker logs <container_id>` or `docker-compose logs`
- Access development container: `docker-compose exec led-matrix-dev bash`
- Run with verbose logging by setting appropriate log levels in the application

### Development Tips
- Use the Docker Compose setup for consistent development environment
- The development container includes volume mounts for live code reloading
- X11 forwarding is configured for emulator display on host systems

