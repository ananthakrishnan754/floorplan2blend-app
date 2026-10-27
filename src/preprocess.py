"""Image preprocessing for floorplans matching CubiCasa5k training format."""

from __future__ import annotations

import numpy as np
from PIL import Image
import torch


def preprocess_image(img_path: str, target_size: int = 512) -> tuple[torch.Tensor, tuple[int, int], float, tuple[int, int]]:
    """Load and preprocess floorplan image with aspect-preserving letterbox padding.
    
    Returns:
        img_tensor: Torch tensor of shape (1, 3, target_size, target_size)
        orig_size: (width, height) of original image
        scale: resize scale factor
        pad_offsets: (offset_x, offset_y) inside the padded target_size canvas
    """
    img = Image.open(img_path).convert("RGB")
    orig_w, orig_h = img.size
    
    # Aspect-ratio preserving resize
    scale = target_size / max(orig_w, orig_h)
    new_w = max(1, int(round(orig_w * scale)))
    new_h = max(1, int(round(orig_h * scale)))
    
    img_resized = img.resize((new_w, new_h), Image.LANCZOS)
    
    # White background letterbox padding (CubiCasa standard)
    padded = Image.new("RGB", (target_size, target_size), (255, 255, 255))
    offset_x = (target_size - new_w) // 2
    offset_y = (target_size - new_h) // 2
    padded.paste(img_resized, (offset_x, offset_y))
    
    # ImageNet normalization
    img_array = np.array(padded, dtype=np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    img_norm = (img_array - mean) / std
    
    # Shape: (1, 3, H, W)
    img_tensor = torch.from_numpy(img_norm.transpose(2, 0, 1)[np.newaxis, ...]).float()
    
    return img_tensor, (orig_w, orig_h), scale, (offset_x, offset_y)
