# Contributing to AmeCompression

Thank you for your interest in contributing to AmeCompression! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.10 or later
- [uv](https://docs.astral.sh/uv/) package manager
- FFmpeg (for testing compression features)
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/tarminjapan/AmeCompression.git
cd AmeCompression

# Install dependencies
uv sync --extra dev

# Install pre-commit hooks (optional but recommended)
uv run pre-commit install
```

### Project Structure

```text
AmeCompression/
├── frontend/               # Electron + React interface
│   ├── src/                # React source code
│   ├── electron/           # Electron main/preload scripts
│   └── package.json        # Frontend dependencies
├── backend/       # Backend package (engine & API)
│   ├── api/                # Flask REST API
│   ├── cli.py              # CLI interface
│   ├── config.py           # Configuration constants
│   ├── ffmpeg.py           # FFmpeg detection and media info
│   ├── video.py            # Video compression
│   ├── audio.py            # Audio compression
│   ├── volume.py           # Volume analysis and adjustment
│   └── utils.py            # Common utility functions
├── tests/                  # Test files (pytest)
├── scripts/                # Build and utility scripts
├── AmeCompression.spec     # PyInstaller spec file
└── pyproject.toml          # Backend project configuration
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout main
git pull
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write clean, readable code following the existing style
- Follow the coding conventions described below

### 3. Run Quality Checks

Before committing, run all quality checks:

```bash
# Backend: Linting
uv run ruff check backend tests

# Backend: Formatting check
uv run ruff format --check backend tests

# Backend: Type checking
uv run pyright --warnings

# Backend: Tests
uv run pytest tests -v

# Frontend: Linting
cd frontend && npm run lint:strict

# Frontend: Formatting check
cd frontend && npm run format:check
```

### 4. Commit and Push

```bash
git add .
git commit -m "Description of your changes"
git push -u origin feature/your-feature-name
```

### 5. Create a Pull Request

- Create a PR targeting the `main` branch
- Include a clear description of the changes
- Reference any related issues

## Coding Conventions

### Python Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guidelines
- Use `ruff` for linting and formatting
- Line length: 100 characters max
- Use double quotes for strings
- Use type hints for function signatures

### Code Quality

- All code must pass `ruff check` with no warnings/errors
- All code must pass `ruff format --check`
- All code must pass `pyright --warnings` (warnings are treated as failures)
- Frontend code must pass `eslint --max-warnings=0`
- Frontend code must pass `prettier --check`
- Do **not** use `# type: ignore`, `# noqa`, or `eslint-disable` to suppress errors. All errors must be fixed properly. Error suppression comments are strictly prohibited.
- All tests must pass

### Testing

- Write tests for new functionality
- Place test files in the `tests/` directory
- Follow the naming convention: `test_<module_name>.py`
- Use pytest fixtures from `conftest.py` for shared setup

### Internationalization (i18n)

- All user-facing strings in the GUI must use the translation system
- Add new keys to both `en.json` and `ja.json`
- Use dot-notation keys (e.g., `"settings.title"`)
- Test that both language files have matching keys

## Pull Request Guidelines

- Keep PRs focused on a single feature or fix
- Include tests for new functionality
- Update documentation if applicable
- Ensure all CI checks pass
- Be responsive to code review feedback

## Reporting Issues

- Use GitHub Issues to report bugs or request features
- Include steps to reproduce for bugs
- Include your Python version and OS

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
