# AME Compression

A high-performance video and audio compression tool using FFmpeg with SVT-AV1.
Featuring a modern, intuitive interface powered by Electron, React, and Flask.

## 🚀 Features

- **Modern Web Interface**: Powered by Electron + React for a sleek, responsive experience.
- **Video Compression**: Powered by SVT-AV1 for high efficiency and quality.
- **Audio Compression**: Convert various formats to high-quality MP3 (libmp3lame).
- **Smart Tools**: Automatic volume adjustment (normalization) and noise reduction.
- **Batch Processing**: Compress multiple files simultaneously with clear progress tracking.
- **Multilingual**: Supports both English and Japanese.

## 📥 Installation

### 1. Prerequisites (FFmpeg)

AmeCompression is distributed in two forms:

| Build Type | Description | Platforms |
|---|---|---|
| **Bundled** | FFmpeg binaries are included — no separate installation needed. | Windows |
| **Non-bundled** | FFmpeg must be installed on the system. | Windows / macOS / Linux |

For the **non-bundled** build, install FFmpeg on your system:

- **Windows**: `choco install ffmpeg` or download from [ffmpeg.org](https://ffmpeg.org/download.html)
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libgtk-3-0 libgbm1 libasound2`

Alternatively, you can place `ffmpeg` and `ffprobe` executables in a `bin/` folder inside the project root — they will be detected automatically at runtime.

### 2. Run from Source

Run the following command in the application root directory:

**macOS / Linux:**
```bash
make dev
```

**Windows:**
```bat
dev.bat
```

## 📄 Documentation

- [Migration Guide](documents/migration_guide.md) - Details on the architecture and setup.
- [Development Plan](documents/development_plan.md) - Project roadmap and goals.

## 🖥️ GUI Usage

1. **Launch**: Start the app via `npm run electron:dev` (dev) or the built executable.
2. **Add Files**: Drag and drop video/audio files into the application.
3. **Configure**: Adjust CRF (quality), Preset (speed), or enable Noise Reduction/Volume Gain.
4. **Process**: Select an output directory and click **Start**.

## 🛠️ Development & Build

```bash
# Backend
uv sync --extra dev

# Frontend
cd frontend
npm install
npm run build

# Build Standalone (using PyInstaller for backend)

# Non-bundled build (default — uses system FFmpeg at runtime)
uv run scripts/build.py

# Bundled build (includes FFmpeg binaries from bin/)
# First, place ffmpeg/ffprobe executables in the bin/ directory
uv run scripts/build.py --with-ffmpeg
```

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov

# Run linter / formatter check
uv run ruff check
uv run ruff format --check

# Run strict type check (warnings fail)
uv run pyright --warnings

# Frontend strict checks
npm --prefix frontend run lint:strict
npm --prefix frontend run format:check
```

## 📄 License

This project is licensed under the MIT License.

When using the **bundled** build, please also review `LICENSE_FFMPEG.txt` for
FFmpeg licensing information (LGPL v2.1+).
