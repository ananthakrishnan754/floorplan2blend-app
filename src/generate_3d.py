"""Generate production-ready architectural 3D GLB models from floor plan geometries."""

from __future__ import annotations

import numpy as np
import trimesh
from typing import Dict, Any, List
from shapely.geometry import Polygon, MultiPolygon, box
from shapely.ops import unary_union
from shapely import affinity

from .labels import (
    WALL_HEIGHT,
    DOOR_HEIGHT,
    DOOR_LINTEL_HEIGHT,
    WINDOW_SILL,
    WINDOW_HEIGHT,
    WINDOW_LINTEL_HEIGHT,
    FLOOR_THICKNESS,
    COLORS,
)

# Transformation matrix to convert local mesh (X=2D x, Y=2D y, Z=height)
# into standard glTF 2.0 (X=right, Y=height/up, Z=-depth):
T_GLTF = np.array([
    [1.0,  0.0,  0.0, 0.0],
    [0.0,  0.0,  1.0, 0.0],
    [0.0, -1.0,  0.0, 0.0],
    [0.0,  0.0,  0.0, 1.0]
], dtype=float)


def extrude_geometry(
    geom: Polygon | MultiPolygon,
    height: float,
    z_offset: float = 0.0,
    color: List[int] = [240, 240, 240, 255],
) -> trimesh.Trimesh | None:
    """Extrude a 2D Shapely geometry along Z and align to glTF Y-up standard."""
    if geom is None or geom.is_empty:
        return None
    
    geoms = list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]
    meshes = []
    
    for g in geoms:
        if g.is_empty or g.area < 0.0005:
            continue
        try:
            m = trimesh.creation.extrude_polygon(g, height=height)
            if z_offset != 0.0:
                m.apply_translation([0.0, 0.0, z_offset])
            meshes.append(m)
        except Exception:
            # Fallback if triangulation of a degenerate polygon fails
            pass
            
    if not meshes:
        return None
    
    combined = trimesh.util.concatenate(meshes)
    combined.visual.face_colors = color
    combined.apply_transform(T_GLTF)
    return combined


def build_3d_scene(features: Dict[str, Polygon | MultiPolygon], target_span_m: float = 14.0) -> trimesh.Scene:
    """Convert extracted 2D architectural features into a complete 3D scene."""
    scene = trimesh.Scene()
    
    s_wall = features.get("wall", Polygon())
    s_door = features.get("door", Polygon())
    s_win = features.get("window", Polygon())
    
    # Calculate bounding box to normalize coordinates to real-world meters
    active_shapes = [s for s in [s_wall, s_door, s_win] if not s.is_empty]
    if not active_shapes:
        # Fallback empty floor if no structural elements
        fallback_floor = trimesh.creation.box(extents=[10, 0.1, 10])
        fallback_floor.visual.face_colors = COLORS["floor"]
        scene.add_geometry(fallback_floor, node_name="floor_slab")
        return scene

    total_bounds = unary_union(active_shapes).bounds
    min_x, min_y, max_x, max_y = total_bounds
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    max_dim = max(max_x - min_x, max_y - min_y)
    scale = target_span_m / max(max_dim, 1.0)

    def normalize(geom: Polygon | MultiPolygon) -> Polygon | MultiPolygon:
        if geom.is_empty:
            return geom
        # Center at origin (0, 0) and scale to real-world meters
        g = affinity.translate(geom, xoff=-center_x, yoff=-center_y)
        g = affinity.scale(g, xfact=scale, yfact=scale, origin=(0, 0))
        return g.buffer(0)

    wall_norm = normalize(s_wall)
    door_norm = normalize(s_door)
    win_norm = normalize(s_win)

    # Cut openings through walls for doors and windows
    openings = unary_union([s for s in [door_norm, win_norm] if not s.is_empty])
    if not openings.is_empty:
        # Small buffer to prevent zero-thickness sliver walls at opening boundaries
        cutter = openings.buffer(0.04)
        wall_main = wall_norm.difference(cutter).buffer(0)
        
        # Openings within or adjacent to walls
        door_openings = door_norm if not door_norm.is_empty else Polygon()
        win_openings = win_norm if not win_norm.is_empty else Polygon()
    else:
        wall_main = wall_norm
        door_openings = Polygon()
        win_openings = Polygon()

    # 1. Main walls (full height with door/window cutouts)
    m_walls = extrude_geometry(
        wall_main,
        height=WALL_HEIGHT,
        z_offset=0.0,
        color=COLORS["wall"]
    )
    if m_walls:
        scene.add_geometry(m_walls, node_name="walls")

    # 2. Doors: lintel above (wall material) + door panel
    if not door_openings.is_empty:
        m_door_lintel = extrude_geometry(
            door_openings,
            height=DOOR_LINTEL_HEIGHT,
            z_offset=DOOR_HEIGHT,
            color=COLORS["wall"]
        )
        if m_door_lintel:
            scene.add_geometry(m_door_lintel, node_name="door_lintels")

        m_door_panel = extrude_geometry(
            door_openings,
            height=DOOR_HEIGHT,
            z_offset=0.0,
            color=COLORS["door"]
        )
        if m_door_panel:
            scene.add_geometry(m_door_panel, node_name="doors")

    # 3. Windows: lintel above + sill below + glass pane
    if not win_openings.is_empty:
        m_win_lintel = extrude_geometry(
            win_openings,
            height=WINDOW_LINTEL_HEIGHT,
            z_offset=WINDOW_SILL + WINDOW_HEIGHT,
            color=COLORS["wall"]
        )
        if m_win_lintel:
            scene.add_geometry(m_win_lintel, node_name="window_lintels")

        m_win_sill = extrude_geometry(
            win_openings,
            height=WINDOW_SILL,
            z_offset=0.0,
            color=COLORS["wall"]
        )
        if m_win_sill:
            scene.add_geometry(m_win_sill, node_name="window_sills")

        m_glass = extrude_geometry(
            win_openings,
            height=WINDOW_HEIGHT,
            z_offset=WINDOW_SILL,
            color=COLORS["window"]
        )
        if m_glass:
            scene.add_geometry(m_glass, node_name="window_glass")

    # 4. Floor slab extending slightly past building footprint
    pad = 0.6  # 60cm foundation / ground border
    floor_box = box(
        (min_x - center_x) * scale - pad,
        (min_y - center_y) * scale - pad,
        (max_x - center_x) * scale + pad,
        (max_y - center_y) * scale + pad,
    )
    m_floor = extrude_geometry(
        floor_box,
        height=FLOOR_THICKNESS,
        z_offset=-FLOOR_THICKNESS,
        color=COLORS["floor"]
    )
    if m_floor:
        scene.add_geometry(m_floor, node_name="floor_slab")

    return scene
