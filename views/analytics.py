import streamlit as st
import pandas as pd
import numpy as np
from database.db_manager import get_expenses
from utils.helpers import format_currency, CATEGORY_COLORS
from utils.charts import (spending_heatmap, category_trend_chart, spending_distribution_chart, monthly_trend_chart)

def show_analytics():
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h1 style="font-size: 26px; font-weight: 700; color: #e6edf3; margin: 0;">📈 Analytics & Insights</h1>
        <p style="color: #8b949e; font-size: 13px; margin: 4px 0 0;">Deep dive into your spending patterns</p>
    </div>
    """, unsafe_allow_html=True)

    user_id = st.session_state.user_id
    df = get_expenses(user_id)

    if df.empty:
        st.info("No data available for analytics. Add some expenses first.")
        return

    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M').astype(str)
    df['weekday'] = df['date'].dt.day_name()
    df['is_weekend'] = df['date'].dt.dayofweek >= 5
    df['week'] = df['date'].dt.isocalendar().week.astype(int)
    
    st.markdown("<div class='section-header'>🔍 Auto-Generated Insights</div>", unsafe_allow_html=True)

    monthly_totals = df.groupby('month')['amount'].sum()
    cat_totals = df.groupby('category')['amount'].sum()
    weekend_avg = df[df['is_weekend']]['amount'].mean()
    weekday_avg = df[~df['is_weekend']]['amount'].mean()

    # Growth rate
    if len(monthly_totals) >= 2:
        last_m = monthly_totals.iloc[-1]
        prev_m = monthly_totals.iloc[-2]
        growth = ((last_m - prev_m) / prev_m * 100) if prev_m > 0 else 0
    else:
        growth = 0

    insights = [
        ("📅", "Highest Spending Month",
         f"{monthly_totals.idxmax()} — {format_currency(monthly_totals.max())}"),
        ("📉", "Lowest Spending Month",
         f"{monthly_totals.idxmin()} — {format_currency(monthly_totals.min())}"),
        ("🏆", "Most Expensive Category",
         f"{cat_totals.idxmax()} — {format_currency(cat_totals.max())}"),
        ("📊", "MoM Growth Rate",
         f"{'📈' if growth > 0 else '📉'} {abs(growth):.1f}% vs previous month"),
        ("🌅", "Weekend vs Weekday",
         f"Weekend avg ₹{weekend_avg:,.0f} vs Weekday avg ₹{weekday_avg:,.0f}"),
        ("💳", "Total Transactions",
         f"{len(df)} transactions · Avg ₹{df['amount'].mean():,.0f}"),
    ]

    cols = st.columns(3)
    for i, (icon, title, value) in enumerate(insights):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-title">{icon} {title}</div>
                <div class="insight-value">{value}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(spending_heatmap(df), use_container_width=True, config={'displayModeBar': False})
    with col2:
        st.plotly_chart(spending_distribution_chart(df), use_container_width=True, config={'displayModeBar': False})

    st.plotly_chart(category_trend_chart(df), use_container_width=True, config={'displayModeBar': False})
    st.plotly_chart(monthly_trend_chart(df), use_container_width=True, config={'displayModeBar': False})

    # Category-wise analysis table
    st.markdown("<div class='section-header'>📊 Category-Wise Analysis</div>", unsafe_allow_html=True)
    cat_analysis = df.groupby('category').agg(
        Total=('amount', 'sum'),
        Count=('amount', 'count'),
        Average=('amount', 'mean'),
        Min=('amount', 'min'),
        Max=('amount', 'max')
    ).round(2).reset_index().sort_values('Total', ascending=False)

    cat_analysis['% of Total'] = (cat_analysis['Total'] / cat_analysis['Total'].sum() * 100).round(1)
    for col in ['Total', 'Average', 'Min', 'Max']:
        cat_analysis[col] = cat_analysis[col].apply(lambda x: f"₹{x:,.0f}")
    cat_analysis['% of Total'] = cat_analysis['% of Total'].apply(lambda x: f"{x}%")

    st.dataframe(cat_analysis, use_container_width=True, height=300)

    # Weekend vs Weekday breakdown
    st.markdown("<div class='section-header'>📅 Weekend vs Weekday Analysis</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    wkd = df[df['is_weekend']]
    wkday = df[~df['is_weekend']]

    metrics = [
        (c1, "🌅 Weekend Total", format_currency(wkd['amount'].sum())),
        (c2, "🗓️ Weekday Total", format_currency(wkday['amount'].sum())),
        (c3, "📊 Weekend Avg/day", format_currency(wkd['amount'].mean())),
        (c4, "📊 Weekday Avg/day", format_currency(wkday['amount'].mean())),
    ]
    for col, label, val in metrics:
        with col:
            st.metric(label, val)