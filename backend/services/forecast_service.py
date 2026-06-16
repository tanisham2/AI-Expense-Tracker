import pandas as pd
import numpy as np
from backend.services.ml_service import run_xgboost_with_colab_features
import warnings
warnings.filterwarnings("ignore")

def run_prophet_forecast(daily_df: pd.DataFrame, periods: int = 30) -> pd.DataFrame:
    try:
        from prophet import Prophet
    except ImportError:
        raise Exception("Prophet not installed")

    if len(daily_df) < 10:
        raise Exception("Need at least 10 data points")

    m = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
        interval_width=0.80
    )
    m.fit(daily_df[["ds","y"]])
    future = m.make_future_dataframe(periods=periods)
    forecast = m.predict(future)
    result = forecast[["ds","yhat","yhat_lower","yhat_upper"]].tail(periods)
    result["yhat"] = result["yhat"].clip(lower=0)
    result["yhat_lower"] = result["yhat_lower"].clip(lower=0)
    return result.reset_index(drop=True)

def get_forecast(expenses_data: list, model_name: str = "Prophet", periods: int = 30) -> dict:
    """
    Main forecast entry point called by the API router.
    expenses_data: list of {"date": "2026-01-01", "amount": 500.0}
    """
    if not expenses_data:
        raise Exception("No expense data available")

    df = pd.DataFrame(expenses_data)
    df["ds"] = pd.to_datetime(df["date"])
    df["y"] = df["amount"].astype(float)
    daily = df.groupby("ds")["y"].sum().reset_index().sort_values("ds")

    if model_name == "Prophet":
        forecast_df = run_prophet_forecast(daily, periods)
    elif model_name == "XGBoost":
        forecast_df = run_xgboost_with_colab_features(daily, periods)
    else:
        raise Exception(f"Unknown model: {model_name}")

    forecast_df["ds"] = forecast_df["ds"].dt.strftime("%Y-%m-%d")
    return {
        "model": model_name,
        "periods": periods,
        "total_predicted": round(float(forecast_df["yhat"].sum()), 2),
        "avg_daily": round(float(forecast_df["yhat"].mean()), 2),
        "forecast": forecast_df.to_dict(orient="records")
    }