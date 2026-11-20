import Rhino.Geometry as rg

# ==========================================
# 01 - CREATION OF A FAN OF SURFACES
# ==========================================

def create_fan(apex, S, N, T, target_y):

    surfaces = []

    N = int(N)

    if N < 1:
        return surfaces

    for k in range(N):

        t1 = k / float(N)
        t2 = (k + T) / float(N)

        # Points along the opposite edge
        p1 = rg.Point3d(t1 * S, target_y, 0)
        p2 = rg.Point3d(t2 * S, target_y, 0)

        # Creation of a triangular surface
        surface = rg.Brep.CreateFromCornerPoints(
            apex,
            p1,
            p2,
            0.001
        )

        if surface is not None:
            surfaces.append(surface)

    return surfaces


# ==========================================
# 02 - CREATION OF TWO CROSSED FANS
# ==========================================

def create_double_fan(S=10, N=12, T=0.5):

    # First convergence point:
    # bottom-left corner
    apex1 = rg.Point3d(0, 0, 0)

    # Second convergence point:
    # top-left corner
    apex2 = rg.Point3d(0, S, 0)

    # Fan 1: bottom to top
    fan1 = create_fan(
        apex1,
        S,
        N,
        T,
        S
    )

    # Fan 2: top to bottom
    fan2 = create_fan(
        apex2,
        S,
        N,
        T,
        0
    )

    # Assembly of the two families
    all_surfaces = fan1 + fan2

    return all_surfaces


# ==========================================
# 04 - PATH GENERATION
# ==========================================

def create_path(COLS=4, ROWS=3):

    COLS = int(COLS)
    ROWS = int(ROWS)

    path = []
    angle = 0

    for row in range(ROWS):

        if row % 2 == 0:
            columns = range(COLS)
        else:
            columns = range(COLS - 1, -1, -1)

        for col in columns:

            path.append((col, row, angle))

            angle = (angle + 90) % 360

    return path


# ==========================================
# 05 - PATTERN GENERATION
# ==========================================

def create_pattern(S=10, N=20, T=0.5,
                   COLS=4, ROWS=3):

    base = create_double_fan(S, N, T)

    path = create_path(COLS, ROWS)

    all_surfaces = []

    center = rg.Point3d(S / 2.0, S / 2.0, 0)

    for col, row, angle in path:

        rotation = rg.Transform.Rotation(
            angle * 3.141592653589793 / 180.0,
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

            new_surface.Transform(rotation)
            new_surface.Transform(translation)

            all_surfaces.append(new_surface)

    return all_surfaces