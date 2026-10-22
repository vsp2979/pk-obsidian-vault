#!/usr/bin/env bash
# OmniView360 - One-Click Launcher

cd "$(dirname "$0")"

echo "=========================================================="
echo "  🎥 OmniView360 — Insta360 Studio & Zero-App 360 Publisher"
echo "=========================================================="

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not found. Please install Python 3."
    exit 1
fi

# Check if ffmpeg is available
if ! command -v ffmpeg &> /dev/null && [ ! -f "/opt/homebrew/bin/ffmpeg" ]; then
    echo "⚠️  Warning: FFmpeg not found in standard PATH. OmniView360 will check /opt/homebrew/bin/ffmpeg."
fi

# Run the server
export PATH="/opt/homebrew/bin:$PATH"
python3 app.py 8080
