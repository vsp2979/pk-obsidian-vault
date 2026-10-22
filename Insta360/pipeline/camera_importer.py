"""
Camera Importer Module for Insta360 cameras.
Scans mounted volumes (SD cards, USB connections) and local directories for .insv and .mp4 files.
"""

import os
import glob
import shutil
import json
import subprocess
from pathlib import Path
from datetime import datetime

class CameraImporter:
    def __init__(self, target_dir="uploads/raw"):
        self.target_dir = Path(target_dir)
        self.target_dir.mkdir(parents=True, exist_ok=True)

    def scan_devices(self):
        """
        Scan /Volumes and common mount paths for Insta360 camera storage or SD cards.
        """
        candidates = []
        volumes_dir = Path("/Volumes")
        if volumes_dir.exists():
            try:
                for entry in volumes_dir.iterdir():
                    if entry.is_dir() and not entry.name.startswith("Macintosh") and not entry.name.startswith("."):
                        dcim = entry / "DCIM"
                        if dcim.exists() or "INSTA" in entry.name.upper() or "360" in entry.name:
                            candidates.append({
                                "name": entry.name,
                                "path": str(entry),
                                "is_camera": True,
                                "dcim_exists": dcim.exists()
                            })
            except PermissionError:
                pass

        return candidates

    def scan_files(self, source_path):
        """
        Scan a source folder for Insta360 video files (.insv, .mp4).
        Insta360 files typically look like:
        - VID_YYYYMMDD_HHMMSS_00_XXX.insv (Front lens)
        - VID_YYYYMMDD_HHMMSS_10_XXX.insv (Rear lens)
        - LRV_YYYYMMDD_... (Low-res preview)
        - PRO_... (Stitched or single lens)
        """
        src = Path(source_path)
        if not src.exists():
            return []

        files = []
        patterns = ["**/*.insv", "**/*.INSV", "**/*.mp4", "**/*.MP4", "**/*.mov", "**/*.MOV"]
        found_paths = set()

        for p in patterns:
            for match in src.glob(p):
                # Skip low-res preview proxy files (LRV_) if full res is present, unless requested
                if match.name.startswith(".") or match.name.startswith("._"):
                    continue
                if match.is_file() and str(match) not in found_paths:
                    found_paths.add(str(match))
                    stat = match.stat()
                    is_lrv = match.name.startswith("LRV_")
                    files.append({
                        "name": match.name,
                        "path": str(match),
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "is_lrv": is_lrv,
                        "extension": match.suffix.lower()
                    })

        # Sort newest first, with high-res files prioritised
        files.sort(key=lambda x: (x["is_lrv"], -Path(x["path"]).stat().st_mtime))
        return files

    def import_file(self, file_path, progress_callback=None):
        """
        Copy video file from camera/SD card to local workspace storage.
        """
        src = Path(file_path)
        if not src.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        dest = self.target_dir / src.name
        if dest.exists() and dest.stat().st_size == src.stat().st_size:
            return str(dest)

        total_size = src.stat().st_size
        bytes_copied = 0
        chunk_size = 4 * 1024 * 1024  # 4MB chunks

        with open(src, "rb") as fsrc, open(dest, "wb") as fdest:
            while True:
                chunk = fsrc.read(chunk_size)
                if not chunk:
                    break
                fdest.write(chunk)
                bytes_copied += len(chunk)
                if progress_callback:
                    progress_callback(bytes_copied / total_size)

        return str(dest)
