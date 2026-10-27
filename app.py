"""Flask Web Application for Floorplan to Blender 3D (GLB)."""

import os
import uuid
from pathlib import Path
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
import sys

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.pipeline import process_floorplan, load_model

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = str(BASE_DIR / "uploads")
app.config["OUTPUT_FOLDER"] = str(BASE_DIR / "outputs")
app.config["SAMPLES_FOLDER"] = str(BASE_DIR / "samples")
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32MB max upload

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "tiff", "webp"}

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)
os.makedirs(app.config["SAMPLES_FOLDER"], exist_ok=True)

# Warm up model weights
WEIGHTS_PATH = str(BASE_DIR / "weights" / "best.safetensors")
try:
    if os.path.exists(WEIGHTS_PATH):
        print(f"Pre-warming model with {WEIGHTS_PATH}...")
        load_model(WEIGHTS_PATH, device="cpu")
        print("Model pre-warmed successfully!")
except Exception as e:
    print(f"Warning: Model pre-warming failed: {e}")


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    # Discover available sample files
    sample_files = []
    if os.path.exists(app.config["SAMPLES_FOLDER"]):
        for f in sorted(os.listdir(app.config["SAMPLES_FOLDER"])):
            if allowed_file(f):
                sample_files.append({
                    "filename": f,
                    "url": f"/samples/{f}",
                    "name": f.rsplit(".", 1)[0].replace("_", " ").title()
                })
    return render_template("index.html", samples=sample_files)


@app.route("/samples/<filename>")
def get_sample(filename: str):
    filename = secure_filename(filename)
    path = os.path.join(app.config["SAMPLES_FOLDER"], filename)
    if not os.path.exists(path):
        return jsonify({"error": "Sample not found"}), 404
    return send_file(path)


@app.route("/api/samples")
def list_samples():
    files = []
    if os.path.exists(app.config["SAMPLES_FOLDER"]):
        for f in sorted(os.listdir(app.config["SAMPLES_FOLDER"])):
            if allowed_file(f):
                files.append({
                    "filename": f,
                    "url": f"/samples/{f}",
                    "title": f.rsplit(".", 1)[0].replace("_", " ").title()
                })
    return jsonify({"samples": files})


@app.route("/generate", methods=["POST"])
def generate():
    unique_id = str(uuid.uuid4())
    input_path = None

    # Option A: Sample selected
    if "sample_name" in request.form and request.form["sample_name"]:
        sample_name = secure_filename(request.form["sample_name"])
        candidate = os.path.join(app.config["SAMPLES_FOLDER"], sample_name)
        if os.path.exists(candidate):
            input_path = candidate
        else:
            return jsonify({"error": f"Sample {sample_name} not found"}), 404

    # Option B: Uploaded file
    elif "file" in request.files:
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            ext = filename.rsplit(".", 1)[1].lower()
            input_filename = f"{unique_id}.{ext}"
            input_path = os.path.join(app.config["UPLOAD_FOLDER"], input_filename)
            file.save(input_path)
        else:
            return jsonify({"error": "Invalid file type. Supported: PNG, JPG, JPEG, BMP, TIFF, WebP"}), 400
    else:
        return jsonify({"error": "Please provide either an image file or choose a sample."}), 400

    output_filename = f"{unique_id}.glb"
    output_path = os.path.join(app.config["OUTPUT_FOLDER"], output_filename)

    try:
        result = process_floorplan(
            input_path=input_path,
            output_path=output_path,
            weights_path=WEIGHTS_PATH,
            device="cpu",
            target_span_m=14.0
        )
        return jsonify({
            "success": True,
            "output_file": output_filename,
            "download_url": f"/download/{output_filename}",
            "view_url": f"/view/{output_filename}",
            "nodes": result.get("nodes", []),
            "bounds": result.get("bounds", []),
            "dimensions": {
                "wall_height": "2.70 m",
                "door_height": "2.00 m",
                "window_sill": "0.85 m",
                "window_height": "1.05 m",
                "blender_axis": "Native Z-Up via glTF 2.0"
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/download/<filename>")
def download(filename: str):
    filename = secure_filename(filename)
    path = os.path.join(app.config["OUTPUT_FOLDER"], filename)
    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404
    return send_file(path, as_attachment=True, download_name="floorplan_3d.glb")


@app.route("/view/<filename>")
def view(filename: str):
    filename = secure_filename(filename)
    path = os.path.join(app.config["OUTPUT_FOLDER"], filename)
    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404
    return send_file(path, mimetype="model/gltf-binary")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
