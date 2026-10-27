"""Extract clean Shapely 2D geometry from floor plan segmentation masks."""

from __future__ import annotations

import cv2
import numpy as np
from typing import Dict, Any
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

from .labels import WALL_ID, DOOR_ID, WINDOW_ID, FLOOR_ID


def mask_to_geometry(
    mask: np.ndarray,
    class_id: int,
    min_area: float = 12.0,
    simplify_tol: float = 0.8,
    closing_radius: int = 3,
) -> Polygon | MultiPolygon:
    """Extract topologically valid Shapely geometry from binary class mask."""
    binary = (mask == class_id).astype(np.uint8)
    if binary.sum() == 0:
        return Polygon()
    
    # Morphological closing to seal minor segmentation gaps
    if closing_radius > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (closing_radius, closing_radius))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hierarchy is None or len(contours) == 0:
        return Polygon()
    
    hierarchy = hierarchy[0]
    holes_by_parent: Dict[int, list] = {}
    for i, (_, _, _, parent) in enumerate(hierarchy):
        if parent != -1:
            holes_by_parent.setdefault(parent, []).append(i)
    
    polys = []
    for i, (_, _, _, parent) in enumerate(hierarchy):
        if parent != -1:
            continue
        if cv2.contourArea(contours[i]) < min_area:
            continue
        
        outer = contours[i].reshape(-1, 2)
        if len(outer) < 3:
            continue
        
        holes = []
        for j in holes_by_parent.get(i, []):
            if cv2.contourArea(contours[j]) < min_area:
                continue
            hole_pts = contours[j].reshape(-1, 2)
            if len(hole_pts) >= 3:
                holes.append(hole_pts)
        
        try:
            poly = Polygon(outer, holes)
            if not poly.is_valid:
                poly = poly.buffer(0)
            if not poly.is_empty and poly.area >= min_area:
                if simplify_tol > 0:
                    poly = poly.simplify(simplify_tol, preserve_topology=True)
                polys.append(poly)
        except Exception:
            pass
            
    if not polys:
        return Polygon()
    
    union_poly = unary_union(polys).buffer(0)
    return union_poly


def extract_features(mask: np.ndarray) -> Dict[str, Polygon | MultiPolygon]:
    """Extract clean vector geometries for walls, doors, windows, and floors."""
    features = {
        "wall": mask_to_geometry(mask, WALL_ID, min_area=15.0, simplify_tol=0.75, closing_radius=3),
        "door": mask_to_geometry(mask, DOOR_ID, min_area=8.0, simplify_tol=0.5, closing_radius=2),
        "window": mask_to_geometry(mask, WINDOW_ID, min_area=8.0, simplify_tol=0.5, closing_radius=2),
        "floor": mask_to_geometry(mask, FLOOR_ID, min_area=30.0, simplify_tol=1.0, closing_radius=5),
    }
    return features
