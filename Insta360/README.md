# 🎥 OmniView360 — Insta360 Studio & Zero-App 360 Publisher

A complete macOS workstation project to import raw Insta360 footage, clean and color-enhance 360 videos, mix background music with intelligent voice ducking, and publish interactive 360 experiences for friends and family **with zero apps or special software required**.

---

## ✨ Key Features

1. **Camera Import & Ingestion**
   - Automatically detects connected Insta360 cameras (X5, X4, X3, X2, ONE RS) and mounted MicroSD cards under `/Volumes`.
   - Supports raw `.insv`, `.insp`, and `.mp4` video files.
   - Built-in drag-and-drop browser uploader.

2. **Video Cleaning & Trimming**
   - Trim start/end times with instant precision (e.g., cutting off hand-holding or selfie stick setup frames).
   - Exposure and color correction sliders (Brightness, Contrast, Saturation/Vibrancy) with live preview.
   - 360 image sharpening filter.
   - Wind noise & microphone handling rumble filter (high-pass filter eliminating low-frequency noise).
   - Target 360 resolutions: **4K (3840×1920)** for optimal web balance, or **1080p** for fast mobile loading.

3. **Background Music & Smart Audio Ducking**
   - Upload any soundtrack (`.mp3`, `.m4a`, `.wav`, `.aac`).
   - Seamless music looping or trimming to match the exact duration of the video.
   - Smooth audio fade-in (1.5s) and fade-out (2.5s).
   - **Smart Voice Ducking (Sidechain compression)**: When voices/dialogue are detected on the camera track, background music volume automatically lowers by -12dB so speech is crisp, then smoothly swells back up when speaking stops.

4. **Zero-App Publishing for Friends & Family**
   - **Interactive Web 360 Experience (Three.js WebGL)**:
     - Friends open a web link on iPhone (Safari), Android (Chrome), iPad, or PC.
     - **Touch & Mouse Drag**: Smooth 360° spherical panning in all directions.
     - **Mobile Gyroscope**: Users can physically move/turn their phone in the air to look around in real-time.
     - No apps, no logins, and no special players needed!
   - **Google Spatial Media 360 Injection**:
     - Automatically embeds Spherical Video v2 metadata (`uuid` / `moov` atom) so files can be uploaded as unlisted videos directly to **YouTube**, **Facebook**, or **VLC** and play natively in 360°.
   - **Self-Contained Web 360 Bundle (.zip)**:
     - Generates a standalone folder containing `index.html` and the 360 video, bundled into a `.zip` file ready to send via AirDrop, Google Drive, or host for free on GitHub Pages / Cloudflare Pages / Netlify.
   - **Home Wi-Fi Instant Share**:
     - The local server displays your Mac's LAN IP address (`http://192.168.x.x:8080`) so family members in the same room can open the link or scan a QR code on their phone to immediately view the video.

---

## 🚀 Quick Start

### 1. Launch OmniView360
In the terminal, run:
```bash
./run.sh
```
Or directly:
```bash
python3 app.py 8080
```

Open your browser at:
- **Local Dashboard:** [http://localhost:8080](http://localhost:8080)
- **Home Wi-Fi Network:** `http://<your-mac-ip>:8080`

---

## 📁 Project Architecture

```
Insta360/
├── app.py                     # Full-stack HTTP server & REST API
├── run.sh                     # One-click launch script
├── pipeline/
│   ├── __init__.py
│   ├── camera_importer.py     # Camera detection & file importer
│   ├── video_cleaner.py       # Trimming, exposure, sharpening & FFmpeg pipeline
│   ├── audio_enhancer.py      # Audio mixing & smart voice ducking
│   ├── spatial_metadata.py    # Google Spatial Media 360 metadata injector
│   └── web_publisher.py       # Standalone interactive Web 360 packager
├── web/
│   ├── index.html             # Sleek dark-mode Studio UI
│   └── static/
│       ├── css/style.css      # Glassmorphism styling & responsive layout
│       └── js/app.js          # Interactive wizard & WebGL 360 controller
├── viewer_template/
│   └── index.html             # Zero-dependency Three.js 360 player for friends
├── uploads/
│   ├── raw/                   # Imported camera footage (.insv / .mp4)
│   └── music/                 # Uploaded soundtracks (.mp3 / .m4a / .wav)
└── exports/
    ├── web_packages/          # Generated web viewer bundles & .zip archives
    └── *.mp4                  # Cleaned 360 MP4s with embedded Spatial Media
```

---

## 🌐 How Friends & Family View Your 360 Videos

| Method | Friends Experience | How to Share |
|---|---|---|
| **Web 360 Link** | Open in Safari/Chrome on phone or computer. Gyroscope and swipe supported. No app needed. | Host on GitHub Pages, Cloudflare Pages, Netlify, or local Wi-Fi. |
| **YouTube 360** | Play directly in YouTube app or web browser in full 360°. | Upload the exported `.mp4` as an "Unlisted" video on YouTube. |
| **Cloud Storage** | Download and view, or open HTML bundle in browser. | Send via Google Drive, Dropbox, or AirDrop. |
