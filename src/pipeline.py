"""Main Floorplan to 3D Pipeline."""

from __future__ import annotations

import os
from pathlib import Path
import torch
import numpy as np
from PIL import Image

from .model import build_model
from .preprocess import preprocess_image
from .extract import extract_features
from .generate_3d import build_3d_scene

_LOADED_MODEL = None
_LOADED_DEVICE = None


def load_model(weights_path: str, device: str = "cpu"):
    """Load and cache the segmentation model."""
    global _LOADED_MODEL, _LOADED_DEVICE
    if _LOADED_MODEL is not None and _LOADED_DEVICE == device:
        return _LOADED_MODEL

    model = build_model(encoder_name="resnet34", encoder_weights=None)
    
    if weights_path.endswith(".safetensors"):
        from safetensors.torch import load_file
        state_dict = load_file(weights_path)
        model.load_state_dict(state_dict)
    else:
        checkpoint = torch.load(weights_path, map_location=device, weights_only=False)
        if isinstance(checkpoint, dict):
            for key in ["model", "state_dict", "model_state_dict"]:
                if key in checkpoint:
                    model.load_state_dict(checkpoint[key])
                    break
            else:
                model.load_state_dict(checkpoint)
        else:
            model.load_state_dict(checkpoint)

    model.to(device)
    model.eval()
    _LOADED_MODEL = model
    _LOADED_DEVICE = device
    return model


def run_inference(model, img_path: str, device: str = "cpu", target_size: int = 512):
    """Run model inference with aspect-preserving letterbox padding."""
    img_tensor, orig_size, scale, (offset_x, offset_y) = preprocess_image(img_path, target_size=target_size)
    img_tensor = img_tensor.to(device)

    with torch.no_grad():
        logits = model(img_tensor)
        pred = torch.argmax(logits, dim=1).squeeze(0).cpu().numpy().astype(np.uint8)

    # Optional: zero out padding area to avoid border artifacts
    orig_w, orig_h = orig_size
    valid_w = int(round(orig_w * scale))
    valid_h = int(round(orig_h * scale))
    
    mask_clean = np.zeros_like(pred)
    mask_clean[offset_y:offset_y + valid_h, offset_x:offset_x + valid_w] = (
        pred[offset_y:offset_y + valid_h, offset_x:offset_x + valid_w]
    )

    return mask_clean, orig_size, scale


def process_floorplan(
    input_path: str,
    output_path: str,
    weights_path: str | None = None,
    device: str = "cpu",
    target_span_m: float = 14.0,
) -> dict:
    """Full pipeline: input image -> AI segmentation -> 2D vectorization -> 3D scene -> GLB file."""
    if weights_path is None or not os.path.exists(weights_path):
        candidates = [
            "weights/best.safetensors",
            "weights/model.pth",
            os.path.join(os.path.dirname(__file__), "..", "weights", "best.safetensors"),
        ]
        for p in candidates:
            if os.path.exists(p):
                weights_path = p
                break
        if weights_path is None or not os.path.exists(weights_path):
            raise FileNotFoundError("Could not find model weights file (best.safetensors).")

    print(f"[1/4] Loading model weights: {weights_path}")
    model = load_model(weights_path, device)

    print(f"[2/4] Running segmentation on: {input_path}")
    pred_mask, orig_size, scale = run_inference(model, input_path, device=device)

    print("[3/4] Extracting architectural geometry & cutting wall openings...")
    features = extract_features(pred_mask)

    print("[4/4] Building 3D scene & aligning to glTF / Blender standard...")
    scene = build_3d_scene(features, target_span_m=target_span_m)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    scene.export(output_path, file_type="glb")
    print(f"[✓] GLB model exported successfully to: {output_path}")

    return {
        "output_path": output_path,
        "nodes": list(scene.geometry.keys()),
        "bounds": scene.bounds.tolist() if scene.bounds is not None else [],
    }
