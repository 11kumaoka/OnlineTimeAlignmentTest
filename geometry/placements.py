"""Read the supported compact XML placements without modifying Geometry."""
import ast
import math
import xml.etree.ElementTree as ET

def xml_number(expr, constants):
    """Evaluate only arithmetic/constants used by this specific compact XML."""
    units = {"mm": 1., "cm": 10., "m": 1000., "um": .001, "pi": math.pi}

    def walk(node, stack):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return float(node.value)
        if isinstance(node, ast.Name):
            if node.id in units:
                return units[node.id]
            if node.id not in constants or node.id in stack:
                raise ValueError(f"Unsupported or recursive XML symbol: {node.id}")
            return walk(ast.parse(constants[node.id], mode="eval").body, stack | {node.id})
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            v = walk(node.operand, stack)
            return v if isinstance(node.op, ast.UAdd) else -v
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            a, b = walk(node.left, stack), walk(node.right, stack)
            if isinstance(node.op, ast.Add): return a + b
            if isinstance(node.op, ast.Sub): return a - b
            if isinstance(node.op, ast.Mult): return a * b
            return a / b
        raise ValueError(f"Unsupported XML arithmetic: {expr}")

    return walk(ast.parse(expr, mode="eval").body, set())


def geometry(path):
    """Validated for this telescope's DD4hep_SiTrackerEndcap2, phi0=0, nmodules=1.

    The DD4hep detector builder places a ring module at global x = -r at phi0=0.
    This is a placement preview, NOT a generic GDML/TGeo geometry converter.
    """
    root = ET.parse(path).getroot()
    constants = {c.attrib["name"]: c.attrib["value"] for c in root.findall("./define/constant")}
    result = {}
    for det in root.findall("./detectors/detector"):
        name = det.get("name")
        if name not in ("SiMAPS", "MPGDPlane", "ACLGADPlane"):
            continue
        if det.get("type") != "DD4hep_SiTrackerEndcap2":
            raise RuntimeError(f"Unexpected detector builder: {name}")
        for layer in det.findall("layer"):
            for ring in layer.findall("ring"):
                if ring.get("nmodules") != "1":
                    raise RuntimeError("Viewer supports only a single module per layer")
                phi = xml_number(ring.get("phi0", "0"), constants)
                if abs(phi) > 1e-12:
                    raise RuntimeError("Viewer assumes phi0=0")
                z = xml_number(ring.attrib["zstart"], constants) + xml_number(ring.get("dz", "0"), constants)
                x = -xml_number(ring.attrib["r"], constants)
                lid = int(layer.attrib["id"])
                result[lid] = (x, z, name)
    if set(result) != set(range(7)):
        raise RuntimeError(f"Expected seven layers L0..L6 in {path}, got {sorted(result)}")
    return result
