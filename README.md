# Project 14A: Rice Phenotype Prediction

This project implements a machine learning pipeline to predict rice phenotypic traits, specifically the days to heading (HDG_80HEAD), based on genotypic markers and environmental conditions. The system integrates a high-performance ensemble model with a full-stack web application for accessible predictions.

## Machine Learning Model

The core predictive model is defined in `ML/model_xg_boost_elite_lightgbm_GE.py`.

### Architecture
The model utilizes a `VotingRegressor` ensemble to combine the strengths of two powerful gradient boosting frameworks:
*   **XGBoost Regressor**: Optimized for speed and performance.
*   **LightGBM Regressor**: Highly efficient gradient boosting decision tree.

### Pipeline
1.  **Data Ingestion**: Loads genotype (G) and environment (E) data.
2.  **Preprocessing**: Handles missing values and performs one-hot encoding for subpopulation data.
3.  **Feature Selection**: Uses an initial XGBoost model to select the top 500 most relevant features (`SelectFromModel`) from the high-dimensional genetic data.
4.  **Ensemble Training**: The selected features are fed into the Voting Regressor to produce the final prediction.

### Metrics
The model is validated using 5-fold Cross-Validation, tracking:
*   **R2 Score**: Coefficient of determination.
*   **MAE**: Mean Absolute Error (in days).

## Project Structure

The repository is organized into machine learning experiments and a web application.

```
/
├── ML/                 # Model training, data processing, and validation scripts
│   ├── model_*.py      # Various model architectures (Ridge, CatBoost, XGBoost)
│   ├── datasets/       # Raw genotype and phenotype data
│   └── plots/          # Generated performance visualizations
└── Web/                # Full-stack integration
    ├── client/         # React.js frontend (Vite + Tailwind)
    ├── server/         # Node.js Express API (Auth, User Management)
    └── fastAPI/        # Python API for Model Inference & Soil Data
```

## Installation and Usage

### Prerequisites
*   Node.js (v18+)
*   Python (v3.9+)
*   MongoDB

### Running the ML Pipeline
To retrain the model:
```bash
cd ML
python model_xg_boost_elite_lightgbm_GE.py
```

### Running the Web Application

1.  **FastAPI (Model Service)**
    ```bash
    cd Web/fastAPI
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000
    ```

2.  **Node.js Server (Backend)**
    ```bash
    cd Web/server
    npm install
    npm run dev
    ```

3.  **React Client (Frontend)**
    ```bash
    cd Web/client
    npm install
    npm run dev
    ```

The application will be available at `http://localhost:5173`.
