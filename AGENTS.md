# AGENTS.md — AmeCompression AI Agent Protocol

> **This document is the absolute law for every AI agent working on this project.**
> Read it. Internalize it. Execute with zero compromise.

---

## 0. THE SINGLE DIRECTIVE

**This project must become the world's best video and audio compression application.**

Not "world-class." Not "competitive." **World's #1.** Every line of code, every pixel of UI, every error message, every millisecond of response time — all must serve this goal. If you are unsure whether your output meets this standard, it does not. Rewrite it.

---

## 1. PROJECT IDENTITY

| Field | Value |
|---|---|
| **Name** | AmeCompression (雨 Compression) |
| **Purpose** | Video (SVT-AV1) and audio (MP3) compression via FFmpeg |
| **Stack** | Electron + React + TypeScript (frontend) / Python + Flask (backend) |
| **Repo** | `tarminjapan/amecompression` |
| **License** | MIT |
| **Python** | >= 3.10 |
| **Package Manager** | `uv` (backend), `npm` (frontend) |

---

## 2. ARCHITECTURE MAP

```
AmeCompression/
├── frontend/                  # Electron + React + Vite
│   ├── electron/              #   Electron main & preload scripts
│   ├── src/
│   │   ├── components/        #   Layout, Sidebar, FloatingBar, ProgressPanel
│   │   ├── views/             #   MediaView, SettingsView
│   │   ├── hooks/             #   useJobs (polling job status)
│   │   ├── services/          #   api.ts (Axios → Flask)
│   │   ├── types/             #   TypeScript type definitions
│   │   ├── i18n/              #   en.json, ja.json translations
│   │   ├── profiles.ts        #   Compression profile presets
│   │   └── App.tsx             #   Root component, state orchestration
│   └── package.json
│
├── backend/                   # Python package
│   ├── api/                   #   Flask REST API
│   │   ├── app.py             #     Flask app factory, CORS, Blueprint registration
│   │   ├── config.py          #     Flask config (dev/prod/test)
│   │   ├── job_runner.py      #     Background job execution engine
│   │   └── blueprints/        #     jobs, media, settings endpoints
│   ├── video.py               #   Video compression (SVT-AV1 via FFmpeg)
│   ├── audio.py               #   Audio compression (MP3 via FFmpeg)
│   ├── ffmpeg.py              #   FFmpeg/ffprobe detection & media info
│   ├── volume.py              #   Volume analysis & normalization
│   ├── config.py              #   Codec constants, resolution limits, file extensions
│   ├── models.py              #   Dataclasses: params, results, progress events
│   ├── progress_handler.py    #   FFmpeg output parser, cancellation control
│   ├── settings.py            #   Persistent settings (JSON, cross-platform)
│   └── utils.py               #   Bitrate parsing, resolution scaling
│
├── tests/                     # pytest test suite
├── scripts/                   # Build & utility scripts
├── documents/                 # Migration guides, specs
├── pyproject.toml             # Backend config (ruff, pyright, mypy, pytest)
└── AGENTS.md                  # ← YOU ARE HERE
```

---

## 3. WORLD'S #1 QUALITY STANDARDS

### 3.1 UI / UX — Pixel-Perfect & Intuitive

- **Zero layout bugs.** No misaligned elements, no inconsistent spacing, no orphaned pixels.
- **Responsive feedback.** Every user action (button press, file drop, slider drag) must produce immediate visual feedback. Loading states, progress bars, and success/error toasts are mandatory — never leave the user guessing.
- **Animations.** Smooth, purposeful, never gratuitous. Use CSS transitions and transforms. Avoid layout thrashing.
- **Dark/Light theme.** Both themes must look intentional — not just an inverted color palette. Test every component in both modes.
- **i18n.** All user-facing strings go through `react-i18next`. Add keys to both `en.json` and `ja.json`. Dot-notation keys only (e.g., `"settings.title"`). Never hardcode user-visible text.
- **Accessibility.** Proper ARIA labels, keyboard navigation, focus management.

### 3.2 Stability — Rock-Solid Under All Conditions

- **Never crash.** Corrupt files, missing FFmpeg, network failures, permission errors, zero-byte files, absurdly large files — handle every edge case gracefully.
- **Error messages.** Must be specific, actionable, and human-readable. Never expose raw stack traces to users. Never show generic "An error occurred."
- **FFmpeg process management.** Always terminate child processes in `finally` blocks. Handle cancellation tokens. Never leave zombie processes.
- **Type safety.** Every function has type hints. Every `None` possibility is handled. Never use `Optional` without guarding.

### 3.3 Compression Quality — Best-in-Class Output

