"""Labels, architectural heights (meters), and color tokens."""

NUM_CLASSES = 4
CLASS_NAMES = ["floor", "wall", "door", "window"]
CLASS_TO_ID = {name: idx for idx, name in enumerate(CLASS_NAMES)}

FLOOR_ID = CLASS_TO_ID["floor"]
WALL_ID = CLASS_TO_ID["wall"]
DOOR_ID = CLASS_TO_ID["door"]
WINDOW_ID = CLASS_TO_ID["window"]

# Architectural dimensions in meters
WALL_HEIGHT = 2.70
DOOR_HEIGHT = 2.00
DOOR_LINTEL_HEIGHT = 0.70  # WALL_HEIGHT - DOOR_HEIGHT

WINDOW_SILL = 0.85
WINDOW_HEIGHT = 1.05
WINDOW_LINTEL_HEIGHT = 0.80  # WALL_HEIGHT - (WINDOW_SILL + WINDOW_HEIGHT)

FLOOR_THICKNESS = 0.15

# Color tokens for 3D GLB export (RGBA: 0-255)
COLORS = {
    "wall": [242, 240, 236, 255],     # Off-white architectural plaster
    "door": [176, 122, 78, 255],      # Warm oak / teak wood
    "window": [140, 210, 245, 180],   # Translucent architectural glass
    "floor": [216, 210, 202, 255],    # Light neutral concrete / stone screed
}
