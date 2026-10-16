"""Render white hand-sketched profile PNGs from licensed Flightradar24 GLB models.

The source GLB models must be downloaded separately from the upstream repository.
This script strips all original colours/liveries, renders the real 3D geometry
from the side with the nose pointing right, and writes transparent PNG assets.

Requires: numpy<2 (for pyrender), trimesh, pyrender, Pillow, PyOpenGL.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps
import trimesh


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "www" / "aircraft-png"
REPOSITORY = "https://github.com/Flightradar24/fr24-3d-models"

# ICAO code -> (source file, exact model name). Codes are included only when
# the upstream model matches the depicted variant; no generic substitution.
MODELS = {
    "A318": ("a318.glb", "Airbus A318"),
    "A319": ("a319.glb", "Airbus A319"),
    "A320": ("a320.glb", "Airbus A320"),
    "A321": ("a321.glb", "Airbus A321"),
    "A332": ("a332.glb", "Airbus A330-200"),
    "A333": ("a333.glb", "Airbus A330-300"),
    "A343": ("a343.glb", "Airbus A340-300"),
    "A346": ("a346.glb", "Airbus A340-600"),
    "A359": ("a359.glb", "Airbus A350-900"),
    "A388": ("a380.glb", "Airbus A380-800"),
    "AT45": ("atr42.glb", "ATR 42-500"),
    "B736": ("b736.glb", "Boeing 737-600"),
    "B737": ("b737.glb", "Boeing 737-700"),
    "B738": ("b738.glb", "Boeing 737-800"),
    "B739": ("b739.glb", "Boeing 737-900"),
    "B744": ("b744.glb", "Boeing 747-400"),
    "B748": ("b748.glb", "Boeing 747-8 Intercontinental"),
    "B752": ("b752.glb", "Boeing 757-200"),
    "B753": ("b753.glb", "Boeing 757-300"),
    "B762": ("b762.glb", "Boeing 767-200"),
    "B763": ("b763.glb", "Boeing 767-300"),
    "B764": ("b764.glb", "Boeing 767-400"),
    "B772": ("b772.glb", "Boeing 777-200"),
    "B773": ("b773.glb", "Boeing 777-300"),
    "B788": ("b788.glb", "Boeing 787-8"),
    "B789": ("b789.glb", "Boeing 787-9"),
    "BCS1": ("cs100.glb", "Airbus A220-100 (CS100)"),
    "BCS3": ("cs300.glb", "Airbus A220-300 (CS300)"),
    "CRJ7": ("crj700.glb", "Bombardier CRJ700"),
    "CRJ9": ("crj900.glb", "Bombardier CRJ900"),
    "DH8D": ("q400.glb", "De Havilland Canada Dash 8-400"),
    "E170": ("e170.glb", "Embraer E170"),
    "E190": ("e190.glb", "Embraer E190"),
}


def neutral_colour(mesh: trimesh.Trimesh) -> list[int]:
    """Keep component contrast (glass, metal, intakes) and erase livery colours."""
    material = getattr(mesh.visual, "material", None)
    name = str(getattr(material, "name", "")).lower()
    part = str(mesh.metadata.get("name", "")).lower()
    hint = f"{name} {part}"
    if any(token in hint for token in ("windscreen", "windshield", "cockpit", "glass", "window", "interior", "black", "rubber", "tire", "tyre", "blade", "fanwheel", "intakeinterior", "geardoor")):
        gray = 48
    elif any(token in hint for token in ("aluminum", "aluminium", "metal", "nozzle", "exhaust", "casing", "core", "pylon")):
        gray = 150
    else:
        gray = 222
    return [gray, min(gray + 2, 255), min(gray + 5, 255), 255]


def camera_pose(eye: np.ndarray, target: np.ndarray) -> np.ndarray:
    forward = target - eye
    forward /= np.linalg.norm(forward)
    up = np.array([0.0, 1.0, 0.0])
    right = np.cross(forward, up)
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    pose = np.eye(4)
    pose[:3, 0], pose[:3, 1], pose[:3, 2], pose[:3, 3] = right, up, -forward, eye
    return pose


def stylize_as_white_sketch(path: Path) -> None:
    """Turn the exact rendered model into white pencil/graphite linework."""
    source = Image.open(path).convert("RGBA")
    rgba = np.asarray(source, dtype=np.uint8)
    alpha = rgba[:, :, 3]
    luminance = np.asarray(ImageOps.grayscale(source), dtype=np.uint8)
    silhouette = Image.fromarray(alpha, "L")

    # Keep the airplane white while retaining subtle shading and dark glazing.
    # Treat aircraft surfaces as white, while retaining the dark glazing from
    # dedicated source meshes such as A380's `windscreen.mesh`. Some models
    # render that charcoal material above pure-black levels, so preserve a
    # broader low-luminance range instead of washing cockpit panes to white.
    values = np.where(luminance < 76, 48, 246 + (luminance.astype(np.float32) * 9 / 255)).clip(0, 255).astype(np.uint8)
    white_body = np.stack((values, np.minimum(values + 1, 255), np.minimum(values + 3, 255), alpha), axis=2)
    result = Image.fromarray(white_body, "RGBA")

    # The outside contour comes from the real model silhouette. A faint offset
    # second stroke and controlled grain keep the line from looking mechanical.
    eroded = silhouette.filter(ImageFilter.MinFilter(5))
    contour = ImageChops.subtract(silhouette, eroded)
    rng = np.random.default_rng(sum(ord(char) for char in path.stem))
    contour_pixels = np.asarray(contour, dtype=np.float32)
    contour_grain = rng.uniform(0.80, 1.0, contour_pixels.shape)
    contour = Image.fromarray(np.clip(contour_pixels * contour_grain * 0.90, 0, 255).astype(np.uint8), "L")
    # Two lighter, imperfect pencil passes make the boundary look hand-traced.
    for offset, opacity in (((1, 1), 72), ((-1, 2), 48)):
        stroke = Image.new("L", source.size, 0)
        stroke.paste(contour.point(lambda value: value * opacity // 255), offset)
        contour = ImageChops.lighter(contour, stroke)

    edge_source = ImageOps.grayscale(source).filter(ImageFilter.FIND_EDGES)
    edge_pixels = np.asarray(edge_source, dtype=np.float32)
    inside = (alpha > 16).astype(np.float32)
    detail_alpha = np.clip((edge_pixels - 38) * 1.45, 0, 160) * inside
    grain = rng.uniform(0.60, 1.0, detail_alpha.shape)
    detail_alpha = np.clip(detail_alpha * grain, 0, 255).astype(np.uint8)
    details = Image.fromarray(detail_alpha, "L").filter(ImageFilter.MaxFilter(3))

    # Fine diagonal pencil hatching stays clipped to naturally shaded parts
    # of the model, so it cannot change the aircraft's real outline.
    hatch = Image.new("L", source.size, 0)
    draw = ImageDraw.Draw(hatch)
    width, height = source.size
    for start in range(-height, width + height, 7):
        draw.line((start, height, start + height, 0), fill=58, width=1)
    shaded = Image.fromarray(np.clip((170 - luminance) * 0.7, 0, 58).astype(np.uint8), "L")
    lower_mask = np.broadcast_to(np.arange(height)[:, None] >= height * 0.66, (height, width))
    lower_edge = Image.fromarray(lower_mask.astype(np.uint8) * 255, "L")
    hatch_region = ImageChops.lighter(shaded, lower_edge)
    hatch_alpha = ImageChops.multiply(ImageChops.multiply(hatch, hatch_region), silhouette)

    for mask, color in ((hatch_alpha, (73, 81, 87, 0)), (details, (56, 66, 75, 0)), (contour, (44, 54, 63, 0))):
        layer = Image.new("RGBA", source.size, color[:3] + (0,))
        layer.putalpha(mask)
        result = Image.alpha_composite(result, layer)

    result.save(path, optimize=True)


def render(model_path: Path, destination: Path, width: int, height: int) -> None:
    # GLB v1 inputs are converted upstream to GLB v2 before rendering.
    scene = trimesh.load(model_path, force="scene")
    meshes = [part for part in scene.dump(concatenate=False) if isinstance(part, trimesh.Trimesh)]
    if not meshes:
        raise ValueError(f"No mesh geometry in {model_path}")

    bounds = np.array([np.concatenate([m.vertices for m in meshes]).min(axis=0),
                       np.concatenate([m.vertices for m in meshes]).max(axis=0)])
    extent = bounds[1] - bounds[0]
    center = bounds.mean(axis=0)
    # Upstream FlightGear-derived models have their fuselage along Z and span along X.
    # Looking from +X makes the nose point right in the output frame.
    import pyrender

    render_scene = pyrender.Scene(bg_color=[0, 0, 0, 0], ambient_light=[0.48, 0.48, 0.48])
    for mesh in meshes:
        mesh.visual = trimesh.visual.ColorVisuals(mesh=mesh, vertex_colors=neutral_colour(mesh))
        render_scene.add(pyrender.Mesh.from_trimesh(mesh, smooth=True))

    camera_distance = max(extent) * 3.0
    eye = center + np.array([camera_distance, 0.0, 0.0])
    pose = camera_pose(eye, center)
    camera = pyrender.OrthographicCamera(
        xmag=extent[2] * 0.90,
        ymag=max(extent[1] * 0.90, extent[2] / 6.0),
        znear=0.1,
        zfar=camera_distance * 3,
    )
    render_scene.add(camera, pose=pose)
    render_scene.add(pyrender.DirectionalLight(color=np.ones(3), intensity=2.0), pose=pose)

    renderer = pyrender.OffscreenRenderer(width, height)
    try:
        pixels, _ = renderer.render(render_scene, flags=pyrender.RenderFlags.RGBA)
    finally:
        renderer.delete()
    # Stage and validate each PNG before replacing the prior asset. A failed
    # renderer must never leave a zero-byte image in the card library.
    destination.parent.mkdir(parents=True, exist_ok=True)
    staged = destination.with_name(f".{destination.stem}.rendering.png")
    try:
        Image.fromarray(pixels, "RGBA").save(staged, optimize=True)
        stylize_as_white_sketch(staged)
        if staged.stat().st_size < 500:
            raise ValueError(f"Rendered PNG is unexpectedly small: {staged}")
        with Image.open(staged) as check:
            check.verify()
        staged.replace(destination)
    finally:
        staged.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_dir", type=Path, help="Directory containing upstream GLB v2 aircraft models")
    parser.add_argument("--width", type=int, default=900)
    parser.add_argument("--height", type=int, default=320)
    args = parser.parse_args()

    # pyrender currently uses the pre-NumPy-2 alias internally.
    if not hasattr(np, "infty"):
        np.infty = np.inf
    import pyrender  # noqa: F401

    catalog = []
    rendered_codes = set()
    for code, (filename, model_name) in MODELS.items():
        source = args.model_dir / filename
        if not source.is_file():
            print(f"skip {code}: missing {source}")
            continue
        destination = OUTPUT / f"{code}.png"
        render(source, destination, args.width, args.height)
        rendered_codes.add(code)
        catalog.append({
            "code": code,
            "model": model_name,
            "source": f"{REPOSITORY}/blob/master/models/{filename}",
            "license": "GPL-2.0",
            "view": "profile",
            "nose": "right",
            "livery": "removed; white hand-sketched rendering",
        })
        print(f"rendered {code}: {destination}")

    for image in OUTPUT.glob("*.png"):
        if image.stem not in rendered_codes:
            image.unlink()

    (OUTPUT / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")

    js = ["/* Neutral real-geometry profile PNGs; ICAO codes without an exact asset have no fallback. */",
          "const AIRCRAFT_PNG_CATALOG = {"]
    for item in catalog:
        js.append(f'  "{item["code"]}": {{ model: "{item["model"]}", src: "/avion_domicile/static/aircraft-png/{item["code"]}.png" }},')
    js.extend(["};", "", "export function aircraftPngForType(type) {",
               '  const code = String(type || "").toUpperCase().replace(/[^A-Z0-9]/g, "");',
               "  const item = AIRCRAFT_PNG_CATALOG[code];",
               '  return item ? { ...item, code, supported: true } : { code, model: code || "Type non identifié", src: null, supported: false };',
               "}", "", "export function listAircraftPngProfiles() {",
               "  return Object.entries(AIRCRAFT_PNG_CATALOG).map(([code, item]) => ({ code, ...item }));",
               "}", ""])
    (ROOT / "www" / "aircraft-png-library.js").write_text("\n".join(js))

    notice = (
        "Aircraft geometry source: Flightradar24/fr24-3d-models\n"
        f"{REPOSITORY}\n\n"
        "The upstream README credits the aircraft models to the FlightGear project and FGMEMBERS. "
        "The project states that all aircraft models other than the Millennium Falcon and Santa are licensed under GPLv2.\n"
        "Changes made here: converted to transparent PNG side views, removed all original material colours/liveries, "
        "rendered the aircraft white with graphite contours and hatching, and oriented the nose to the right.\n"
        "No airline livery or logo is baked into these PNGs.\n"
    )
    (OUTPUT / "ATTRIBUTION.txt").write_text(notice)


if __name__ == "__main__":
    main()
