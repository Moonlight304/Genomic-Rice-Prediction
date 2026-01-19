from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import joblib
import numpy as np
import os
import json
import logging
# --- CHANGED IMPORT ---
# We now import the generic loader that gets both pH and Nitrogen
from soil_loader import get_soil_values 

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS (Crucial for React Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(BASE_DIR, "rice_model_GE.pkl")

# Global Load
if os.path.exists(MODEL_FILE):
    package = joblib.load(MODEL_FILE)
    model = package["model"]
    selector = package["selector"]
    training_means = package["training_means"]
    training_columns = package["training_columns"]
    logger.info("✅ Model loaded successfully.")
else:
    logger.error(f"❌ Model file not found at {MODEL_FILE}")
    model = None

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

    # 1. Parse Environmental Data (from Node.js)
    try:
        env_dict = json.loads(env_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in env_data")

    # --- 2. INTELLIGENT SOIL LOOKUP (Hybrid Engine) ---
    # We try to overwrite Node's calculated values with Real Map Data
    if latitude and longitude:
        try:
            lat_val = float(latitude)
            lon_val = float(longitude)
            
            # Call the Loader (Gets pH AND Nitrogen)
            real_soil = get_soil_values(lat_val, lon_val, BASE_DIR)
            
            # Update pH
            if real_soil["E_soil_ph"] is not None:
                env_dict["E_soil_ph"] = real_soil["E_soil_ph"]
                print(f"✅ [PYTHON] Using MAP pH: {real_soil['E_soil_ph']}")
            
            # Update Nitrogen
            if real_soil["E_soil_nitrogen"] is not None:
                env_dict["E_soil_nitrogen"] = real_soil["E_soil_nitrogen"]
                print(f"✅ [PYTHON] Using MAP Nitrogen (from Carbon): {real_soil['E_soil_nitrogen']}")
            
        except Exception as e:
            print(f"❌ [PYTHON] Soil Lookup Error: {e}")

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
    print(f"ℹ️ Feature Overlap: {overlap_ratio:.1%}")

    # 6. Inject Env Data
    for col, value in env_dict.items():
        df[col] = value

    # 7. Alignment & Prediction
    aligned = df.reindex(columns=training_columns, fill_value=np.nan)
    aligned = aligned.fillna(training_means)

    try:
        X_elite = selector.transform(aligned.values)
        preds = model.predict(X_elite)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model Error: {str(e)}")

    # 8. Response
    results = []
    for i, pred in enumerate(preds):
        results.append({
            "sample_id": sample_ids[i],
            "predicted_days": round(float(pred), 2),
            "status": "High Confidence" if overlap_ratio > 0.5 else "Low Confidence"
        })

    return results