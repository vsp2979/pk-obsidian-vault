"""
Video Cleaner and Stitcher Module.
Handles video inspection, trimming, color/exposure enhancement, stabilization filters,
and equirectangular 360 projection optimization via FFmpeg.
"""

import json
import os
import subprocess
from pathlib import Path

FFMPEG_BIN = "/opt/homebrew/bin/ffmpeg"
FFPROBE_BIN = "/opt/homebrew/bin/ffprobe"

# Fallback to PATH if not in /opt/homebrew/bin
if not Path(FFMPEG_BIN).exists():
    FFMPEG_BIN = "ffmpeg"
if not Path(FFPROBE_BIN).exists():
    FFPROBE_BIN = "ffprobe"

class VideoCleaner:
    def __init__(self, output_dir="exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def probe(self, file_path):
        """
        Probe video stream to extract duration, resolution, audio channels, and fps.
        """
        cmd = [
            FFPROBE_BIN,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(file_path)
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)
            video_stream = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), None)
            audio_stream = next((s for s in info.get("streams", []) if s.get("codec_type") == "audio"), None)

            width = int(video_stream.get("width", 0)) if video_stream else 0
            height = int(video_stream.get("height", 0)) if video_stream else 0
            duration = float(info.get("format", {}).get("duration", 0))
            codec = video_stream.get("codec_name", "unknown") if video_stream else "none"

            # Check aspect ratio: standard 360 equirectangular is 2:1 (e.g. 3840x1920 or 5760x2880)
            is_equirectangular = False
            if height > 0 and abs((width / height) - 2.0) < 0.1:
                is_equirectangular = True

            return {
                "duration": round(duration, 2),
                "width": width,
                "height": height,
                "aspect_ratio": f"{width}:{height}",
                "is_equirectangular": is_equirectangular,
                "video_codec": codec,
                "has_audio": audio_stream is not None,
                "audio_codec": audio_stream.get("codec_name", "") if audio_stream else None,
                "size_bytes": int(info.get("format", {}).get("size", 0))
            }
        except Exception as e:
            return {
                "error": str(e),
                "duration": 0,
                "width": 1920,
                "height": 960,
                "is_equirectangular": True,
                "has_audio": False
            }

    def generate_proxy(self, input_path, output_path=None):
        """
        Generate a lightweight, fast-loading 720p/1080p equirectangular MP4 preview
        for instant scrubbing in the web interface and mobile browsers.
        """
        src = Path(input_path)
        if not output_path:
            output_path = self.output_dir / f"{src.stem}_preview.mp4"
        else:
            output_path = Path(output_path)

        cmd = [
            FFMPEG_BIN, "-y",
            "-i", str(src),
            "-vf", "scale=1920:960,format=yuv420p",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "25",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            str(output_path)
        ]
        subprocess.run(cmd, check=True)
        return str(output_path)

    def clean_and_process(
        self,
        input_path,
        output_path,
        start_time=0.0,
        end_time=None,
        brightness=0.0,     # -1.0 to 1.0 (0 default)
        contrast=1.0,       # 0.0 to 2.0 (1.0 default)
        saturation=1.0,     # 0.0 to 3.0 (1.0 default)
        sharpness=False,
        denoise=False,
        target_resolution="4k", # "4k" (3840x1920), "5.7k" (original), or "1080p" (1920x960)
        progress_callback=None
    ):
        """
        Cleans video with trimming, color adjustment, filters, and encodes for maximum compatibility.
        """
        src = Path(input_path)
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        # Build video filter chain
        vf_filters = []

        # Color & exposure tuning
        eq_filter = f"eq=brightness={brightness}:contrast={contrast}:saturation={saturation}"
        vf_filters.append(eq_filter)

        if sharpness:
            vf_filters.append("unsharp=5:5:0.8:5:5:0.0")

        if denoise:
            vf_filters.append("hqdn3d=2.0:1.5:2.0:1.5")

        # Resolution scaling
        if target_resolution == "1080p":
            vf_filters.append("scale=1920:960")
        elif target_resolution == "4k":
            vf_filters.append("scale=3840:1920")

        # Ensure compatibility with all web and mobile hardware decoders (yuv420p)
        vf_filters.append("format=yuv420p")

        filter_str = ",".join(vf_filters)

        cmd = [FFMPEG_BIN, "-y"]

        # Fast seek to start
        if start_time > 0:
            cmd.extend(["-ss", str(start_time)])

        cmd.extend(["-i", str(src)])

        if end_time and end_time > start_time:
            duration = end_time - start_time
            cmd.extend(["-t", str(duration)])

        cmd.extend([
            "-vf", filter_str,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",   # High visual quality
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            str(out)
        ])

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )

        for line in process.stdout:
            if progress_callback:
                progress_callback(line)

        process.wait()
        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg process exited with code {process.returncode}")

        return str(out)
