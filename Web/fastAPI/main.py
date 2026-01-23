from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import joblib
import numpy as np
import os
import json
import logging
from soil_loader import get_soil_values

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(BASE_DIR, "rice_model_GE.pkl")

if os.path.exists(MODEL_FILE):
    package = joblib.load(MODEL_FILE)
    model = package["model"]
    selector = package["selector"]
    training_means = package["training_means"]
    training_columns = package["training_columns"]
    logger.info("Model loaded successfully.")
else:
    logger.error(f"Model file not found at {MODEL_FILE}")
    model = None


def check_viability(env_dict):
    """
    Evaluates if environmental conditions are suitable for rice cultivation.
    Returns: (bool, str) -> (is_viable, reason_for_failure)
    """
    warnings = []

    # 1. Rainfall Check
    rain = env_dict.get('E_total_rain_mm', 0)
    if rain < 500:
        warnings.append(f"CRITICAL: Insufficient Rain ({rain}mm). Required >800mm.")

    # 2. Soil Nitrogen Check
    nitrogen = env_dict.get('E_soil_nitrogen', 0)
    if nitrogen < 0.8:
        warnings.append(f"Poor Soil Fertility (N={nitrogen} g/kg).")

    # 3. Temperature Check
    avg_temp = env_dict.get('E_avg_temp', 25)
    if avg_temp < 15:
        warnings.append(f"Too Cold ({avg_temp}C). Metabolic inactivity likely.")
    elif avg_temp > 40:
        warnings.append(f"Heat Stress ({avg_temp}C).")

    if len(warnings) > 0:
        return False, "; ".join(warnings)
    
    return True, "Favorable Conditions"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(
    file: UploadFile = File(...), 
    env_data: str = Form(...),
    latitude: str = Form(None), 
    longitude: str = Form(None)
):
    if model is None:
        raise HTTPException(status_code=500, detail="Model is not active.")

    # 1. Parse Environmental Data
    try:
        env_dict = json.loads(env_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in env_data")

    # 2. Intelligent Soil Lookup (Hybrid Approach)
    if latitude and longitude:
        try:
            lat_val = float(latitude)
            lon_val = float(longitude)
            
            current_rain = env_dict.get('E_total_rain_mm', 1200)
            current_moisture = env_dict.get('E_soil_moisture', 0.35)

            real_soil = get_soil_values(
                lat_val, 
                lon_val, 
                BASE_DIR, 
                annual_rain_mm=current_rain, 
                soil_moisture=current_moisture
            )
            
            if real_soil["E_soil_ph"] is not None:
                env_dict["E_soil_ph"] = real_soil["E_soil_ph"]
                print(f"[PYTHON] Using MAP pH: {real_soil['E_soil_ph']}")
            
            if real_soil["E_soil_nitrogen"] is not None:
                env_dict["E_soil_nitrogen"] = real_soil["E_soil_nitrogen"]
                print(f"[PYTHON] Using MAP Nitrogen: {real_soil['E_soil_nitrogen']}")
            
        except Exception as e:
            logger.error(f"Soil Lookup Error: {e}")

    # 3. Read Genetic Data
    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read CSV: {str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail="CSV is empty.")

    # 4. Preprocessing
    sample_ids = df.iloc[:, 0].astype(str).values
    df = df.iloc[:, 1:] 
    df = df.apply(pd.to_numeric, errors='coerce')

    # 5. Overlap Check
    required_snps = [c for c in training_columns if c not in env_dict.keys()]
    present_snps = [c for c in df.columns if c in required_snps]
    overlap_ratio = len(present_snps) / len(required_snps) if len(required_snps) > 0 else 0
    print(f"Feature Overlap: {overlap_ratio:.1%}")

    # 6. Inject Environmental Data
    for col, value in env_dict.items():
        df[col] = value

    # 7. Biological Viability Check
    is_viable, viability_reason = check_viability(env_dict)
    
    if not is_viable:
        print(f"[BIO-CHECK] Environment Unsuitable: {viability_reason}")

    # 8. Alignment & Prediction
    aligned = df.reindex(columns=training_columns, fill_value=np.nan)
    aligned = aligned.fillna(training_means)

    try:
        X_elite = selector.transform(aligned.values)
        preds = model.predict(X_elite)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model Error: {str(e)}")

    # 9. Format Response
    results = []
    for i, pred in enumerate(preds):
        
        status = "High Confidence"
        
        if overlap_ratio < 0.5:
            status = "Low Confidence (Missing SNPs)"
            
        if not is_viable:
            status = f"Unsuitable Environment: {viability_reason}"

        results.append({
            "sample_id": sample_ids[i],
            "predicted_days": round(float(pred), 2),
            "confidence": status
        })

    return results