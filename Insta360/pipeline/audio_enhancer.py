"""
Audio Enhancer Module.
Mixes background music, applies smart audio ducking (sidechain compression),
wind rumble reduction, and smooth fade in/out transitions.
"""

import subprocess
from pathlib import Path

FFMPEG_BIN = "/opt/homebrew/bin/ffmpeg"
if not Path(FFMPEG_BIN).exists():
    FFMPEG_BIN = "ffmpeg"

class AudioEnhancer:
    def __init__(self, output_dir="exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def enhance_and_mix(
        self,
        video_path,
        music_path,
        output_path,
        video_duration,
        camera_volume=1.0,      # 0.0 to 2.0
        music_volume=0.5,       # 0.0 to 2.0
        enable_ducking=True,    # Auto-duck music when speech occurs
        ducking_ratio=4.0,      # Compression ratio
        ducking_threshold=0.08, # Sensitivity threshold (0.01 - 0.2)
        wind_reduction=True,    # Highpass filter for wind rumble
        fade_in_sec=1.5,
        fade_out_sec=2.5,
        progress_callback=None
    ):
        """
        Takes video with ambient/voice audio and music track, builds FFmpeg filtergraph
        to duck music when voices are active, cuts/loops music to match video duration,
        and outputs merged video file.
        """
        video = Path(video_path)
        music = Path(music_path)
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        fade_out_start = max(0, video_duration - fade_out_sec)

        # Build FFmpeg complex filter
        # 1. Camera audio processing (filter [0:a])
        cam_filters = []
        if wind_reduction:
            cam_filters.append("highpass=f=120") # Filter wind rumble below 120Hz
        cam_filters.append(f"volume={camera_volume}")
        cam_filter_str = ",".join(cam_filters) if cam_filters else "anull"

        # 2. Music track processing (filter [1:a])
        # Infinite loop music if shorter than video, trim to video duration, apply volume & fades
        music_filters = [
            f"aloop=loop=-1:size=2e+09",
            f"atrim=0:{video_duration}",
            f"volume={music_volume}",
            f"afade=t=in:ss=0:d={fade_in_sec}",
            f"afade=t=out:st={fade_out_start}:d={fade_out_sec}"
        ]
        music_filter_str = ",".join(music_filters)

        if enable_ducking:
            # Sidechain compression: input 0:a ducks input 1:a
            filter_complex = (
                f"[0:a]{cam_filter_str},asplit=2[cam_voice][cam_sidechain];"
                f"[1:a]{music_filter_str}[music_pre];"
                f"[music_pre][cam_sidechain]sidechaincompress=threshold={ducking_threshold}:"
                f"ratio={ducking_ratio}:attack=120:release=900[ducked_music];"
                f"[cam_voice][ducked_music]amix=inputs=2:duration=first:dropout_transition=2[aout]"
            )
        else:
            filter_complex = (
                f"[0:a]{cam_filter_str}[cam_voice];"
                f"[1:a]{music_filter_str}[music_processed];"
                f"[cam_voice][music_processed]amix=inputs=2:duration=first:dropout_transition=2[aout]"
            )

        cmd = [
            FFMPEG_BIN, "-y",
            "-i", str(video),
            "-i", str(music),
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",  # Copy video stream instantly without re-encoding!
            "-c:a", "aac",
            "-b:a", "256k",
            "-movflags", "+faststart",
            str(out)
        ]

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
            raise RuntimeError(f"FFmpeg audio mix failed with code {process.returncode}")

        return str(out)
