# AmeCompression Migration & Release Guide (Issue #50)

This document outlines the transition from the CustomTkinter-based GUI to the new Electron + React + Flask architecture, along with operational requirements and development setup instructions.

## 🏗️ New Architecture Overview

The application has migrated from a pure Python GUI (CustomTkinter) to a modern web-based desktop application:

- **Frontend**: Electron + React (TypeScript) + Vite
- **Backend**: Flask API (Python)
- **Communication**: REST API (localhost:5000)

This change allows for a more responsive UI, better cross-platform consistency, and a more robust separation of concerns between the media processing logic and the user interface.

## 🛠️ Developer Setup Instructions

To set up the development environment for the new architecture, follow these steps:

### 1. Python Environment (Backend)

We recommend using `uv` for managing Python dependencies.

```bash
# Install dependencies
uv sync --extra dev

# Run the API server manually (optional, Electron starts it automatically)
uv run python -m backend --api --port 5000 --config dev
```

### 2. Node.js Environment (Frontend)

Ensure you have Node.js (v18+) installed.

```bash
# Go to the frontend directory
cd frontend

# Install dependencies
npm install

# Start development mode (Vite + Electron)
npm run electron:dev
```

## ⚙️ FFmpeg Placement & Configuration

The application requires `ffmpeg` and `ffprobe`. There are two ways to provide these:

1. **System PATH**: Install FFmpeg globally so it's accessible via the command line.
2. **Local `bin/` Directory**: Place the `ffmpeg` and `ffprobe` (or `ffmpeg.exe` and `ffprobe.exe` on Windows) executables in a directory named `bin` at the **root of the project repository**.

The backend automatically detects local executables in the `bin/` folder before falling back to the system PATH.

## ⚠️ Compatibility & Constraints

- **CLI Mode**: The CLI version (`uv run python -m backend <input>`) remains fully compatible and functional.
- **Port Conflict**: The Flask backend defaults to port `5000`. Ensure this port is not in use by other services (e.g., macOS AirPlay Receiver).
- **CORS**: The API is configured to only allow requests from the Electron app (`app://.`) and the Vite development server (`http://localhost:5173`).

## 🚀 Release Procedure

1. **Version Update**: Increment the version in `pyproject.toml` and `frontend/package.json`.
2. **Build Frontend**: Run `npm run build` in the `frontend` directory.
3. **Build Executable**: Use `uv run scripts/build.py` to create the standalone executable.
4. **Verification**:
    - Run all Python tests: `uv run pytest tests`
    - Verify FFmpeg detection status in the settings view.
    - Perform a test compression flow for both video and audio.
