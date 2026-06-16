import pandas as pd
import numpy as np
from datetime import datetime, timedelta

CATEGORIES = [
    "Food & Dining", "Transportation", "Shopping", "Entertainment",
    "Healthcare", "Utilities", "Rent/Housing", "Education",
    "Travel", "Personal Care", "Groceries", "Insurance",
    "Investments", "Subscriptions", "Gifts", "Other"
]

PAYMENT_MODES = ["Cash", "Credit Card", "Debit Card", "UPI", "Net Banking", "Wallet", "EMI"]

CATEGORY_COLORS = {
    "Food & Dining": "#ff6b6b",
    "Transportation": "#4ecdc4",
    "Shopping": "#45b7d1",
    "Entertainment": "#f9ca24",
    "Healthcare": "#6c5ce7",
    "Utilities": "#a29bfe",
    "Rent/Housing": "#fd79a8",
    "Education": "#00b894",
    "Travel": "#e17055",
    "Personal Care": "#fdcb6e",
    "Groceries": "#55efc4",
    "Insurance": "#74b9ff",
    "Investments": "#0984e3",
    "Subscriptions": "#b2bec3",
    "Gifts": "#e84393",
    "Other": "#636e72"
}

def format_currency(amount, currency="₹"):
    if amount >= 1_00_000:
        return f"{currency}{amount/1_00_000:.1f}L"
    elif amount >= 1000:
        return f"{currency}{amount/1000:.1f}K"
    return f"{currency}{amount:,.0f}"

def get_date_range_df(df, start_date=None, end_date=None):
    if df.empty:
        return df
    df['date'] = pd.to_datetime(df['date'])
    if start_date:
        df = df[df['date'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['date'] <= pd.to_datetime(end_date)]
    return df

def prepare_time_series(df):
    if df.empty:
        return pd.DataFrame()
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    daily = df.groupby('date')['amount'].sum().reset_index()
    daily.columns = ['ds', 'y']
    daily = daily.sort_values('ds')
    return daily

def get_color_for_value(value, max_value, reverse=False):
    ratio = value / max_value if max_value > 0 else 0
    if reverse:
        ratio = 1 - ratio
    if ratio < 0.5:
        return "#3fb950"
    elif ratio < 0.8:
        return "#e3b341"
    else:
        return "#f85149"

def generate_sample_data(user_id, days=180):
    """Generate sample expense data for demo purposes"""
    from database.db_manager import add_expense
    import random

    categories = list(CATEGORY_COLORS.keys())
    payment_modes = PAYMENT_MODES

    start_date = datetime.now() - timedelta(days=days)
    data = []

    for i in range(days):
        date = start_date + timedelta(days=i)
        n_transactions = random.randint(1, 5)
        for _ in range(n_transactions):
            cat = random.choice(categories)
            if cat in ["Rent/Housing"]:
                if date.day == 1:
                    amount = random.uniform(8000, 25000)
                else:
                    continue
            elif cat in ["Utilities", "Insurance"]:
                amount = random.uniform(500, 3000)
            elif cat in ["Food & Dining", "Groceries"]:
                amount = random.uniform(100, 2000)
            else:
                amount = random.uniform(200, 5000)

            data.append({
                'user_id': user_id,
                'date': date.date(),
                'category': cat,
                'amount': round(amount, 2),
                'payment_mode': random.choice(payment_modes),
                'notes': f"Sample {cat} expense"
            })

    return data