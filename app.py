import zipfile
import secrets
import logging
import time
from datetime import datetime
from pathlib import Path
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file,
    flash,
    abort,
    jsonify,
)
from werkzeug.utils import secure_filename
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Track app start time for uptime monitoring
APP_START_TIME = time.time()

# Configure logging
if app.config.get("DEBUG"):
    logging.basicConfig(level=getattr(logging, app.config.get("LOG_LEVEL", "INFO")))
    app.logger.setLevel(getattr(logging, app.config.get("LOG_LEVEL", "INFO")))
    app.logger.info("🧱 Event Gallery starting in DEBUG mode")

Path(app.config["UPLOAD_ROOT"]).mkdir(parents=True, exist_ok=True)
Path(app.config["ARCHIVE_ROOT"]).mkdir(parents=True, exist_ok=True)


def _is_guest():
    return session.get("role") == "guest"


def _is_admin():
    return session.get("role") == "admin"


def _safe_subdir(s: str) -> str:
    # Guest name folder safety
    s = s.strip()[:80]
    s = secure_filename(s) or "guest"
    return s


def _unique_name(orig: str) -> str:
    base = secure_filename(orig)
    stem, dot, ext = base.rpartition(".")
    if not dot:
        stem, ext = base, ""
    token = datetime.utcnow().strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(4)
    return f"{stem or 'file'}-{token}{('.' + ext) if ext else ''}"


@app.route("/", methods=["GET", "POST"])
def landing():
    if request.method == "POST":
        code = (request.form.get("code") or "").strip()
        if code == app.config["EVENT_CODE"]:
            session.clear()
            session["role"] = "guest"
            session.permanent = True
            return redirect(url_for("upload"))
        if code == app.config["ADMIN_CODE"]:
            session.clear()
            session["role"] = "admin"
            session.permanent = True
            return redirect(url_for("admin"))
        flash("Wrong code. Try again.")
    return render_template("landing.html")


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if not _is_guest() and not _is_admin():
        return redirect(url_for("landing"))

    if request.method == "POST":
        files = request.files.getlist("files")
        guest_name = _safe_subdir(request.form.get("guest_name") or "guest")
        date_dir = datetime.utcnow().strftime("%Y-%m-%d")
        target_dir = Path(app.config["UPLOAD_ROOT"]) / date_dir / guest_name
        target_dir.mkdir(parents=True, exist_ok=True)

        if app.config.get("DEBUG"):
            app.logger.debug(f"📂 Upload target directory: {target_dir}")
            app.logger.debug(f"👤 Guest name: {guest_name}")
            app.logger.debug(f"📁 Files received: {len(files)}")

        saved = 0
        skipped = 0
        for f in files:
            if not f or f.filename == "":
                skipped += 1
                if app.config.get("DEBUG"):
                    app.logger.debug("❌ Skipped empty file")
                continue
            if not Config.allowed(f.filename):
                skipped += 1
                if app.config.get("DEBUG"):
                    app.logger.debug(f"❌ Skipped disallowed file: {f.filename}")
                continue
            filename = _unique_name(f.filename)
            file_path = target_dir / filename
            f.save(file_path)
            saved += 1
            if app.config.get("DEBUG"):
                app.logger.debug(
                    f"✅ Saved file: {filename} ({file_path.stat().st_size} bytes)"
                )

        if app.config.get("DEBUG"):
            app.logger.info(f"📊 Upload summary - Saved: {saved}, Skipped: {skipped}")

        if saved:
            flash(f"Uploaded {saved} file(s). Thank you!")
        else:
            flash("No valid files were uploaded.")
        return redirect(url_for("upload"))

    return render_template("upload.html")


@app.route("/admin", methods=["GET"])
def admin():
    if not _is_admin():
        return redirect(url_for("landing"))

    # Gather some basic stats
    root = Path(app.config["UPLOAD_ROOT"])
    total_files = 0
    total_bytes = 0
    folders = 0
    for p in root.rglob("*"):
        if p.is_file():
            total_files += 1
            total_bytes += p.stat().st_size
        elif p.is_dir():
            folders += 1

    return render_template(
        "admin.html",
        total_files=total_files,
        total_gb=round(total_bytes / 1024 / 1024 / 1024, 3),
        folders=folders,
    )


@app.route("/admin/download-all", methods=["POST"])
def download_all():
    if not _is_admin():
        abort(403)

    # Create a zip on disk and stream it back
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    zip_name = f"event-gallery-{timestamp}.zip"
    zip_path = Path(app.config["ARCHIVE_ROOT"]) / zip_name

    root = Path(app.config["UPLOAD_ROOT"])
    # Build zip file; store relative paths for nice tree
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in root.rglob("*"):
            if path.is_file():
                zf.write(path, arcname=path.relative_to(root))

    # Use send_file without loading to memory
    return send_file(zip_path, as_attachment=True, download_name=zip_name)


