"""
Web Publisher Module.
Generates standalone, zero-app 360 Web viewer packages and zip archives
ready for GitHub Pages, Cloudflare Pages, Netlify, or direct friend & family sharing.
"""

import os
import shutil
import zipfile
import socket
from pathlib import Path

class WebPublisher:
    def __init__(self, template_path="viewer_template/index.html", output_base="exports/web_packages"):
        self.template_path = Path(template_path)
        self.output_base = Path(output_base)
        self.output_base.mkdir(parents=True, exist_ok=True)

    def get_local_ip(self):
        """Find local LAN IP address to share within home Wi-Fi network."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def publish_package(self, video_file_path, title="My 360 Experience", package_name=None):
        """
        Creates a standalone web directory with index.html and video.mp4,
        plus a ready-to-send .zip archive.
        """
        src_video = Path(video_file_path)
        if not src_video.exists():
            raise FileNotFoundError(f"Video file not found: {video_file_path}")

        if not package_name:
            package_name = src_video.stem

        pkg_dir = self.output_base / package_name
        pkg_dir.mkdir(parents=True, exist_ok=True)

        # 1. Copy video to package as video.mp4 (or link)
        dest_video = pkg_dir / "video.mp4"
        if not dest_video.exists() or dest_video.stat().st_size != src_video.stat().st_size:
            shutil.copy2(src_video, dest_video)

        # 2. Render index.html from template
        template_content = self.template_path.read_text(encoding="utf-8")
        rendered = template_content.replace("{{TITLE}}", title)
        rendered = rendered.replace("{{VIDEO_SRC}}", "video.mp4")

        (pkg_dir / "index.html").write_text(rendered, encoding="utf-8")

        # 3. Create .zip archive for one-click sharing
        zip_path = self.output_base / f"{package_name}_web360.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(pkg_dir):
                for file in files:
                    full_file = Path(root) / file
                    arcname = full_file.relative_to(pkg_dir)
                    zf.write(full_file, arcname)

        return {
            "package_dir": str(pkg_dir),
            "zip_path": str(zip_path),
            "video_path": str(dest_video),
            "index_html": str(pkg_dir / "index.html")
        }
