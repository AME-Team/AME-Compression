@echo off
setlocal

echo [1/4] Building backend (FFmpeg bundled)...
call uv run scripts/build.py --with-ffmpeg
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Bundled backend build failed.
    exit /b %ERRORLEVEL%
)

echo [2/4] Packaging GUI (installer + portable .7z, FFmpeg bundled)...
pushd frontend
call npm run package:win:bundled
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Bundled GUI packaging failed.
    popd
    exit /b %ERRORLEVEL%
)
popd

echo [3/4] Building backend (system FFmpeg)...
call uv run scripts/build.py --no-ffmpeg
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Non-bundled backend build failed.
    exit /b %ERRORLEVEL%
)

echo [4/4] Packaging GUI (installer + portable .7z, system FFmpeg)...
pushd frontend
call npm run package:win:nonbundled
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Non-bundled GUI packaging failed.
    popd
    exit /b %ERRORLEVEL%
)
popd

echo [DONE] Windows distributables are in frontend\release
echo   - Installer (.exe): ffmpeg-bundled / ffmpeg-system
echo   - Portable archive (.7z): ffmpeg-bundled / ffmpeg-system
