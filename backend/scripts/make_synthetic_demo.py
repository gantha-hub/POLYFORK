"""Synthetic Demo Asset Generator for VrikshaVision.

Generates sample assets for end-to-end demonstrations:
1. data/demo_aerial_tile.tif: A 1024x1024 3-band GeoTIFF with EPSG:4326 georeferencing
   and realistic procedural tree canopy clusters with varying crown sizes.
2. data/demo_ground_plots.csv: A 14-plot field audit calibration CSV containing ground-truth
   counts (G) and aerial detected counts (V) that satisfies the N >= 10 validation rule.

Usage:
    python scripts/make_synthetic_demo.py
"""

from pathlib import Path
import csv
import math
import numpy as np
import rasterio
from rasterio.transform import from_origin


def create_demo_aerial_tile(output_path: Path, width: int = 1024, height: int = 1024) -> Path:
    """Generates a 1024x1024 multi-band GeoTIFF with simulated tree canopies."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # EPSG:4326 Georeferencing (Coordinates around Western Ghats, India)
    west_lon = 76.5400
    north_lat = 12.1500
    # ~0.5 meter per pixel in degrees (~0.000005 deg)
    res_deg = 0.000005
    transform = from_origin(west_lon, north_lat, res_deg, res_deg)

    # 1. Base ground landscape: Warm soil and low grass base
    rng = np.random.default_rng(seed=42)
    base_noise = rng.normal(0, 4, (height, width))

    red_band = np.clip(60 + base_noise, 40, 90).astype(np.uint8)
    green_band = np.clip(110 + base_noise * 1.5, 80, 140).astype(np.uint8)
    blue_band = np.clip(50 + base_noise, 30, 80).astype(np.uint8)

    # 2. Procedural tree crowns
    # We place clusters of tree centers across the image
    # including cross-tile boundaries (x or y near 512) to test stitching.
    tree_centers = []

    # Cluster 1: Top-Left dense stand
    for _ in range(40):
        cx = rng.integers(60, 450)
        cy = rng.integers(60, 450)
        radius = rng.integers(12, 32)
        tree_centers.append((cx, cy, radius, rng.uniform(0.7, 1.0)))

    # Cluster 2: Bottom-Right dense stand
    for _ in range(45):
        cx = rng.integers(560, 960)
        cy = rng.integers(560, 960)
        radius = rng.integers(14, 35)
        tree_centers.append((cx, cy, radius, rng.uniform(0.75, 1.0)))

    # Cluster 3: Seam-crossing cluster around x=512, y=512
    for _ in range(30):
        cx = rng.integers(420, 600)
        cy = rng.integers(420, 600)
        radius = rng.integers(15, 30)
        tree_centers.append((cx, cy, radius, rng.uniform(0.7, 0.95)))

    # Cluster 4: Top-Right scattered trees
    for _ in range(25):
        cx = rng.integers(580, 950)
        cy = rng.integers(70, 460)
        radius = rng.integers(10, 26)
        tree_centers.append((cx, cy, radius, rng.uniform(0.65, 0.9)))

    # Cluster 5: Bottom-Left riparian strip
    for _ in range(25):
        cx = rng.integers(70, 470)
        cy = rng.integers(580, 950)
        radius = rng.integers(12, 28)
        tree_centers.append((cx, cy, radius, rng.uniform(0.7, 0.95)))

    # Render crowns onto image
    y_coords, x_coords = np.ogrid[:height, :width]

    for cx, cy, radius, vigor in tree_centers:
        dist_sq = (x_coords - cx) ** 2 + (y_coords - cy) ** 2
        mask = dist_sq <= (radius ** 2)

        if not np.any(mask):
            continue

        # Radial falloff for dome-like crown brightness
        norm_dist = np.sqrt(dist_sq[mask]) / radius
        radial_factor = 1.0 - (norm_dist ** 1.8) * 0.45

        # Canopy green coloration
        g_val = np.clip(180 + 75 * vigor * radial_factor, 140, 255).astype(np.uint8)
        r_val = np.clip(30 + 35 * (1.0 - radial_factor), 15, 75).astype(np.uint8)
        b_val = np.clip(35 + 30 * (1.0 - radial_factor), 20, 70).astype(np.uint8)

        # Highlight center, shade periphery
        green_band[mask] = np.maximum(green_band[mask], g_val)
        red_band[mask] = np.where(green_band[mask] > 180, r_val, red_band[mask])
        blue_band[mask] = np.where(green_band[mask] > 180, b_val, blue_band[mask])

    # Write GeoTIFF
    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=3,
        dtype=np.uint8,
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(np.stack([red_band, green_band, blue_band]))

    print(f"[+] Created synthetic GeoTIFF: {output_path} ({width}x{height}, EPSG:4326)")
    return output_path


def create_demo_ground_plots(output_path: Path) -> Path:
    """Generates a 14-plot ground calibration CSV satisfying N >= 10 refusal constraint."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 14 representative field inventory audit plots
    plots = [
        {"plot_name": "Plot_Alpha_01", "G": 38, "V": 34, "canopy_cover": 78.5, "crown_area": 19.2, "forest_type": "tropical_moist"},
        {"plot_name": "Plot_Alpha_02", "G": 42, "V": 37, "canopy_cover": 82.0, "crown_area": 21.0, "forest_type": "tropical_moist"},
        {"plot_name": "Plot_Alpha_03", "G": 29, "V": 27, "canopy_cover": 65.4, "crown_area": 16.5, "forest_type": "tropical_moist"},
        {"plot_name": "Plot_Alpha_04", "G": 51, "V": 44, "canopy_cover": 88.2, "crown_area": 23.4, "forest_type": "tropical_moist"},
        {"plot_name": "Plot_Beta_05",  "G": 24, "V": 23, "canopy_cover": 58.0, "crown_area": 15.1, "forest_type": "tropical_moist"},
        {"plot_name": "Plot_Beta_06",  "G": 33, "V": 31, "canopy_cover": 71.5, "crown_area": 18.0, "forest_type": "tropical_moist"},
        {"plot_name": "Plot_Beta_07",  "G": 46, "V": 40, "canopy_cover": 84.1, "crown_area": 22.8, "forest_type": "tropical_moist"},
        {"plot_name": "Plot_Gamma_08", "G": 19, "V": 18, "canopy_cover": 49.3, "crown_area": 14.2, "forest_type": "tropical_moist"},
        {"plot_name": "Plot_Gamma_09", "G": 36, "V": 33, "canopy_cover": 75.0, "crown_area": 18.9, "forest_type": "tropical_moist"},
        {"plot_name": "Plot_Gamma_10", "G": 40, "V": 36, "canopy_cover": 79.8, "crown_area": 20.4, "forest_type": "tropical_moist"},
        {"plot_name": "Plot_Delta_11", "G": 28, "V": 26, "canopy_cover": 62.1, "crown_area": 17.1, "forest_type": "tropical_moist"},
        {"plot_name": "Plot_Delta_12", "G": 44, "V": 39, "canopy_cover": 83.5, "crown_area": 22.0, "forest_type": "tropical_moist"},
        {"plot_name": "Plot_Delta_13", "G": 31, "V": 29, "canopy_cover": 69.2, "crown_area": 17.8, "forest_type": "tropical_moist"},
        {"plot_name": "Plot_Delta_14", "G": 48, "V": 42, "canopy_cover": 86.7, "crown_area": 24.1, "forest_type": "tropical_moist"},
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["plot_name", "G", "V", "canopy_cover", "crown_area", "forest_type"],
        )
        writer.writeheader()
        writer.writerows(plots)

    print(f"[+] Created synthetic ground audit CSV: {output_path} ({len(plots)} plots, satisfies N >= 10)")
    return output_path


def main():
    """Generates all demonstration assets into the backend data/ folder."""
    root_dir = Path(__file__).resolve().parent.parent
    data_dir = root_dir / "data"

    demo_geotiff = data_dir / "demo_aerial_tile.tif"
    demo_csv = data_dir / "demo_ground_plots.csv"

    print("Generating VrikshaVision synthetic demonstration assets...")
    create_demo_aerial_tile(demo_geotiff)
    create_demo_ground_plots(demo_csv)
    print("\nDemonstration assets are ready in data/ folder:")
    print(f"  GeoTIFF: {demo_geotiff}")
    print(f"  CSV:     {demo_csv}")


if __name__ == "__main__":
    main()
