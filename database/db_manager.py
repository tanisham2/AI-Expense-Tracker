import sqlite3
import os
import hashlib
import pandas as pd
from datetime import datetime

DB_PATH = "fintrack.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            currency TEXT DEFAULT 'INR',
            theme TEXT DEFAULT 'dark',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date DATE NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            payment_mode TEXT DEFAULT 'Cash',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            category TEXT NOT NULL,
            budget_amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, month, category),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS forecast_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            forecast_date DATE NOT NULL,
            model_used TEXT NOT NULL,
            forecast_period INTEGER NOT NULL,
            total_predicted REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(name, email, password):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, hash_password(password))
        )
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        return True, user_id
    except sqlite3.IntegrityError:
        return False, None

def authenticate_user(email, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT * FROM users WHERE email = ? AND password_hash = ?",
        (email, hash_password(password))
    )
    user = c.fetchone()
    conn.close()
    if user:
        return dict(user)
    return None

def get_user_by_id(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None

def update_user_password(user_id, new_password):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (hash_password(new_password), user_id)
    )
    conn.commit()
    conn.close()

def add_expense(user_id, date, category, amount, payment_mode, notes=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO expenses (user_id, date, category, amount, payment_mode, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, date, category, amount, payment_mode, notes)
    )
    conn.commit()
    expense_id = c.lastrowid
    conn.close()
    return expense_id

def get_expenses(user_id, start_date=None, end_date=None, category=None, payment_mode=None):
    conn = get_connection()
    query = "SELECT * FROM expenses WHERE user_id = ?"
    params = [user_id]

    if start_date:
        query += " AND date >= ?"
        params.append(str(start_date))
    if end_date:
        query += " AND date <= ?"
        params.append(str(end_date))
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
    if payment_mode and payment_mode != "All":
        query += " AND payment_mode = ?"
        params.append(payment_mode)

    query += " ORDER BY date DESC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def update_expense(expense_id, date, category, amount, payment_mode, notes):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE expenses SET date=?, category=?, amount=?, payment_mode=?, notes=? WHERE id=?",
        (date, category, amount, payment_mode, notes, expense_id)
    )
    conn.commit()
    conn.close()

def delete_expense(expense_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()

def get_budget(user_id, month):
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM budgets WHERE user_id = ? AND month = ?",
        conn, params=[user_id, month]
    )
    conn.close()
    return df

def set_budget(user_id, month, category, amount):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO budgets (user_id, month, category, budget_amount)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, month, category) DO UPDATE SET budget_amount = excluded.budget_amount
    """, (user_id, month, category, amount))
    conn.commit()
    conn.close()

def save_forecast(user_id, model_used, forecast_period, total_predicted):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO forecast_history (user_id, forecast_date, model_used, forecast_period, total_predicted) VALUES (?, ?, ?, ?, ?)",
        (user_id, datetime.now().date(), model_used, forecast_period, total_predicted)
    )
    conn.commit()
    conn.close()

def import_csv_expenses(user_id, df):
    conn = get_connection()
    c = conn.cursor()
    count = 0
    for _, row in df.iterrows():
        try:
            date = pd.to_datetime(row.get('Date', row.get('date', datetime.now()))).date()
            category = str(row.get('Category', row.get('category', 'Other')))
            amount = float(row.get('Amount', row.get('amount', 0)))
            payment_mode = str(row.get('Payment_Mode', row.get('payment_mode', 'Cash')))
            notes = str(row.get('Notes', row.get('notes', '')))
            c.execute(
                "INSERT INTO expenses (user_id, date, category, amount, payment_mode, notes) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, date, category, amount, payment_mode, notes)
            )
            count += 1
        except Exception:
            continue
    conn.commit()
    conn.close()
    return count