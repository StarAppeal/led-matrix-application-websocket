# LED Matrix Application Docker Image

## Overview
This project provides a Docker image for running the LED Matrix Application. The application can be configured and run either on a Raspberry Pi or locally using an emulator.

## Pulling the Docker Image
To pull the latest Docker image from the GitHub Container Registry (GHCR), run the following command:

```bash
podman pull ghcr.io/starappeal/led-matrix-application-websocket:latest
```

## Running the Docker Image
### On a Raspberry Pi
When running on a Raspberry Pi, you **must run the container as privileged** to access hardware resources. Use the following command:

```bash
podman run --rm -it --privileged --env-file .env ghcr.io/starappeal/led-matrix-application-websocket:latest
```

### Locally with Emulator
If running locally (e.g., on your development machine), ensure the `.env` file contains the following environment variables:

```env
USE_EMULATOR=True
WEBSOCKET_URL=<Your WebSocket URL>
JWT_TOKEN=<Your JWT Token>
```

Use the following command to start the container locally:

```bash
podman run --rm -it --env-file .env -p 8888:8888 ghcr.io/starappeal/led-matrix-application-websocket:latest
```

### Environment Variables
The `.env` file must include the following variables:

- `USE_EMULATOR`: Set to `True` when running locally to use the RGBMatrixEmulator.
- `WEBSOCKET_URL`: The URL of the WebSocket server the application will connect to.
- `JWT_TOKEN`: The JWT token used for authentication.

## Example `.env` File
Here is an example `.env` file:

```env
USE_EMULATOR=True
WEBSOCKET_URL=wss://example.com/socket
JWT_TOKEN=your-jwt-token-here
```

## Notes
- **Raspberry Pi Users**: Ensure the container is run with `--privileged` to allow access to GPIO and hardware resources.
- **Local Development**: The `USE_EMULATOR=True` flag enables the emulator to simulate the LED matrix locally.

## Troubleshooting
If you encounter issues:
1. Ensure all required environment variables are set correctly in the `.env` file.
2. Verify that the container is run with `--privileged` on the Raspberry Pi.
3. Check the logs for error messages using:

   ```bash
   podman logs <container_id>
   ```

