import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from utils.helpers import CATEGORY_COLORS

CHART_THEME = {
    "bg": "rgba(0,0,0,0)",
    "paper_bg": "rgba(0,0,0,0)",
    "grid": "#21262d",
    "text": "#8b949e",
    "accent": "#388bfd",
    "font_family": "Inter, sans-serif"
}

def apply_dark_theme(fig, height=300, show_legend=True):
    fig.update_layout(
        height=height,
        paper_bgcolor=CHART_THEME["paper_bg"],
        plot_bgcolor=CHART_THEME["bg"],
        font=dict(color=CHART_THEME["text"], family=CHART_THEME["font_family"], size=11),
        margin=dict(l=10, r=10, t=30, b=10),
        showlegend=show_legend,
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor="#21262d",
            font=dict(size=10, color="#8b949e")
        ),
        xaxis=dict(
            gridcolor=CHART_THEME["grid"],
            tickfont=dict(size=10),
            linecolor="#21262d"
        ),
        yaxis=dict(
            gridcolor=CHART_THEME["grid"],
            tickfont=dict(size=10),
            linecolor="#21262d"
        )
    )
    return fig

def daily_trend_chart(df):
    if df.empty:
        return go.Figure()
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    daily = df.groupby('date')['amount'].sum().reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily['date'], y=daily['amount'],
        mode='lines',
        fill='tozeroy',
        fillcolor='rgba(56,139,253,0.1)',
        line=dict(color='#388bfd', width=2),
        name='Daily Spend',
        hovertemplate='₹%{y:,.0f}<extra></extra>'
    ))

    if len(daily) > 7:
        daily['ma7'] = daily['amount'].rolling(7).mean()
        fig.add_trace(go.Scatter(
            x=daily['date'], y=daily['ma7'],
            mode='lines',
            line=dict(color='#f85149', width=1.5, dash='dot'),
            name='7-day MA',
            hovertemplate='₹%{y:,.0f}<extra></extra>'
        ))

    fig.update_layout(title=dict(text="Daily Expense Trend", font=dict(size=13, color="#e6edf3")))
    return apply_dark_theme(fig, height=260)

def monthly_trend_chart(df):
    if df.empty:
        return go.Figure()
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M').astype(str)
    monthly = df.groupby('month')['amount'].sum().reset_index()

    colors = ['#388bfd' if i < len(monthly)-1 else '#3fb950' for i in range(len(monthly))]

    fig = go.Figure(go.Bar(
        x=monthly['month'], y=monthly['amount'],
        marker_color=colors,
        text=[f'₹{v/1000:.1f}K' for v in monthly['amount']],
        textposition='outside',
        textfont=dict(size=9),
        hovertemplate='%{x}<br>₹%{y:,.0f}<extra></extra>'
    ))
    fig.update_layout(title=dict(text="Monthly Expenses", font=dict(size=13, color="#e6edf3")))
    return apply_dark_theme(fig, height=260, show_legend=False)

def category_pie_chart(df):
    if df.empty:
        return go.Figure()
    cat_data = df.groupby('category')['amount'].sum().reset_index().sort_values('amount', ascending=False)
    top = cat_data.head(8)

    colors = [CATEGORY_COLORS.get(c, '#636e72') for c in top['category']]

    fig = go.Figure(go.Pie(
        labels=top['category'],
        values=top['amount'],
        hole=0.55,
        marker=dict(colors=colors, line=dict(color='#0d1117', width=2)),
        textinfo='percent',
        textfont=dict(size=10),
        hovertemplate='%{label}<br>₹%{value:,.0f}<br>%{percent}<extra></extra>'
    ))
    fig.update_layout(
        title=dict(text="Category Breakdown", font=dict(size=13, color="#e6edf3")),
        annotations=[dict(text='Spend', x=0.5, y=0.5, font_size=12, showarrow=False, font_color='#8b949e')]
    )
    return apply_dark_theme(fig, height=280)

def top_categories_bar(df):
    if df.empty:
        return go.Figure()
    cat_data = df.groupby('category')['amount'].sum().reset_index().sort_values('amount', ascending=True).tail(8)
    colors = [CATEGORY_COLORS.get(c, '#636e72') for c in cat_data['category']]

    fig = go.Figure(go.Bar(
        x=cat_data['amount'], y=cat_data['category'],
        orientation='h',
        marker_color=colors,
        text=[f'₹{v/1000:.1f}K' for v in cat_data['amount']],
        textposition='outside',
        textfont=dict(size=9),
        hovertemplate='%{y}<br>₹%{x:,.0f}<extra></extra>'
    ))
    fig.update_layout(title=dict(text="Top Categories", font=dict(size=13, color="#e6edf3")))
    return apply_dark_theme(fig, height=280, show_legend=False)

