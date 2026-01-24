import rasterio
from rasterio.windows import Window
from pyproj import Transformer
import os
import logging
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
PH_PATH = "ph.h2o_usda.4c1a2a_m_250m_b10cm_19500101_20171231_go_epsg.4326_v0.2.tif"

# 2. Organic Carbon File (The new b10cm file you are downloading)
SOC_PATH = "organic.carbon_usda.6a1c_m_250m_b10cm_19500101_20171231_go_epsg.4326_v0.2.tif" 

def get_soil_values(lat, lon, base_dir, annual_rain_mm=1200, soil_moisture=0.35):
    """
    Hybrid Loader:
    - Checks global soil maps.
    - If NO data is found in maps, assumes Ocean/Water body and returns None.
    - If One map has data, uses fallbacks for the other.
    """
    results = {
        "E_soil_ph": None,
        "E_soil_nitrogen": None 
    }
    
    ph_file = os.path.join(base_dir, PH_PATH)
    soc_file = os.path.join(base_dir, SOC_PATH)

    ph_raw = _read_pixel(ph_file, lat, lon)
    soc_raw = _read_pixel(soc_file, lat, lon)

    # --- 1. MARINE / NO-DATA CHECK ---
    # If both global maps return NoData, we are 99% sure it's not arable land.
    if ph_raw is None and soc_raw is None:
        logger.warning(f"[Map] No soil data for {lat}, {lon}. Likely Water Body.")
        return None

    # --- 2. GET pH ---
    if ph_raw is not None:
        results["E_soil_ph"] = ph_raw / 10.0
        logger.info(f"[Map] pH Found: {results['E_soil_ph']}")
    else:
        # Partial Fallback (Map hole on land)
        est_ph = 7.5 - (annual_rain_mm / 2000.0)
        results["E_soil_ph"] = round(max(4.5, min(8.5, est_ph)), 2)

    # --- 3. GET NITROGEN ---
    if soc_raw is not None:
        carbon_g_kg = soc_raw * 5.0
        nitrogen_g_kg = carbon_g_kg / 10.0
        results["E_soil_nitrogen"] = round(nitrogen_g_kg, 2)
        logger.info(f"[Map] Carbon Found -> N: {results['E_soil_nitrogen']} g/kg")
    else:
        # Partial Fallback
        est_n = 1.0 + (soil_moisture * 5.0)
        results["E_soil_nitrogen"] = round(max(0.5, min(4.0, est_n)), 2)

    return results

def _read_pixel(filepath, lat, lon):
    """ Reads a single pixel from GeoTIFF, handling projections automatically. """
    if not os.path.exists(filepath):
        return None

    try:
        with rasterio.open(filepath) as src:
            # 1. Coordinate Transform (EPSG:4326 -> Map Projection)
            transformer = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
            x, y = transformer.transform(lon, lat)

            # 2. Bounds Check
            if not (src.bounds.left <= x <= src.bounds.right and \
                    src.bounds.bottom <= y <= src.bounds.top):
                return None

            # 3. Read Pixel
            row, col = src.index(x, y)
            window = Window(col, row, 1, 1)
            data = src.read(1, window=window)
            
            val = data[0, 0]
            if val == src.nodata or np.isnan(val) or val < 0:
                return None
                
            return float(val)

    except Exception as e:
        logger.error(f"Read Error {filepath}: {e}")
        return None