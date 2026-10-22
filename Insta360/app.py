#!/usr/bin/env python3
"""
OmniView360 - Insta360 Video Studio & Zero-App 360 Publisher.
Full-stack web application server built for macOS Apple Silicon.
"""

import os
import sys
import json
import mimetypes
import shutil
import socket
import threading
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from pathlib import Path

from pipeline.camera_importer import CameraImporter
from pipeline.video_cleaner import VideoCleaner
from pipeline.audio_enhancer import AudioEnhancer
from pipeline.spatial_metadata import SpatialMetadataInjector
from pipeline.web_publisher import WebPublisher

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
RAW_DIR = UPLOAD_DIR / "raw"
MUSIC_DIR = UPLOAD_DIR / "music"
EXPORT_DIR = BASE_DIR / "exports"
WEB_DIR = BASE_DIR / "web"

for d in [RAW_DIR, MUSIC_DIR, EXPORT_DIR, WEB_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Active processing jobs
ACTIVE_JOBS = {}
JOB_LOCK = threading.Lock()

def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class OmniViewHandler(BaseHTTPRequestHandler):
    importer = CameraImporter(target_dir=str(RAW_DIR))
    cleaner = VideoCleaner(output_dir=str(EXPORT_DIR))
    audio_enhancer = AudioEnhancer(output_dir=str(EXPORT_DIR))
    spatial_injector = SpatialMetadataInjector()
    publisher = WebPublisher(
        template_path=str(BASE_DIR / "viewer_template" / "index.html"),
        output_base=str(EXPORT_DIR / "web_packages")
    )

    def log_message(self, format, *args):
        # Clean logging
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Range")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # 1. API Endpoints
        if path == "/api/status":
            lan_ip = get_lan_ip()
            ffmpeg_ok = Path("/opt/homebrew/bin/ffmpeg").exists() or shutil.which("ffmpeg") is not None
            self.send_json({
                "status": "online",
                "ffmpeg_available": ffmpeg_ok,
                "lan_ip": lan_ip,
                "port": self.server.server_port,
                "share_url": f"http://{lan_ip}:{self.server.server_port}"
            })
            return

        if path == "/api/devices":
            devices = self.importer.scan_devices()
            self.send_json({"devices": devices})
            return

        if path == "/api/scan":
            src = query.get("path", [""])[0]
            if not src:
                self.send_json({"error": "Missing path parameter"}, status=400)
                return
            files = self.importer.scan_files(src)
            self.send_json({"files": files})
            return

        if path == "/api/files":
            raw_files = [
                {
                    "name": f.name,
                    "path": str(f),
                    "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                    "ext": f.suffix.lower()
                }
                for f in RAW_DIR.glob("*") if f.is_file() and not f.name.startswith(".")
            ]
            music_files = [
                {
                    "name": f.name,
                    "path": str(f),
                    "size_mb": round(f.stat().st_size / (1024 * 1024), 2)
                }
                for f in MUSIC_DIR.glob("*") if f.is_file() and not f.name.startswith(".")
            ]
            export_files = [
                {
                    "name": f.name,
                    "path": str(f),
                    "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                    "is_zip": f.suffix.lower() == ".zip"
                }
                for f in EXPORT_DIR.glob("**/*") if f.is_file() and not f.name.startswith(".")
            ]
            self.send_json({
                "raw_videos": sorted(raw_files, key=lambda x: x["name"]),
                "music_tracks": sorted(music_files, key=lambda x: x["name"]),
                "exports": sorted(export_files, key=lambda x: x["name"])
            })
            return

        if path == "/api/job_status":
            job_id = query.get("job_id", [""])[0]
            with JOB_LOCK:
                job = ACTIVE_JOBS.get(job_id)
            if job:
                self.send_json(job)
            else:
                self.send_json({"status": "not_found"}, status=404)
            return

        # 2. Stream Media / File Download
        if path.startswith("/media/"):
            rel_path = unquote(path[len("/media/"):])
            # Security check: must reside inside project directory
            target = (BASE_DIR / rel_path).resolve()
            if not str(target).startswith(str(BASE_DIR)):
                self.send_error(403, "Access denied")
                return
            if not target.exists() or not target.is_file():
                self.send_error(404, "File not found")
                return
            self.serve_file_with_range(target)
            return

        # 3. View Published 360 Package
        if path.startswith("/view/"):
            pkg_name = unquote(path[len("/view/"):].strip("/"))
            index_file = EXPORT_DIR / "web_packages" / pkg_name / "index.html"
            if index_file.exists():
                self.serve_file_with_range(index_file)
            else:
                self.send_error(404, "Published 360 package not found")
            return

        # 4. Static Web Assets
        req_path = path.lstrip("/")
        if not req_path or req_path == "index.html":
            target = WEB_DIR / "index.html"
        else:
            target = (WEB_DIR / req_path).resolve()

        if target.exists() and target.is_file():
            self.serve_file_with_range(target)
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/probe":
            body = self.read_json_body()
            file_path = body.get("file_path")
            if not file_path or not Path(file_path).exists():
                self.send_json({"error": "File does not exist"}, status=400)
                return
            info = self.cleaner.probe(file_path)
            self.send_json(info)
            return

        if path == "/api/import":
            body = self.read_json_body()
            src_file = body.get("file_path")
            if not src_file:
                self.send_json({"error": "Missing file_path"}, status=400)
                return
            try:
                dest = self.importer.import_file(src_file)
                self.send_json({"status": "imported", "dest": dest, "name": Path(dest).name})
            except Exception as e:
                self.send_json({"error": str(e)}, status=500)
            return

        if path == "/api/upload_music":
            self.handle_upload_file(MUSIC_DIR)
            return

        if path == "/api/upload_video":
            self.handle_upload_file(RAW_DIR)
            return

        if path == "/api/process":
            body = self.read_json_body()
            job_id = f"job_{len(ACTIVE_JOBS) + 1}_{int(socket.gethostname().__hash__() % 10000)}"
            with JOB_LOCK:
                ACTIVE_JOBS[job_id] = {
                    "id": job_id,
                    "status": "queued",
                    "progress": 0,
                    "step": "Queued...",
                    "error": None,
                    "result": None
                }

            # Spawn processing in background thread
            t = threading.Thread(target=self.run_pipeline_job, args=(job_id, body))
            t.daemon = True
            t.start()

            self.send_json({"job_id": job_id, "status": "started"})
            return

        self.send_error(404, "Endpoint not found")

    def run_pipeline_job(self, job_id, params):
        def update_job(step, progress, status="running"):
            with JOB_LOCK:
                if job_id in ACTIVE_JOBS:
                    ACTIVE_JOBS[job_id]["step"] = step
                    ACTIVE_JOBS[job_id]["progress"] = progress
                    ACTIVE_JOBS[job_id]["status"] = status

        try:
            video_input = params.get("video_path")
            music_input = params.get("music_path")
            title = params.get("title", "My 360 Experience")
            start_time = float(params.get("start_time", 0.0))
            end_time = float(params["end_time"]) if params.get("end_time") else None
            brightness = float(params.get("brightness", 0.0))
            contrast = float(params.get("contrast", 1.0))
            saturation = float(params.get("saturation", 1.0))
            sharpness = bool(params.get("sharpness", True))
            camera_vol = float(params.get("camera_volume", 1.0))
            music_vol = float(params.get("music_volume", 0.4))
            enable_ducking = bool(params.get("enable_ducking", True))
            resolution = params.get("resolution", "4k")

            video_p = Path(video_input)
            base_stem = f"{video_p.stem}_clean360"

            # Step 1: Probe video
            update_job("Analyzing video properties...", 10)
            probe_data = self.cleaner.probe(video_input)
            duration = probe_data.get("duration", 10.0)
            if end_time and end_time > start_time:
                effective_duration = end_time - start_time
            else:
                effective_duration = max(1.0, duration - start_time)

            # Step 2: Clean, trim & enhance video
            update_job("Cleaning video & optimizing 360 projection...", 30)
            cleaned_video = EXPORT_DIR / f"{base_stem}_temp.mp4"
            self.cleaner.clean_and_process(
                input_path=video_input,
                output_path=str(cleaned_video),
                start_time=start_time,
                end_time=end_time,
                brightness=brightness,
                contrast=contrast,
                saturation=saturation,
                sharpness=sharpness,
                target_resolution=resolution
            )

            # Step 3: Enhance & mix background music (if provided)
            mixed_video = EXPORT_DIR / f"{base_stem}_mixed.mp4"
            if music_input and Path(music_input).exists():
                update_job("Mixing background music with smart voice ducking...", 60)
                self.audio_enhancer.enhance_and_mix(
                    video_path=str(cleaned_video),
                    music_path=str(music_input),
                    output_path=str(mixed_video),
                    video_duration=effective_duration,
                    camera_volume=camera_vol,
                    music_volume=music_vol,
                    enable_ducking=enable_ducking
                )
                working_video = mixed_video
            else:
                working_video = cleaned_video

            # Step 4: Inject Google Spatial Media 360 metadata (Spherical v2)
            update_job("Injecting Google Spatial Media 360 metadata...", 80)
            final_mp4 = EXPORT_DIR / f"{base_stem}.mp4"
            self.spatial_injector.inject(str(working_video), str(final_mp4))

            # Cleanup temp files
            for tmp in [cleaned_video, mixed_video]:
                if tmp.exists() and tmp != final_mp4:
                    try:
                        tmp.unlink()
                    except Exception:
                        pass

            # Step 5: Publish Interactive Web 360 Package & Zip
            update_job("Generating Zero-App Web 360 viewer & shareable package...", 90)
            pub_result = self.publisher.publish_package(
                video_file_path=str(final_mp4),
                title=title,
                package_name=base_stem
            )

            lan_ip = get_lan_ip()
            port = self.server.server_port
            web_view_url = f"http://{lan_ip}:{port}/exports/web_packages/{base_stem}/index.html"

            result = {
                "mp4_file": str(final_mp4),
                "mp4_rel": f"/media/exports/{final_mp4.name}",
                "web_package_dir": pub_result["package_dir"],
                "zip_file": pub_result["zip_path"],
                "zip_rel": f"/media/exports/web_packages/{Path(pub_result['zip_path']).name}",
                "web_view_url": web_view_url,
                "title": title
            }

            with JOB_LOCK:
                ACTIVE_JOBS[job_id]["status"] = "completed"
                ACTIVE_JOBS[job_id]["progress"] = 100
                ACTIVE_JOBS[job_id]["step"] = "Complete! Ready to share."
                ACTIVE_JOBS[job_id]["result"] = result

        except Exception as e:
            traceback.print_exc()
            with JOB_LOCK:
                ACTIVE_JOBS[job_id]["status"] = "failed"
                ACTIVE_JOBS[job_id]["error"] = str(e)

    def handle_upload_file(self, target_dir):
        """Simple multipart/form-data or binary upload handler."""
        try:
            content_type = self.headers.get("Content-Type", "")
            content_length = int(self.headers.get("Content-Length", 0))

            if "multipart/form-data" in content_type:
                boundary = content_type.split("boundary=")[1].strip().encode()
                data = self.rfile.read(content_length)
                parts = data.split(b"--" + boundary)
                for part in parts:
                    if b'filename="' in part:
                        headers_blob, body = part.split(b"\r\n\r\n", 1)
                        # Extract filename
                        h_str = headers_blob.decode("utf-8", errors="ignore")
                        filename = h_str.split('filename="')[1].split('"')[0]
                        filename = os.path.basename(filename)
                        if body.endswith(b"\r\n"):
                            body = body[:-2]
                        dest = target_dir / filename
                        with open(dest, "wb") as f:
                            f.write(body)
                        self.send_json({"status": "uploaded", "path": str(dest), "filename": filename})
                        return

            self.send_json({"error": "Unsupported upload format"}, status=400)
        except Exception as e:
            self.send_json({"error": str(e)}, status=500)

    def serve_file_with_range(self, file_path):
        """
        Serves files with HTTP 206 Partial Content support for smooth seeking
        and streaming of high-resolution 360 videos in HTML5 and Three.js.
        """
        stat = file_path.stat()
        file_size = stat.st_size
        mime, _ = mimetypes.guess_type(str(file_path))
        if not mime:
            mime = "application/octet-stream"

        range_header = self.headers.get("Range")

        if range_header:
            # Parse Range header: 'bytes=START-END'
            try:
                byte_range = range_header.strip().split("=")[1]
                start_str, end_str = byte_range.split("-")
                start = int(start_str) if start_str else 0
                end = int(end_str) if end_str else file_size - 1
                end = min(end, file_size - 1)
                length = end - start + 1

                self.send_response(206)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Content-Length", str(length))
                self.send_header("Accept-Ranges", "bytes")
                self.send_cors_headers()
                self.end_headers()

                with open(file_path, "rb") as f:
                    f.seek(start)
                    chunk_size = 64 * 1024
                    bytes_remaining = length
                    while bytes_remaining > 0:
                        read_bytes = min(bytes_remaining, chunk_size)
                        buf = f.read(read_bytes)
                        if not buf:
                            break
                        self.wfile.write(buf)
                        bytes_remaining -= len(buf)
                return
            except Exception:
                pass

        # Standard 200 response
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(file_size))
        self.send_header("Accept-Ranges", "bytes")
        self.send_cors_headers()
        self.end_headers()

        with open(file_path, "rb") as f:
            shutil.copyfileobj(f, self.wfile)

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > 0:
            raw = self.rfile.read(length)
            return json.loads(raw.decode("utf-8"))
        return {}


def main():
    port = 8080
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    server = HTTPServer(("0.0.0.0", port), OmniViewHandler)
    lan_ip = get_lan_ip()
    print("=" * 65)
    print("  🎥 OmniView360 Studio & Zero-App 360 Publisher")
    print("=" * 65)
    print(f"  • Local Mac Dashboard : http://localhost:{port}")
    print(f"  • Home Wi-Fi Network  : http://{lan_ip}:{port}")
    print("=" * 65)
    print("  Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping OmniView360 server...")
        server.server_close()


if __name__ == "__main__":
    main()