- **SVT-AV1** for video (CRF-based quality control, configurable preset 0-13).
- **AAC** for video audio tracks, **libmp3lame** for audio-only files.
- **Volume normalization.** Auto-gain analysis via FFmpeg `volumedetect`. Target: -16 dB for speech/dialogue, with clipping prevention.
- **Denoising.** `afftdn` filter with configurable level (0.0–1.0).
  The UI value (0.0–1.0) is mapped to the FFmpeg `nr` parameter (0–97 dB) via
  `nr = int(denoise_level * 97)` (see `backend/volume.py:build_audio_filter()`).
  **Never** pass the raw UI value directly as `nr` — always apply this conversion.
- **Resolution scaling.** Maintains aspect ratio, enforces even dimensions for encoding quality. Max: 4K (3840×2160).

---

## 4. ABSOLUTE PROHIBITIONS

### 4.1 Error Suppression Comments — STRICTLY FORBIDDEN

These are **never** allowed under any circumstances:

```python
# ❌ ABSOLUTELY FORBIDDEN
x = risky()  # type: ignore
# noqa: E501
# mypy: ignore
```

```typescript
// ❌ ABSOLUTELY FORBIDDEN
// eslint-disable-next-line
// @ts-ignore
// @ts-nocheck
/* eslint-disable */
```

**If a type error or lint warning appears, fix the root cause.** Restructure the code, correct the type definitions in `frontend/src/types/index.ts` or `backend/models.py`, or rewrite the logic. There is no excuse for suppression comments.

### 4.2 Other Prohibitions

- **No `console.log` in production code.** Use structured logging.
- **No `print()` in backend API code.** CLI-only is acceptable for `cli.py`.
- **No hardcoded URLs or file paths.** Use configuration.
- **No `any` types** unless truly unavoidable and documented with a TODO.
- **No commented-out code.** Delete it. Git remembers everything.
- **No emoji in code or commit messages** unless explicitly requested.

---

## 5. MANDATORY WORKFLOW

### 5.1 Before Writing Any Code

1. **Read this file** (`AGENTS.md`) and `CONTRIBUTING.md` in full.
2. **Read `.gemini/styleguide.md`** for project-specific conventions.
3. **Understand the surrounding code.** Read neighboring files, check imports, study existing patterns before introducing new ones.
4. **Check existing types.** Before creating new types, verify `frontend/src/types/index.ts` and `backend/models.py`.

### 5.2 Code Generation Checklist

Every piece of code you generate must pass ALL of the following:

- [ ] **Lint clean:** `ruff check` / `eslint --max-warnings=0` — zero warnings, zero errors
- [ ] **Format clean:** `ruff format --check` / `prettier --check` — zero diffs
- [ ] **Type clean:** `pyright --warnings` / `tsc --noEmit` — zero errors, zero warnings
- [ ] **Tests pass:** `pytest tests -v` / relevant frontend tests
- [ ] **No suppression comments:** Zero `# type: ignore`, `# noqa`, `eslint-disable`, `@ts-ignore`
- [ ] **i18n complete:** All new user-facing strings have entries in both `en.json` and `ja.json`
- [ ] **Error handling:** Every external call (subprocess, HTTP, file I/O) is wrapped in try/except with specific handling
- [ ] **No crashes:** Tested mentally against corrupt input, missing files, and edge cases

### 5.3 Quality Check Commands

```bash
# Backend
uv run ruff check backend tests
uv run ruff format --check backend tests
uv run pyright --warnings
uv run pytest tests -v

# Frontend
cd frontend && npm run lint:strict
cd frontend && npm run format:check
cd frontend && npm run typecheck
```

**All must pass with zero issues before any code is considered complete.**

---

## 6. CODING CONVENTIONS

### 6.1 Python (Backend)

- **Style:** PEP 8, enforced by `ruff` (line-length: 100)
- **Quotes:** Double quotes (`"`)
- **Type hints:** Required on all function signatures and public variables
- **Imports:** `ruff` isort rules (stdlib → third-party → local)
- **Docstrings:** Google convention for all public functions/classes
- **Naming:**
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
- **Error handling:** Specific exception types, never bare `except:`. Always include informative error messages.
- **Path handling:** Use `pathlib.Path`, not `os.path`

### 6.2 TypeScript / React (Frontend)

- **Style:** Enforced by ESLint + Prettier
- **Components:** Functional components with hooks. No class components.
- **Types:** Define in `frontend/src/types/index.ts`. Export from there.
- **State:** `useState` for local, `useRef` for mutable refs, context/props for shared.
- **Naming:**
  - Components: `PascalCase` files and exports
  - Functions/variables: `camelCase`
  - Types/Interfaces: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