@app.route("/gallery", methods=["GET"])
def gallery():
    if not app.config["ENABLE_GALLERY"]:
        abort(404)
    # Very simple gallery: list image files (not videos)
    root = Path(app.config["UPLOAD_ROOT"])
    images = []
    all_files = []

    if app.config.get("DEBUG"):
        app.logger.debug(f"🖼️ Scanning gallery directory: {root}")

    for p in sorted(root.rglob("*")):
        if p.is_file():
            all_files.append(p)
            ext = p.suffix.lower().strip(".")
            rel = p.relative_to(root)

            if ext in {"jpg", "jpeg", "png", "gif", "webp", "heic", "heif"}:
                # Image files
                images.append({"path": str(rel), "type": "image"})
                if app.config.get("DEBUG"):
                    app.logger.debug(f"🖼️ Found image: {rel}")
            elif ext in {"mp4", "mov", "hevc", "mkv", "webm", "avi"}:
                # Video files - include if enabled
                if app.config.get("GALLERY_SHOW_VIDEOS"):
                    images.append({"path": str(rel), "type": "video"})
                    if app.config.get("DEBUG"):
                        app.logger.debug(f"🎥 Found video (included): {rel}")
                elif app.config.get("DEBUG"):
                    app.logger.debug(f"🎥 Found video (excluded): {rel}")

    if app.config.get("DEBUG"):
        app.logger.info(
            f"📊 Gallery stats - Total files: {len(all_files)}, Images in gallery: {len(images)}"
        )

    return render_template("gallery.html", images=images)


@app.route("/raw/<path:rel>")
def raw(rel):
    # Serve a single file by relative path (used for gallery)
    root = Path(app.config["UPLOAD_ROOT"]).resolve()

    # Security: Sanitize path components to prevent traversal attacks
    # Split the path and sanitize each component
    path_parts = Path(rel).parts
    sanitized_parts = []
    for part in path_parts:
        # Reject any attempt at path traversal
        if part in ("..", ".") or part.startswith("/") or part.startswith("\\"):
            abort(404)
        # Sanitize each component
        safe_part = secure_filename(part)
        if not safe_part or safe_part != part:
            # If sanitization changes the part, it's suspicious
            abort(404)
        sanitized_parts.append(safe_part)

    # Reconstruct the path from sanitized components
    safe_rel = Path(*sanitized_parts) if sanitized_parts else Path()
    abs_path = (root / safe_rel).resolve()

    # Ensure resolved path stays under root (defense in depth)
    if not abs_path.is_relative_to(root):
        abort(404)

    # Verify the file exists
    if not abs_path.is_file():
        abort(404)

    return send_file(abs_path, as_attachment=False)


@app.route("/health/simple", methods=["GET"])
def health_simple():
    """Simple health check for basic liveness probes."""
    return "OK", 200


@app.route("/health", methods=["GET"])
def health_detailed():
    """Detailed health check with diagnostics and readiness information."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uptime_seconds": round(time.time() - APP_START_TIME, 2),
        "checks": {},
    }

    # Check 1: Storage directories accessible
    try:
        upload_root = Path(app.config["UPLOAD_ROOT"])
        archive_root = Path(app.config["ARCHIVE_ROOT"])

        upload_exists = upload_root.exists() and upload_root.is_dir()
        archive_exists = archive_root.exists() and archive_root.is_dir()

        if upload_exists and archive_exists:
            health_status["checks"]["storage"] = {
                "status": "pass",
                "upload_root": str(upload_root),
                "archive_root": str(archive_root),
            }
        else:
            health_status["status"] = "degraded"
            health_status["checks"]["storage"] = {
                "status": "fail",
                "error": "Storage directories not accessible",
                "upload_exists": upload_exists,
                "archive_exists": archive_exists,
            }
    except (OSError, ValueError, KeyError) as e:
        health_status["status"] = "degraded"
        health_status["checks"]["storage"] = {
            "status": "fail",
            "error": str(e),
        }

    # Check 2: Configuration validation
    config_ok = True
    config_issues = []

    if app.config["SECRET_KEY"] == "dev-insecure-change-me":
        config_ok = False
        config_issues.append("Using default SECRET_KEY (insecure)")

    if (
        app.config["EVENT_CODE"] == "flowers"
        or app.config["ADMIN_CODE"] == "champagne"
    ):
        config_ok = False
        config_issues.append("Using default access codes (insecure)")

    if config_ok:
        health_status["checks"]["config"] = {"status": "pass"}
    else:
        health_status["status"] = "degraded"
        health_status["checks"]["config"] = {
            "status": "warn",
            "issues": config_issues,
        }

    # Check 3: Basic app stats
    try:
        root = Path(app.config["UPLOAD_ROOT"])
        total_files = sum(1 for p in root.rglob("*") if p.is_file())
        health_status["checks"]["stats"] = {
            "status": "pass",
            "total_files": total_files,
        }
    except (OSError, ValueError, KeyError) as e:
        health_status["checks"]["stats"] = {
            "status": "fail",
            "error": str(e),
        }

    # Return appropriate HTTP status code
    http_status = 200 if health_status["status"] == "healthy" else 503
    return jsonify(health_status), http_status


@app.errorhandler(413)
def too_large(_e):
    flash(f"File too large. Max {app.config['MAX_CONTENT_MB']} MB total per request.")
    return redirect(url_for("upload"))


if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", False))
