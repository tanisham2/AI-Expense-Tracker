import pandas as pd
import io
from datetime import datetime

def generate_csv_report(df):
    """Generate a comprehensive CSV report"""
    output = io.StringIO()
    df.to_csv(output, index=False)
    return output.getvalue()

def generate_summary_dict(df):
    """Generate summary statistics"""
    if df.empty:
        return {}
    df['date'] = pd.to_datetime(df['date'])
    return {
        'total_expenses': df['amount'].sum(),
        'total_transactions': len(df),
        'avg_transaction': df['amount'].mean(),
        'max_transaction': df['amount'].max(),
        'min_transaction': df['amount'].min(),
        'top_category': df.groupby('category')['amount'].sum().idxmax(),
        'date_range': f"{df['date'].min().date()} to {df['date'].max().date()}"
    }