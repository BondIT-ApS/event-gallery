import os
import io
import zipfile
import secrets
from datetime import datetime
from pathlib import Path
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, send_file, flash, abort
)
from werkzeug.utils import secure_filename
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

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
            session.clear(); session["role"] = "guest"
            session.permanent = True
            return redirect(url_for("upload"))
        if code == app.config["ADMIN_CODE"]:
            session.clear(); session["role"] = "admin"
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

        saved = 0
        for f in files:
            if not f or f.filename == "":
                continue
            if not app.config["allowed"](f.filename):
                continue
            filename = _unique_name(f.filename)
            f.save(target_dir / filename)
            saved += 1

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

    return render_template("admin.html",
                           total_files=total_files,
                           total_gb=round(total_bytes/1024/1024/1024, 3),
                           folders=folders)

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
    for p in sorted(root.rglob("*")):
        if p.is_file():
            ext = p.suffix.lower().strip(".")
            if ext in {"jpg","jpeg","png","gif","webp"}:
                # Build a lightweight download link; no inline EXIF processing
                rel = p.relative_to(root)
                images.append(str(rel))
    return render_template("gallery.html", images=images)

@app.route("/raw/<path:rel>")
def raw(rel):
    # Serve a single file by relative path (used for gallery)
    root = Path(app.config["UPLOAD_ROOT"])
    abs_path = (root / rel).resolve()
    # Security: ensure resolved path stays under root
    if root not in abs_path.parents and abs_path != root:
        abort(404)
    if not abs_path.is_file():
        abort(404)
    return send_file(abs_path, as_attachment=False)

@app.errorhandler(413)
def too_large(_e):
    flash(f"File too large. Max {app.config['MAX_CONTENT_MB']} MB total per request.")
    return redirect(url_for("upload"))

if __name__ == "__main__":
    app.run(debug=True)