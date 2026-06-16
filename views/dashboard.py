import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database.db_manager import get_expenses
from utils.helpers import format_currency, CATEGORIES, PAYMENT_MODES
from utils.charts import (daily_trend_chart, monthly_trend_chart,
                          category_pie_chart, top_categories_bar, weekly_pattern_chart)

def show_dashboard():
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h1 style="font-size: 26px; font-weight: 700; color: #e6edf3; margin: 0;">📊 Dashboard</h1>
        <p style="color: #8b949e; font-size: 13px; margin: 4px 0 0;">Your financial overview at a glance</p>
    </div>
    """, unsafe_allow_html=True)

    user_id = st.session_state.user_id

    # Filters
    with st.expander("🔍 Filters", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            date_range = st.date_input("Date Range", value=(start_date, end_date))
        with col2:
            sel_category = st.selectbox("Category", ["All"] + CATEGORIES)
        with col3:
            sel_payment = st.selectbox("Payment Method", ["All"] + PAYMENT_MODES)

    try:
        sd = date_range[0] if len(date_range) > 0 else start_date
        ed = date_range[1] if len(date_range) > 1 else end_date
    except Exception:
        sd, ed = start_date, end_date

    df = get_expenses(user_id, start_date=sd, end_date=ed,
                      category=sel_category, payment_mode=sel_payment)

    # Load all data for monthly comparison
    df_all = get_expenses(user_id)

    if df.empty:
        st.markdown("""
        <div style="text-align:center; padding: 60px 20px; color: #8b949e;">
            <div style="font-size: 48px; margin-bottom: 16px;">📭</div>
            <div style="font-size: 18px; font-weight: 600; color: #e6edf3;">No expenses found</div>
            <div style="font-size: 13px; margin-top: 8px;">Add your first expense in the Expense Manager to get started.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # KPI Calculations
    total_expense = df['amount'].sum()
    n_days = max((pd.to_datetime(ed) - pd.to_datetime(sd)).days, 1)
    avg_daily = total_expense / n_days
    n_transactions = len(df)
    top_category = df.groupby('category')['amount'].sum().idxmax() if not df.empty else "N/A"

    # Month comparison
    this_month = datetime.now().replace(day=1)
    last_month_start = (this_month - timedelta(days=1)).replace(day=1)
    df_this = df_all[pd.to_datetime(df_all['date']) >= pd.to_datetime(this_month)]
    df_last = df_all[
        (pd.to_datetime(df_all['date']) >= pd.to_datetime(last_month_start)) &
        (pd.to_datetime(df_all['date']) < pd.to_datetime(this_month))
    ]
    this_total = df_this['amount'].sum()
    last_total = df_last['amount'].sum()
    mom_change = ((this_total - last_total) / last_total * 100) if last_total > 0 else 0

    # KPI Cards
    c1, c2, c3, c4, c5 = st.columns(5)

    kpis = [
        (c1, "💸", "Total Expenses", format_currency(total_expense),
         f"{'↑' if mom_change > 0 else '↓'} {abs(mom_change):.1f}% vs last month",
         "negative" if mom_change > 0 else "positive"),
        (c2, "📅", "Monthly Expenses", format_currency(this_total),
         f"₹{last_total/1000:.1f}K last month", "neutral"),
        (c3, "📈", "Avg Daily Spend", format_currency(avg_daily),
         f"Over {n_days} days", "neutral"),
        (c4, "🏆", "Top Category", top_category,
         f"₹{df.groupby('category')['amount'].sum().max():,.0f}", "neutral"),
        (c5, "🔢", "Transactions", str(n_transactions),
         f"Avg ₹{total_expense/max(n_transactions,1):,.0f} each", "neutral"),
    ]

    for col, icon, label, value, delta, delta_type in kpis:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">{icon}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
                <div class="metric-delta {delta_type}">{delta}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts Row 1
    col1, col2 = st.columns([3, 2])
    with col1:
        st.plotly_chart(daily_trend_chart(df), use_container_width=True, config={'displayModeBar': False})
    with col2:
        st.plotly_chart(category_pie_chart(df), use_container_width=True, config={'displayModeBar': False})

    # Charts Row 2
    col1, col2 = st.columns([2, 3])
    with col1:
        st.plotly_chart(weekly_pattern_chart(df), use_container_width=True, config={'displayModeBar': False})
    with col2:
        st.plotly_chart(monthly_trend_chart(df_all), use_container_width=True, config={'displayModeBar': False})

    # Charts Row 3
    st.plotly_chart(top_categories_bar(df), use_container_width=True, config={'displayModeBar': False})