- **CSS:** Scoped component CSS. Follow existing class naming patterns in `App.css` and `index.css`.
- **API calls:** Use the shared `api` Axios instance from `services/api.ts`. Always handle errors.

### 6.3 Git Conventions

- **Branch naming:** `feature/<description>`, `fix/<description>`, `refactor/<description>`
- **Commit messages:** Imperative mood, concise. e.g., `feat: add audio denoise slider`, `fix: handle corrupt file input`
- **PR scope:** One feature or fix per PR. Keep it focused.

---

## 7. KEY DATA FLOWS

### 7.1 Compression Job Lifecycle

```
User selects files (MediaView)
  → FloatingBar "Start Compression"
    → POST /api/jobs (backend/api/blueprints/jobs)
      → job_runner starts background thread
        → video.py: compress_video_service() or audio.py: compress_audio_service()
          → subprocess.Popen(ffmpeg ...)
            → ProgressParser reads stdout line-by-line
              → ProgressEvent emitted via callback
                → Stored in job_runner state
  → Frontend polls GET /api/jobs every 1s (useJobs hook)
    → Updates UI: ProgressPanel, FloatingBar status
      → On completion: Electron notification via electronAPI
```

### 7.2 Settings Flow

```
SettingsView (React)
  → GET/PUT /api/settings (backend/api/blueprints/settings)
    → SettingsManager (singleton, JSON file on disk)
      → Cross-platform config dir: %APPDATA% / ~/Library/Application Support / ~/.config/AmeCompression
```

### 7.3 Profile System

```
MediaProfile (TypeScript interface, profiles.ts)
  → Stored in localStorage (browser/Electron)
  → Load/Save via loadProfiles() / saveProfiles()
  → Applied to MediaView settings → passed to API on compression
```

---

## 8. API ENDPOINTS

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/jobs` | Start a new compression job |
| GET | `/api/jobs` | List all jobs with status/progress |
| DELETE | `/api/jobs/:id` | Cancel a running job |
| GET | `/api/media/info` | Get media file information (ffprobe) |
| POST | `/api/media/volume-analyze` | Analyze volume level |
| GET | `/api/settings` | Get all settings |
| PUT | `/api/settings` | Update settings |

---

## 9. FFmpeg COMMAND PATTERNS

### Video Compression

```bash
ffmpeg -i <input> -y \
  -vf "scale=W:H,fps=FPS" \
  -c:v libsvtav1 -crf <0-63> -b:v 0 -preset <0-13> \
  [-af "afftdn=nr=N,volume=GdB"] -c:a aac -b:a <bitrate> \
  <output>
```

### Audio Compression

```bash
ffmpeg -i <input> -y \
  [-af "afftdn=nr=N,volume=GdB"] \
  -c:a libmp3lame -b:a <bitrate> \
  -map_metadata 0 \
  <output>
```

### Volume Analysis

```bash
ffmpeg -i <input> -af volumedetect -vn -sn -dn -f null -
```

---

## 10. DEFAULT CONFIGURATION VALUES

| Parameter | Default | Range |
|-----------|---------|-------|
| Video codec | `libsvtav1` | — |
| CRF | `25` | 0–63 |
| Preset | `6` | 0–13 |
| Audio codec (video) | `aac` | — |
| Audio codec (audio) | `libmp3lame` | — |
| Audio bitrate | `192k` | 16k–320k |
| Max resolution | `3840×2160` | — |
| Target volume | `-16 dB` | — |
| Max volume | `-1 dB` | — |
| Denoise level | `0.15` | 0.0–1.0 |

---

## 11. SELF-REVIEW PROTOCOL

Before finalizing any output, answer these questions:

1. **Would Apple ship this UI?** If the answer is not an immediate "yes," refine the design.
2. **Can this code crash?** Trace every error path. If any path leads to an unhandled exception, fix it.
3. **Is every type correct?** No `any`, no suppression comments, no loose assumptions.
4. **Does the user understand what's happening?** Loading states, progress, errors — all clear and informative.
5. **Would the best engineer on Earth approve this PR?** If not, you are not done.

---

## 12. GEMINI CODE ASSIST INTEGRATION

After completing any implementation, use these commands for verification:

| Command | Purpose |
|---------|---------|
| `/gemini review` | Full code quality and UX review |
| `/gemini summary` | Implementation status overview |
| `/gemini` | General development support |
| `/gemini help` | Command specification reference |
| `@gemini-code-assist <file>` | Module-specific optimization proposals |

---

## 13. FINAL REMINDER

You are not writing code for a hobby project. You are building **the world's best compression application.** Every decision you make — from variable names to error handling to pixel alignment — must reflect this standard.

**Good enough is the enemy of world's #1. Ship perfection.**
