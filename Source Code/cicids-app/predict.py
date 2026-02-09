# predict.py
import os
import numpy as np
import pandas as pd
import joblib
import tensorflow as tf

# --- Paths (assumes these files are in the project root) ---
MODEL_PATH = "model.h5"
LABEL_ENCODER_PATH = "label_encoder.pkl"
SCALER_PATH = "scaler.pkl"
PCA_PATH = "pca.pkl"

# --- Ensure files exist ---
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"{MODEL_PATH} not found in project folder.")
if not os.path.exists(LABEL_ENCODER_PATH):
    raise FileNotFoundError(f"{LABEL_ENCODER_PATH} not found in project folder.")
if not os.path.exists(SCALER_PATH):
    raise FileNotFoundError(f"{SCALER_PATH} not found in project folder.")
if not os.path.exists(PCA_PATH):
    raise FileNotFoundError(f"{PCA_PATH} not found in project folder.")

# --- Load model & preprocessing objects once at import ---
model = tf.keras.models.load_model(MODEL_PATH)
label_encoder = joblib.load(LABEL_ENCODER_PATH)
scaler = joblib.load(SCALER_PATH)
pca = joblib.load(PCA_PATH)

EXPECTED_FEATURE_COUNT = None
if hasattr(scaler, "mean_"):
    EXPECTED_FEATURE_COUNT = scaler.mean_.shape[0]


def preprocess_and_predict(csv_path):
    """
    Robust preprocessing + prediction.
    Returns: list of labels or raises informative ValueError.
    """
    # 1) Read CSV
    df = pd.read_csv(csv_path)

    # 2) Normalize and clean column names
    df.columns = df.columns.str.strip()

    # 3) Drop irrelevant columns if present
    drop_cols = ['Flow ID', 'Source IP', 'Destination IP', 'Timestamp']
    df.drop(columns=[c for c in drop_cols if c in df.columns], inplace=True)

    # 4) Drop label column if present (handles 'Label' or ' Label' etc.)
    if 'Label' in df.columns:
        df = df.drop('Label', axis=1)

    # 5) Try coercing object columns to numeric (safe conversion)
    object_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    if object_cols:
        for c in object_cols:
            # coerce errors -> NaN
            df[c] = pd.to_numeric(df[c], errors='coerce')

    # 6) Replace inf with NaN and drop rows with NaN
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.dropna(inplace=True)

    # Basic checks
    if df.shape[0] == 0:
        raise ValueError("Uploaded CSV has no valid rows after cleaning (NaN/inf removal).")

    # 7) Ensure all remaining columns are numeric
    non_num_after = df.select_dtypes(exclude=[np.number]).columns.tolist()
    if non_num_after:
        raise ValueError(f"Found non-numeric columns after coercion: {non_num_after}. Remove/convert them before uploading.")

    # 8) Check expected feature count
    if EXPECTED_FEATURE_COUNT is not None and df.shape[1] != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            f"CSV has {df.shape[1]} features but model expects {EXPECTED_FEATURE_COUNT} features. "
            "Ensure CSV columns match training features (same names/order)."
        )

    # 9) Scale -> PCA -> reshape for model
    try:
        X_scaled = scaler.transform(df)
    except Exception as e:
        raise ValueError("Scaler.transform() failed: " + str(e))

    try:
        X_pca = pca.transform(X_scaled)
    except Exception as e:
        raise ValueError("PCA.transform() failed: " + str(e))

    if X_pca.ndim != 2:
        raise ValueError("PCA output has unexpected shape: " + str(X_pca.shape))

    X_final = X_pca.reshape(X_pca.shape[0], X_pca.shape[1], 1)

    # 10) Predict
    try:
        preds = model.predict(X_final)
    except Exception as e:
        raise ValueError("Model.predict() failed: " + str(e))

    pred_classes = np.argmax(preds, axis=1)
    labels = label_encoder.inverse_transform(pred_classes)

    # Limit UI results to first 100
    #modhatidi
    return labels.tolist()
    #rendavadi
    # preview = labels[:100]  

    # # Save full output to a file for download
    # full_output_path = csv_path.replace(".csv", "_predictions.csv")
    # pd.DataFrame({"Prediction": labels}).to_csv(full_output_path, index=False)

    # return preview, full_output_path

