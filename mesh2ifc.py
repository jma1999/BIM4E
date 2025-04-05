import ifcopenshell
import ifcopenshell.api

def read_parsed_mesh_file(path):
    """
      Returns (vertices, faces) where
      vertices is a list of (x, y, z) floats
      faces is a list of [i, j, k, ...] integer vertex indices
    """
    vertices = []
    faces = []
    mode = None  # track if we are reading "Vertices" or "Faces"

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # skip blank lines
            if not line:
                continue

            # detect section
            if line.startswith("Vertices:"):
                mode = "verts"
                continue
            elif line.startswith("Faces:"):
                mode = "faces"
                continue
            elif line.startswith("==="):
                # skip lines like "=== Parsed Mesh Data ==="
                continue

            # if we are inside "Vertices" or "Faces" section, parse them
            if mode == "verts":
                # e.g. "0.0 0.0 1.0"
                parts = line.split()
                x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
                vertices.append((x, y, z))

            elif mode == "faces":
                # e.g. "1 2 3 4"
                parts = line.split()
                idxs = [int(x) for x in parts]
                faces.append(idxs)

    return vertices, faces

def create_ifc_from_mesh(verts, faces, output_ifc="GeneratedBlock.ifc"):
    # Create a new blank IFC file
    ifc_file = ifcopenshell.file()

    # Add a minimal project structure: project, site, building, storey
    project = ifcopenshell.api.run("project.create_project", ifc_file, name="LLM Mesh Project")
    site = ifcopenshell.api.run("root.create_entity", ifc_file, ifc_class="IfcSite", name="Site")
    building = ifcopenshell.api.run("root.create_entity", ifc_file, ifc_class="IfcBuilding", name="MyBuilding")
    storey = ifcopenshell.api.run("root.create_entity", ifc_file, ifc_class="IfcBuildingStorey", name="GroundFloor")

    # Add them in correct hierarchy
    ifcopenshell.api.run("aggregate.add_object", ifc_file, product=site, relating_object=project)
    ifcopenshell.api.run("aggregate.add_object", ifc_file, product=building, relating_object=site)
    ifcopenshell.api.run("aggregate.add_object", ifc_file, product=storey, relating_object=building)

    # Create geometry shape from the mesh
    shape = ifcopenshell.api.run(
        "geometry.add_faceted_brep_shape", 
        ifc_file,
        points=verts,
        faces=faces
    )

    # Create a BuildingElementProxy to hold the shape
    proxy = ifcopenshell.api.run(
        "root.create_entity",
        ifc_file, 
        ifc_class="IfcBuildingElementProxy", 
        name="GeneratedBlock"
    )

    # Assign the geometry to that product
    ifcopenshell.api.run("geometry.assign_shape", ifc_file, product=proxy, shape=shape)

    # Place it in the storey
    ifcopenshell.api.run("spatial.assign_container", ifc_file, product=proxy, relating_structure=storey)

    # Write out the IFC
    ifc_file.write(output_ifc)
    print(f"IFC file generated: {output_ifc}")


def main():
    # 1) Read the data from parsed_mesh.txt
    verts, faces = read_parsed_mesh_file("parsed_mesh.txt")

    # 2) Create IFC using IfcOpenShell
    create_ifc_from_mesh(verts, faces, output_ifc="GeneratedBlock.ifc")


if __name__ == "__main__":
    main()
