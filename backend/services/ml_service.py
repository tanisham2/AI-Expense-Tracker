import joblib
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

MODEL_PATH = "models/expense_category_model.pkl"

_category_model = None

def load_category_model():
    global _category_model
    if _category_model is None and os.path.exists(MODEL_PATH):
        try:
            _category_model = joblib.load(MODEL_PATH)
            print(f"✅ Loaded category model from {MODEL_PATH}")
        except Exception as e:
            print(f"⚠️ Could not load model: {e}")
    return _category_model

def predict_category(notes: str) -> dict:
    """
    Uses your Colab-trained expense_category_model.pkl
    to predict the category from expense notes/description
    """
    model = load_category_model()
    if model is None:
        return {"predicted_category": "Other", "confidence": None}

    try:
        pred = model.predict([notes])[0]
        confidence = None
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba([notes])[0]
            confidence = round(float(max(proba)), 3)
        return {"predicted_category": str(pred), "confidence": confidence}
    except Exception as e:
        return {"predicted_category": "Other", "confidence": None, "error": str(e)}


def build_features_from_colab(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replicates your Colab notebook's feature engineering:
    - Date features: Month, Day, Weekday
    - Lag features: Lag_1, Lag_2, Lag_3
    - Rolling Mean features
    This matches what your FinanceProj.ipynb does.
    """
    df = df.copy().sort_values("ds").reset_index(drop=True)
    df["ds"] = pd.to_datetime(df["ds"])

    # Date-based features (from your Colab)
    df["Month"] = df["ds"].dt.month
    df["Day"] = df["ds"].dt.day
    df["Weekday"] = df["ds"].dt.dayofweek
    df["Quarter"] = df["ds"].dt.quarter
    df["DayOfYear"] = df["ds"].dt.dayofyear
    df["WeekOfYear"] = df["ds"].dt.isocalendar().week.astype(int)
    df["IsWeekend"] = (df["Weekday"] >= 5).astype(int)

    # Lag features (from your Colab: Lag_1, Lag_2, Lag_3)
    df["Lag_1"] = df["y"].shift(1)
    df["Lag_2"] = df["y"].shift(2)
    df["Lag_3"] = df["y"].shift(3)
    df["Lag_7"] = df["y"].shift(7)
    df["Lag_14"] = df["y"].shift(14)

    # Rolling mean features (from your Colab)
    df["Rolling_Mean_7"] = df["y"].rolling(window=7, min_periods=1).mean()
    df["Rolling_Mean_14"] = df["y"].rolling(window=14, min_periods=1).mean()
    df["Rolling_Std_7"] = df["y"].rolling(window=7, min_periods=1).std().fillna(0)

    return df


FEATURE_COLS = [
    "Month", "Day", "Weekday", "Quarter", "DayOfYear", "WeekOfYear", "IsWeekend",
    "Lag_1", "Lag_2", "Lag_3", "Lag_7", "Lag_14",
    "Rolling_Mean_7", "Rolling_Mean_14", "Rolling_Std_7"
]


def run_xgboost_with_colab_features(daily_df: pd.DataFrame, periods: int = 30) -> pd.DataFrame:
    """
    XGBoost forecast using the exact same feature engineering from your Colab notebook.
    Falls back to training a fresh model if forecast_model.pkl is missing.
    """
    try:
        import xgboost as xgb
    except ImportError:
        raise Exception("XGBoost not installed")

    if len(daily_df) < 14:
        raise Exception("Need at least 14 days of data")

    df_feat = build_features_from_colab(daily_df).dropna()

    # Try to load your saved Colab model first
    colab_xgb_path = "models/forecast_model.pkl"
    if os.path.exists(colab_xgb_path):
        try:
            model = joblib.load(colab_xgb_path)
            print("✅ Using your Colab-trained XGBoost model")
        except Exception:
            model = None
    else:
        model = None

    # Train fresh if no saved model
    if model is None:
        X = df_feat[FEATURE_COLS]
        y = df_feat["y"]
        model = xgb.XGBRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbosity=0
        )
        model.fit(X, y)

    # Iterative future prediction
    full_df = daily_df.copy()
    forecast_rows = []

    for _ in range(periods):
        next_date = full_df["ds"].max() + timedelta(days=1)
        new_row = pd.DataFrame({"ds": [next_date], "y": [np.nan]})
        full_df = pd.concat([full_df, new_row], ignore_index=True)
        feat = build_features_from_colab(full_df)

        last_feat = feat.iloc[[-1]][FEATURE_COLS]
        if last_feat.isnull().any().any():
            pred = float(full_df["y"].dropna().tail(7).mean())
        else:
            pred = float(model.predict(last_feat)[0])
            pred = max(0, pred)

        full_df.loc[full_df.index[-1], "y"] = pred
        forecast_rows.append({
            "ds": next_date,
            "yhat": pred,
            "yhat_lower": pred * 0.80,
            "yhat_upper": pred * 1.20
        })

    return pd.DataFrame(forecast_rows)