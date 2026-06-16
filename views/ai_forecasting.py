import streamlit as st
import pandas as pd
from database.db_manager import get_expenses, save_forecast
from models.forecasting_models import get_forecast
from utils.helpers import format_currency, prepare_time_series
from utils.charts import forecast_chart

def show_ai_forecasting():
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h1 style="font-size: 26px; font-weight: 700; color: #e6edf3; margin: 0;">🤖 AI Forecasting</h1>
        <p style="color: #8b949e; font-size: 13px; margin: 4px 0 0;">Predict your future expenses with machine learning</p>
    </div>
    """, unsafe_allow_html=True)

    user_id = st.session_state.user_id
    df = get_expenses(user_id)

    if df.empty or len(df) < 10:
        st.markdown("""
        <div class="alert-card">
            <div style="color: #e6edf3; font-weight: 600;">⚠️ Insufficient Data</div>
            <div style="color: #8b949e; font-size: 13px; margin-top: 4px;">
                You need at least 10 expense records for AI forecasting. Add more expenses first.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        model_choice = st.selectbox(
            "🧠 Forecast Model",
            ["Prophet", "XGBoost"],
            help="Prophet: best for seasonal data. XGBoost: great for patterns."
        )
    with col2:
        period_choice = st.selectbox(
            "📅 Forecast Period",
            ["7 Days", "30 Days", "90 Days"]
        )
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        run_btn = st.button("🚀 Run Forecast", use_container_width=True)

    period_map = {"7 Days": 7, "30 Days": 30, "90 Days": 90}
    periods = period_map[period_choice]

    if run_btn:
        ts = prepare_time_series(df)

        with st.spinner(f"Running {model_choice} forecast for {periods} days..."):
            forecast_df, error = get_forecast(ts, model_name=model_choice, periods=periods)

        if error:
            st.error(f"Forecasting error: {error}")
            return

        if forecast_df is None or forecast_df.empty:
            st.error("Could not generate forecast. Try with more data.")
            return

        # Save to history
        save_forecast(user_id, model_choice, periods, forecast_df['yhat'].sum())

        # Summary KPIs
        total_pred = forecast_df['yhat'].sum()
        avg_daily_pred = forecast_df['yhat'].mean()
        peak_day = forecast_df.loc[forecast_df['yhat'].idxmax()]
        low_day = forecast_df.loc[forecast_df['yhat'].idxmin()]

        st.markdown("<div class='section-header'>Forecast Summary</div>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        kpis = [
            (c1, "💰", "Total Predicted", format_currency(total_pred)),
            (c2, "📊", "Avg Daily", format_currency(avg_daily_pred)),
            (c3, "📈", "Peak Day", f"₹{peak_day['yhat']:,.0f}"),
            (c4, "📉", "Lowest Day", f"₹{low_day['yhat']:,.0f}"),
        ]
        for col, icon, label, val in kpis:
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-icon">{icon}</div>
                    <div class="metric-value">{val}</div>
                    <div class="metric-label">{label}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Chart
        hist_ts = prepare_time_series(df).tail(60)
        hist_ts.columns = ['ds', 'y']
        hist_ts['ds'] = pd.to_datetime(hist_ts['ds'])
        forecast_df['ds'] = pd.to_datetime(forecast_df['ds'])

        st.plotly_chart(forecast_chart(hist_ts, forecast_df, model_choice),
                        use_container_width=True, config={'displayModeBar': False})

        # Forecast Table
        st.markdown("<div class='section-header'>Detailed Forecast</div>", unsafe_allow_html=True)
        display = forecast_df.copy()
        display['ds'] = pd.to_datetime(display['ds']).dt.strftime('%Y-%m-%d')
        display['Day'] = pd.to_datetime(forecast_df['ds']).dt.day_name()
        display['yhat'] = display['yhat'].apply(lambda x: f"₹{x:,.0f}")
        if 'yhat_lower' in display.columns:
            display['yhat_lower'] = display['yhat_lower'].apply(lambda x: f"₹{x:,.0f}")
            display['yhat_upper'] = display['yhat_upper'].apply(lambda x: f"₹{x:,.0f}")
            display.columns = ['Date', 'Predicted', 'Lower Bound', 'Upper Bound', 'Day']
            display = display[['Date', 'Day', 'Predicted', 'Lower Bound', 'Upper Bound']]
        else:
            display.columns = ['Date', 'Predicted', 'Day']
            display = display[['Date', 'Day', 'Predicted']]

        st.dataframe(display, use_container_width=True, height=300)

        # Trend insights
        if len(forecast_df) > 7:
            first_week = forecast_df['yhat'].head(7).mean()
            last_week = forecast_df['yhat'].tail(7).mean()
            trend_pct = ((last_week - first_week) / first_week * 100) if first_week > 0 else 0

            trend_class = "alert-card" if trend_pct > 10 else "success-card"
            trend_icon = "📈" if trend_pct > 0 else "📉"
            st.markdown(f"""
            <div class="{trend_class}" style="margin-top: 16px;">
                <div style="color: #e6edf3; font-weight: 600;">{trend_icon} Spending Trend</div>
                <div style="color: #8b949e; font-size: 13px; margin-top: 4px;">
                    Based on {model_choice} model, your spending is predicted to
                    {'increase' if trend_pct > 0 else 'decrease'} by <strong>{abs(trend_pct):.1f}%</strong>
                    over the forecast period.
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center; padding: 60px 20px; color: #8b949e;">
            <div style="font-size: 56px; margin-bottom: 16px;">🔮</div>
            <div style="font-size: 18px; font-weight: 600; color: #e6edf3;">AI-Powered Expense Prediction</div>
            <div style="font-size: 13px; margin-top: 8px;">
                Select a model and forecast period, then click <strong>Run Forecast</strong> to predict your future expenses.
            </div>
        </div>
        """, unsafe_allow_html=True)