def weekly_pattern_chart(df):
    if df.empty:
        return go.Figure()
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['weekday'] = df['date'].dt.day_name()
    order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekly = df.groupby('weekday')['amount'].mean().reindex(order).reset_index()

    colors = ['#f85149' if d in ['Saturday', 'Sunday'] else '#388bfd' for d in weekly['weekday']]

    fig = go.Figure(go.Bar(
        x=[d[:3] for d in weekly['weekday']],
        y=weekly['amount'],
        marker_color=colors,
        text=[f'₹{v/1000:.1f}K' if not pd.isna(v) else '' for v in weekly['amount']],
        textposition='outside',
        textfont=dict(size=9),
        hovertemplate='%{x}<br>₹%{y:,.0f}<extra></extra>'
    ))
    fig.update_layout(title=dict(text="Avg Spending by Day", font=dict(size=13, color="#e6edf3")))
    return apply_dark_theme(fig, height=240, show_legend=False)

def forecast_chart(historical_df, forecast_df, model_name="Prophet"):
    fig = go.Figure()

    if not historical_df.empty:
        fig.add_trace(go.Scatter(
            x=historical_df['ds'], y=historical_df['y'],
            mode='lines',
            line=dict(color='#58a6ff', width=1.5),
            name='Historical',
            hovertemplate='%{x|%b %d}<br>₹%{y:,.0f}<extra></extra>'
        ))

    if not forecast_df.empty:
        if 'yhat_lower' in forecast_df.columns and 'yhat_upper' in forecast_df.columns:
            fig.add_trace(go.Scatter(
                x=pd.concat([forecast_df['ds'], forecast_df['ds'][::-1]]),
                y=pd.concat([forecast_df['yhat_upper'], forecast_df['yhat_lower'][::-1]]),
                fill='toself',
                fillcolor='rgba(63,185,80,0.1)',
                line=dict(color='rgba(0,0,0,0)'),
                name='Confidence Interval',
                hoverinfo='skip'
            ))

        fig.add_trace(go.Scatter(
            x=forecast_df['ds'], y=forecast_df['yhat'],
            mode='lines+markers',
            line=dict(color='#3fb950', width=2, dash='dash'),
            marker=dict(size=5),
            name=f'{model_name} Forecast',
            hovertemplate='%{x|%b %d}<br>₹%{y:,.0f}<extra></extra>'
        ))

    fig.update_layout(title=dict(text=f"Expense Forecast — {model_name}", font=dict(size=13, color="#e6edf3")))
    return apply_dark_theme(fig, height=350)

def spending_heatmap(df):
    if df.empty:
        return go.Figure()
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['week'] = df['date'].dt.isocalendar().week.astype(int)
    df['weekday'] = df['date'].dt.dayofweek
    pivot = df.groupby(['week', 'weekday'])['amount'].sum().unstack(fill_value=0)
    pivot = pivot.reindex(columns=range(7), fill_value=0)

    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=days,
        y=[f"W{w}" for w in pivot.index],
        colorscale=[[0, '#0d1117'], [0.5, '#388bfd'], [1, '#f85149']],
        hovertemplate='%{x}<br>Week %{y}<br>₹%{z:,.0f}<extra></extra>',
        showscale=True
    ))
    fig.update_layout(title=dict(text="Spending Heatmap", font=dict(size=13, color="#e6edf3")))
    return apply_dark_theme(fig, height=280)

def category_trend_chart(df):
    if df.empty:
        return go.Figure()
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M').astype(str)
    top_cats = df.groupby('category')['amount'].sum().nlargest(5).index.tolist()

    fig = go.Figure()
    for cat in top_cats:
        cat_monthly = df[df['category'] == cat].groupby('month')['amount'].sum().reset_index()
        fig.add_trace(go.Scatter(
            x=cat_monthly['month'], y=cat_monthly['amount'],
            mode='lines+markers',
            name=cat,
            line=dict(color=CATEGORY_COLORS.get(cat, '#636e72'), width=2),
            marker=dict(size=4),
            hovertemplate=f'{cat}<br>%{{x}}<br>₹%{{y:,.0f}}<extra></extra>'
        ))

    fig.update_layout(title=dict(text="Category Trends Over Time", font=dict(size=13, color="#e6edf3")))
    return apply_dark_theme(fig, height=300)

def spending_distribution_chart(df):
    if df.empty:
        return go.Figure()

    fig = go.Figure(go.Histogram(
        x=df['amount'],
        nbinsx=30,
        marker_color='#388bfd',
        opacity=0.8,
        hovertemplate='₹%{x:,.0f}<br>Count: %{y}<extra></extra>'
    ))
    fig.update_layout(title=dict(text="Spending Distribution", font=dict(size=13, color="#e6edf3")))
    return apply_dark_theme(fig, height=260, show_legend=False)