
import math
import random
import Rhino.Geometry as rg


def create_crochet_pseudosphere(
    hyperbolic_rounds=2,
    first_round=12,
    increase=3,
    stitch_width=1.0,
    stitch_height=2.0,
    iterations=500,
    seed=17,
    subdivision=3,
    smooth_iterations=15,
    thickness=0.15
):
    """
    Abstract crochet growth mesh.

    Initial rounds:
        12 -> 12 -> 12

    Hyperbolic growth:
        12 -> 36 -> 108 ...

    The final mesh is subdivided, smoothed and thickened.
    """

    # --------------------------------------------------
    # 1. PARAMETERS
    # --------------------------------------------------

    first_round = int(first_round)
    increase = int(increase)
    hyperbolic_rounds = int(hyperbolic_rounds)
    iterations = int(iterations)
    subdivision = int(subdivision)
    smooth_iterations = int(smooth_iterations)

    stitch_width = float(stitch_width)
    stitch_height = float(stitch_height)
    thickness = float(thickness)

    if first_round < 3:
        raise ValueError("first_round must be at least 3.")

    if increase < 2:
        raise ValueError("increase must be at least 2.")

    if hyperbolic_rounds < 0:
        raise ValueError("hyperbolic_rounds cannot be negative.")

    if stitch_width <= 0 or stitch_height <= 0:
        raise ValueError("Stitch dimensions must be positive.")

    if iterations < 1:
        raise ValueError("iterations must be at least 1.")

    if subdivision < 0 or subdivision > 3:
        raise ValueError("subdivision must be between 0 and 3.")

    if smooth_iterations < 0:
        raise ValueError("smooth_iterations cannot be negative.")

    if thickness < 0:
        raise ValueError("thickness cannot be negative.")

    final_count = first_round * (increase ** hyperbolic_rounds)

    if final_count > 600:
        raise ValueError(
            "Too many stitches. Reduce hyperbolic_rounds or increase."
        )

    random.seed(seed)

    # --------------------------------------------------
    # 2. GEOMETRY STORAGE
    # --------------------------------------------------

    points = []
    rows = []
    faces = []

    def add_point(x, y, z):

        index = len(points)

        points.append([
            float(x),
            float(y),
            float(z)
        ])

        return index

    def create_ring(count, radius, z):

        ring = []

        for i in range(count):

            angle = 2.0 * math.pi * i / count

            ring.append(
                add_point(
                    radius * math.cos(angle),
                    radius * math.sin(angle),
                    z
                )
            )

        return ring

    # --------------------------------------------------
    # 3. INITIAL TWO FLAT ROUNDS
    # --------------------------------------------------

    radius = (
        first_round * stitch_width
        / (2.0 * math.pi)
    ) * 0.40

    # Starting contour
    rows.append(
        create_ring(first_round, radius, 0.0)
    )

    # Two rounds growing in XY
    for turn in range(2):

        radius += stitch_width

        rows.append(
            create_ring(first_round, radius, 0.0)
        )

    # Connect the flat rounds with quads
    for row_number in range(2):

        previous = rows[row_number]
        current = rows[row_number + 1]

        count = len(previous)

        for i in range(count):

            j = (i + 1) % count

            faces.append((
                previous[i],
                previous[j],
                current[j],
                current[i]
            ))

    # --------------------------------------------------
    # 4. HYPERBOLIC GROWTH
    # --------------------------------------------------

    growth_links = []

    for turn in range(hyperbolic_rounds):

        previous = rows[-1]

        old_count = len(previous)
        new_count = old_count * increase

        # Extra circumference from the new stitches
        radius += (
            (new_count - old_count)
            * stitch_width
            / (2.0 * math.pi)
        )

        z_level = (turn + 1) * stitch_height

        current = []

        for j in range(new_count):

            angle = 2.0 * math.pi * j / new_count

            # Small asymmetry for natural deformation
            angle += random.uniform(-0.003, 0.003)

            radial_noise = random.uniform(
                -0.015 * stitch_width,
                0.015 * stitch_width
            )

            r = radius + radial_noise

            z_noise = random.uniform(
                -0.02 * stitch_height,
                0.02 * stitch_height
            )

            current.append(
                add_point(
                    r * math.cos(angle),
                    r * math.sin(angle),
                    z_level + z_noise
                )
            )

        rows.append(current)

        # Parent-child connections
        for i in range(old_count):

            parent_a = previous[i]
            parent_b = previous[(i + 1) % old_count]

            child_start = i * increase

            for k in range(increase):

                child = current[child_start + k]

                t = float(k) / increase

                length_a = math.sqrt(
                    stitch_height ** 2
                    + (t * stitch_width) ** 2
                )

                length_b = math.sqrt(
                    stitch_height ** 2
                    + ((1.0 - t) * stitch_width) ** 2
                )

                growth_links.append(
                    (parent_a, child, length_a, 0.55)
                )

                growth_links.append(
                    (parent_b, child, length_b, 0.55)
                )

            # Faces between parent and children
            for k in range(increase - 1):

                a = parent_a
                b = current[child_start + k]
                c = current[child_start + k + 1]

                faces.append((a, b, c))

            # Bridge between neighbouring parent sectors
            next_child = current[
                ((i + 1) * increase) % new_count
            ]

            last_child = current[
                child_start + increase - 1
            ]

            faces.append((
                parent_a,
                last_child,
                next_child,
                parent_b
            ))

    # --------------------------------------------------
    # 5. BUILD CONSTRAINTS
    # --------------------------------------------------

    constraints = []

    def add_constraint(a, b, rest_length, stiffness):

        if a == b:
            return

        constraints.append((
            a,
            b,
            float(rest_length),
            float(stiffness)
        ))

    # Keep the initial three rings fixed
    fixed_vertices = set()

    for row in rows[:3]:

        for index in row:
            fixed_vertices.add(index)

    # Circumferential and bending constraints
    for row in rows:

        count = len(row)

        for i in range(count):

            j = (i + 1) % count

            add_constraint(
                row[i],
                row[j],
                stitch_width,
                0.85
            )

        # Second neighbours
        for i in range(count):

            j = (i + 2) % count

            add_constraint(
                row[i],
                row[j],
                2.0 * stitch_width,
                0.12
            )

        # Third neighbours
        for i in range(count):

            j = (i + 3) % count

            add_constraint(
                row[i],
                row[j],
                3.0 * stitch_width,
                0.025
            )

    # Growth constraints
    for a, b, length, stiffness in growth_links:

        add_constraint(
            a,
            b,
            length,
            stiffness
        )

    # --------------------------------------------------
    # 6. POSITION BASED CONSTRAINT SOLVER
    # --------------------------------------------------

    for iteration in range(iterations):

        if iteration % 2 == 0:
            active_constraints = constraints
        else:
            active_constraints = reversed(constraints)

        for a, b, rest_length, stiffness in active_constraints:

            pa = points[a]
            pb = points[b]

            dx = pb[0] - pa[0]
            dy = pb[1] - pa[1]
            dz = pb[2] - pa[2]

            distance = math.sqrt(
                dx * dx + dy * dy + dz * dz
            )

            if distance < 1e-9:
                continue

            error = (distance - rest_length) / distance
            correction = stiffness * error

            fixed_a = a in fixed_vertices
            fixed_b = b in fixed_vertices

            if fixed_a and fixed_b:
                continue

            if fixed_a:
                factor_a = 0.0
                factor_b = 1.0

            elif fixed_b:
                factor_a = 1.0
                factor_b = 0.0

            else:
                factor_a = 0.5
                factor_b = 0.5

            if factor_a > 0.0:

                pa[0] += dx * correction * factor_a
                pa[1] += dy * correction * factor_a
                pa[2] += dz * correction * factor_a

            if factor_b > 0.0:

                pb[0] -= dx * correction * factor_b
                pb[1] -= dy * correction * factor_b
                pb[2] -= dz * correction * factor_b

    # --------------------------------------------------
    # 7. CREATE INITIAL MESH
    # --------------------------------------------------

    mesh = rg.Mesh()

    for p in points:

        mesh.Vertices.Add(
            rg.Point3d(p[0], p[1], p[2])
        )

    for face in faces:

        if len(face) == 3:

            mesh.Faces.AddFace(
                face[0],
                face[1],
                face[2]
            )

        elif len(face) == 4:

            mesh.Faces.AddFace(
                face[0],
                face[1],
                face[2],
                face[3]
            )

    # --------------------------------------------------
    # 8. SUBDIVISION OF ALL MESH FACES
    # --------------------------------------------------

    def subdivide_all_faces(source_mesh):

        old_vertices = []

        for i in range(source_mesh.Vertices.Count):

            p = source_mesh.Vertices[i]

            old_vertices.append(
                rg.Point3d(p.X, p.Y, p.Z)
            )

        new_vertices = list(old_vertices)

        edge_midpoints = {}
        new_faces = []

        def midpoint_index(a, b):

            key = (min(a, b), max(a, b))

            if key in edge_midpoints:
                return edge_midpoints[key]

            pa = old_vertices[a]
            pb = old_vertices[b]

            midpoint = rg.Point3d(
                (pa.X + pb.X) * 0.5,
                (pa.Y + pb.Y) * 0.5,
                (pa.Z + pb.Z) * 0.5
            )

            index = len(new_vertices)

            new_vertices.append(midpoint)
            edge_midpoints[key] = index

            return index

        for i in range(source_mesh.Faces.Count):

            face = source_mesh.Faces[i]

            if face.IsTriangle:

                ids = [face.A, face.B, face.C]

            else:

                ids = [
                    face.A,
                    face.B,
                    face.C,
                    face.D
                ]

            # Face center
            cx = 0.0
            cy = 0.0
            cz = 0.0

            for index in ids:

                p = old_vertices[index]

                cx += p.X
                cy += p.Y
                cz += p.Z

            count = float(len(ids))

            center = rg.Point3d(
                cx / count,
                cy / count,
                cz / count
            )

            center_index = len(new_vertices)
            new_vertices.append(center)

            mids = []

            for j in range(len(ids)):

                a = ids[j]
                b = ids[(j + 1) % len(ids)]

                mids.append(
                    midpoint_index(a, b)
                )

            # One quad per original edge
            for j in range(len(ids)):

                previous_mid = mids[
                    (j - 1) % len(ids)
                ]

                current_mid = mids[j]

                new_faces.append((
                    ids[j],
                    current_mid,
                    center_index,
                    previous_mid
                ))

        result = rg.Mesh()

        for p in new_vertices:
            result.Vertices.Add(p)

        for face in new_faces:

            result.Faces.AddFace(
                face[0],
                face[1],
                face[2],
                face[3]
            )

        return result

    for level in range(subdivision):

        mesh = subdivide_all_faces(mesh)

    # --------------------------------------------------
    # 9. TAUBIN SMOOTHING
    # --------------------------------------------------

    def taubin_smooth(source_mesh, smooth_iterations=8):

        vertex_count = source_mesh.Vertices.Count

        neighbors = [
            set() for i in range(vertex_count)
        ]

        edge_counts = {}

        # Build vertex adjacency
        for i in range(source_mesh.Faces.Count):

            face = source_mesh.Faces[i]

            if face.IsTriangle:

                ids = [face.A, face.B, face.C]

            else:

                ids = [
                    face.A,
                    face.B,
                    face.C,
                    face.D
                ]

            for j in range(len(ids)):

                a = ids[j]
                b = ids[(j + 1) % len(ids)]

                neighbors[a].add(b)
                neighbors[b].add(a)

                key = (min(a, b), max(a, b))

                edge_counts[key] = (
                    edge_counts.get(key, 0) + 1
                )

        # Detect boundary edges
        boundary_neighbors = [
            set() for i in range(vertex_count)
        ]

        for edge, count in edge_counts.items():

            if count == 1:

                a, b = edge

                boundary_neighbors[a].add(b)
                boundary_neighbors[b].add(a)

        positions = []

        for i in range(vertex_count):

            p = source_mesh.Vertices[i]

            positions.append([
                p.X, p.Y, p.Z
            ])

        def smoothing_step(current, factor):

            updated = []

            for i in range(vertex_count):

                p = current[i]

                if len(boundary_neighbors[i]) == 2:

                    active = boundary_neighbors[i]

                elif len(boundary_neighbors[i]) > 0:

                    updated.append(list(p))
                    continue

                else:

                    active = neighbors[i]

                if not active:

                    updated.append(list(p))
                    continue

                average = [0.0, 0.0, 0.0]

                for j in active:

                    q = current[j]

                    average[0] += q[0]
                    average[1] += q[1]
                    average[2] += q[2]

                count = float(len(active))

                average = [
                    average[0] / count,
                    average[1] / count,
                    average[2] / count
                ]

                updated.append([
                    p[0] + factor * (average[0] - p[0]),
                    p[1] + factor * (average[1] - p[1]),
                    p[2] + factor * (average[2] - p[2])
                ])

            return updated

        # Taubin lambda-mu smoothing
        lam = 0.35
        mu = -0.36

        for iteration in range(smooth_iterations):

            positions = smoothing_step(
                positions,
                lam
            )

            positions = smoothing_step(
                positions,
                mu
            )

        for i, p in enumerate(positions):

            source_mesh.Vertices.SetVertex(
                i,
                rg.Point3f(p[0], p[1], p[2])
            )

        return source_mesh

    mesh = taubin_smooth(
        mesh,
        smooth_iterations=smooth_iterations
    )

    # --------------------------------------------------
    # 10. FINALIZE SURFACE BEFORE OFFSET
    # --------------------------------------------------

    mesh.Weld(math.radians(180))
    mesh.UnifyNormals()
    mesh.Normals.ComputeNormals()
    mesh.Compact()

    # --------------------------------------------------
    # 11. ADD THICKNESS
    # --------------------------------------------------

    if thickness > 0:

        try:

            thick_mesh = mesh.Offset(
                thickness,
                True
            )

            if thick_mesh is None:

                raise ValueError(
                    "Rhino could not create the thick mesh. "
                    "Try a smaller thickness."
                )

            mesh = thick_mesh

        except Exception as error:

            raise ValueError(
                "Mesh thickness failed: {0}. "
                "Try reducing thickness or checking the mesh."
                .format(error)
            )

    # --------------------------------------------------
    # 12. FINAL MESH
    # --------------------------------------------------

    mesh.Weld(math.radians(180))
    mesh.UnifyNormals()
    mesh.Normals.ComputeNormals()
    mesh.Compact()

    return mesh
