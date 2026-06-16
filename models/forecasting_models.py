import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def run_prophet_forecast(df, periods=30):
    try:
        from prophet import Prophet
    except ImportError:
        return None, "Prophet not installed. Run: pip install prophet"

    if df.empty or len(df) < 5:
        return None, "Need at least 5 data points for forecasting."

    try:
        ts = df[['ds', 'y']].copy()
        ts['ds'] = pd.to_datetime(ts['ds'])

        m = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=0.05,
            interval_width=0.80
        )
        m.fit(ts)

        future = m.make_future_dataframe(periods=periods)
        forecast = m.predict(future)

        result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods)
        result['yhat'] = result['yhat'].clip(lower=0)
        result['yhat_lower'] = result['yhat_lower'].clip(lower=0)
        return result, None
    except Exception as e:
        return None, str(e)

def run_xgboost_forecast(df, periods=30):
    try:
        import xgboost as xgb
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        return None, "XGBoost not installed. Run: pip install xgboost"

    if df.empty or len(df) < 10:
        return None, "Need at least 10 data points for XGBoost forecasting."

    try:
        ts = df[['ds', 'y']].copy()
        ts['ds'] = pd.to_datetime(ts['ds'])
        ts = ts.sort_values('ds').reset_index(drop=True)

        # Fill missing dates
        date_range = pd.date_range(ts['ds'].min(), ts['ds'].max(), freq='D')
        ts = ts.set_index('ds').reindex(date_range).fillna(0).reset_index()
        ts.columns = ['ds', 'y']

        def create_features(df_in):
            d = df_in.copy()
            d['dayofweek'] = d['ds'].dt.dayofweek
            d['month'] = d['ds'].dt.month
            d['day'] = d['ds'].dt.day
            d['quarter'] = d['ds'].dt.quarter
            d['dayofyear'] = d['ds'].dt.dayofyear
            d['weekofyear'] = d['ds'].dt.isocalendar().week.astype(int)
            for lag in [1, 2, 3, 7, 14]:
                d[f'lag_{lag}'] = d['y'].shift(lag)
            d['rolling_7'] = d['y'].rolling(7).mean()
            d['rolling_14'] = d['y'].rolling(14).mean()
            return d

        ts_feat = create_features(ts).dropna()
        feat_cols = ['dayofweek', 'month', 'day', 'quarter', 'dayofyear', 'weekofyear',
                     'lag_1', 'lag_2', 'lag_3', 'lag_7', 'lag_14', 'rolling_7', 'rolling_14']

        X = ts_feat[feat_cols]
        y = ts_feat['y']

        model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42,
            verbosity=0
        )
        model.fit(X, y)

        # Iterative forecasting
        last_known = ts.copy()
        forecast_rows = []

        for i in range(periods):
            next_date = last_known['ds'].max() + timedelta(days=1)
            temp = pd.DataFrame({'ds': [next_date], 'y': [np.nan]})
            last_known = pd.concat([last_known, temp], ignore_index=True)
            feat = create_features(last_known)
            if feat.empty or feat.iloc[-1][feat_cols].isnull().any():
                last_known.loc[last_known.index[-1], 'y'] = last_known['y'].dropna().tail(7).mean()
                forecast_rows.append({'ds': next_date, 'yhat': last_known.loc[last_known.index[-1], 'y']})
                continue
            pred = model.predict(feat[feat_cols].iloc[[-1]])[0]
            pred = max(0, pred)
            last_known.loc[last_known.index[-1], 'y'] = pred
            forecast_rows.append({'ds': next_date, 'yhat': pred})

        result = pd.DataFrame(forecast_rows)
        # Add confidence intervals (±20%)
        result['yhat_lower'] = result['yhat'] * 0.80
        result['yhat_upper'] = result['yhat'] * 1.20
        return result, None

    except Exception as e:
        return None, str(e)

def get_forecast(df, model_name="Prophet", periods=30):
    ts = df.copy()
    if 'date' in ts.columns:
        ts = ts.rename(columns={'date': 'ds', 'amount': 'y'})
    if 'ds' not in ts.columns or 'y' not in ts.columns:
        return None, "Invalid data format."

    daily = ts.groupby('ds')['y'].sum().reset_index()

    if model_name == "Prophet":
        return run_prophet_forecast(daily, periods)
    elif model_name == "XGBoost":
        return run_xgboost_forecast(daily, periods)
    else:
        return None, f"Unknown model: {model_name}"