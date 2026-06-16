import requests
import streamlit as st

BASE_URL = "http://localhost:8000"

def get_headers():
    token = st.session_state.get("access_token", "")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def refresh_if_needed():
    """Auto-refresh access token using refresh token"""
    refresh_token = st.session_state.get("refresh_token")
    if not refresh_token:
        return False
    try:
        r = requests.post(f"{BASE_URL}/auth/refresh",
                          json={"refresh_token": refresh_token}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            st.session_state.access_token = data["access_token"]
            st.session_state.refresh_token = data["refresh_token"]
            return True
    except Exception:
        pass
    return False

def api_get(endpoint, params=None):
    try:
        r = requests.get(f"{BASE_URL}{endpoint}", headers=get_headers(), params=params, timeout=15)
        if r.status_code == 401:
            if refresh_if_needed():
                r = requests.get(f"{BASE_URL}{endpoint}", headers=get_headers(), params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend. Make sure FastAPI is running on port 8000.")
        return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def api_post(endpoint, data):
    try:
        r = requests.post(f"{BASE_URL}{endpoint}", headers=get_headers(), json=data, timeout=15)
        if r.status_code == 401:
            if refresh_if_needed():
                r = requests.post(f"{BASE_URL}{endpoint}", headers=get_headers(), json=data, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend.")
        return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def api_put(endpoint, data):
    try:
        r = requests.put(f"{BASE_URL}{endpoint}", headers=get_headers(), json=data, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def api_delete(endpoint):
    try:
        r = requests.delete(f"{BASE_URL}{endpoint}", headers=get_headers(), timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

# ── Auth ──────────────────────────────────────────────
def login(email, password):
    r = requests.post(f"{BASE_URL}/auth/login",
                      json={"email": email, "password": password}, timeout=10)
    return r.json(), r.status_code

def register(name, email, password):
    r = requests.post(f"{BASE_URL}/auth/register",
                      json={"name": name, "email": email, "password": password}, timeout=10)
    return r.json(), r.status_code

# ── Expenses ──────────────────────────────────────────
def get_expenses(start_date=None, end_date=None, category=None, payment_mode=None):
    params = {}
    if start_date: params["start_date"] = str(start_date)
    if end_date: params["end_date"] = str(end_date)
    if category and category != "All": params["category"] = category
    if payment_mode and payment_mode != "All": params["payment_mode"] = payment_mode
    return api_get("/expenses/", params=params) or []

def add_expense(date, category, amount, payment_mode, notes):
    return api_post("/expenses/", {
        "date": str(date), "category": category,
        "amount": amount, "payment_mode": payment_mode, "notes": notes
    })

def update_expense(expense_id, date, category, amount, payment_mode, notes):
    return api_put(f"/expenses/{expense_id}", {
        "date": str(date), "category": category,
        "amount": amount, "payment_mode": payment_mode, "notes": notes
    })

def delete_expense(expense_id):
    return api_delete(f"/expenses/{expense_id}")

# ── Forecast ──────────────────────────────────────────
def get_forecast(model_name="Prophet", periods=30):
    return api_post("/forecast/predict", {"model_name": model_name, "periods": periods})

def predict_category(notes: str):
    return api_post("/forecast/categorize", {"notes": notes})

# ── Analytics ─────────────────────────────────────────
def get_insights():
    return api_get("/analytics/insights")

# ── Budget ────────────────────────────────────────────
def get_budgets(month):
    return api_get(f"/expenses/budgets/{month}") or []

def set_budget(month, category, amount):
    return api_post("/expenses/budgets/", {
        "month": month, "category": category, "budget_amount": amount
    })