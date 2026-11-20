import Rhino.Geometry as rg
import math
import random


# ==========================================
# 1. FAN CREATION
# ==========================================

def create_fan(apex, S, N, T, target_y):

    surfaces = []
    N = int(N)

    if N < 1:
        return surfaces

    for k in range(N):

        t1 = k / float(N)
        t2 = (k + T) / float(N)

        p1 = rg.Point3d(t1 * S, target_y, 0)
        p2 = rg.Point3d(t2 * S, target_y, 0)

        surface = rg.Brep.CreateFromCornerPoints(
            apex, p1, p2, 0.001
        )

        if surface is not None:
            surfaces.append(surface)

    return surfaces


# ==========================================
# 2. DOUBLE FAN CREATION
# ==========================================

def create_double_fan(S, N, T):

    apex1 = rg.Point3d(0, 0, 0)
    apex2 = rg.Point3d(0, S, 0)

    fan1 = create_fan(apex1, S, N, T, S)
    fan2 = create_fan(apex2, S, N, T, 0)

    return fan1 + fan2


# ==========================================
# 3. SNAKE-LIKE PATH
# ==========================================

def create_path(COLS, ROWS):

    positions = []

    COLS = int(COLS)
    ROWS = int(ROWS)

    for row in range(ROWS):

        if row % 2 == 0:
            columns = range(COLS)
        else:
            columns = range(COLS - 1, -1, -1)

        for col in columns:
            positions.append((col, row))

    return positions


# ==========================================
# 4. TILE PLACEMENT AND ROTATION
# ==========================================

def place_tile(base, S, col, row, angle):

    result = []

    center = rg.Point3d(
        S / 2.0,
        S / 2.0,
        0
    )

    rotation = rg.Transform.Rotation(
        math.radians(angle),
        rg.Vector3d(0, 0, 1),
        center
    )

    translation = rg.Transform.Translation(
        col * S,
        row * S,
        0
    )

    for surface in base:

        new_surface = surface.DuplicateBrep()

        # Rotate the tile around its center
        new_surface.Transform(rotation)

        # Move it to its position in the grid
        new_surface.Transform(translation)

        result.append(new_surface)

    return result


# ==========================================
# 5. RANDOM GRID CREATION
# ==========================================

def create_pattern(S=10, N=20, T=0.5,
                   COLS=6, ROWS=6):

    COLS = int(COLS)
    ROWS = int(ROWS)

    if COLS < 1 or ROWS < 1:
        return [], [], [], ["Invalid dimensions"]

    # Create the base module
    base = create_double_fan(S, N, T)

    if len(base) == 0:
        return [], [], [], ["No surfaces created"]

    # Create the path
    positions = create_path(COLS, ROWS)

    # Separate geometries by color
    blue = []
    yellow = []
    red = []

    # Tile types and number of repetitions
    tile_types = [
        ("blue", 3),
        ("yellow", 2),
        ("red", 1)
    ]

    # Initialization
    index = 0
    previous_color = None
    angle = 0

    blue_count = 0
    yellow_count = 0
    red_count = 0

    # Fill the grid
    while index < len(positions):

        # Choose a color different from the previous group
        available_colors = [
            item for item in tile_types
            if item[0] != previous_color
        ]

        color, repetition = random.choice(
            available_colors
        )

        # Rotate by 90 degrees at each color change
        if previous_color is not None:
            angle = (angle + 90) % 360

        # Available positions for this group
        group_positions = positions[
            index:index + repetition
        ]

        # Place all tiles in the group
        for col, row in group_positions:

            tile = place_tile(
                base,
                S,
                col,
                row,
                angle
            )

            if color == "blue":
                blue.extend(tile)

            elif color == "yellow":
                yellow.extend(tile)

            elif color == "red":
                red.extend(tile)

        # Count occupied cells
        if color == "blue":
            blue_count += len(group_positions)

        elif color == "yellow":
            yellow_count += len(group_positions)

        elif color == "red":
            red_count += len(group_positions)

        # Update the sequence
        index += len(group_positions)
        previous_color = color

    # Diagnostic information
    debug = [
        "Total number of cells: " + str(len(positions)),
        "Blue cells: " + str(blue_count),
        "Yellow cells: " + str(yellow_count),
        "Red cells: " + str(red_count),
        "Total filled cells: " + str(
            blue_count + yellow_count + red_count
        )
    ]

    return blue, yellow, red, debug