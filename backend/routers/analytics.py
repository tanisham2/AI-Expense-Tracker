from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
import pandas as pd

from backend.database import get_db
from backend.models.expense import Expense
from backend.routers.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])

def auth_user(authorization: str = Header(...), db: Session = Depends(get_db)):
    token = authorization.replace("Bearer ", "")
    return get_current_user(token, db)

@router.get("/insights")
def get_insights(db: Session = Depends(get_db), current_user=Depends(auth_user)):
    expenses = db.query(Expense).filter(Expense.user_id == current_user.id).all()
    if not expenses:
        return {}

    df = pd.DataFrame([{
        "date": e.date, "category": e.category,
        "amount": e.amount, "payment_mode": e.payment_mode
    } for e in expenses])

    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["is_weekend"] = df["date"].dt.dayofweek >= 5

    monthly = df.groupby("month")["amount"].sum()
    cat_totals = df.groupby("category")["amount"].sum()
    weekend_avg = float(df[df["is_weekend"]]["amount"].mean()) if df["is_weekend"].any() else 0
    weekday_avg = float(df[~df["is_weekend"]]["amount"].mean()) if (~df["is_weekend"]).any() else 0

    growth = 0
    if len(monthly) >= 2:
        last, prev = monthly.iloc[-1], monthly.iloc[-2]
        growth = round(((last - prev) / prev * 100), 2) if prev > 0 else 0

    return {
        "highest_month": {"month": monthly.idxmax(), "amount": round(float(monthly.max()), 2)},
        "lowest_month": {"month": monthly.idxmin(), "amount": round(float(monthly.min()), 2)},
        "top_category": {"category": cat_totals.idxmax(), "amount": round(float(cat_totals.max()), 2)},
        "growth_rate": growth,
        "weekend_avg": round(weekend_avg, 2),
        "weekday_avg": round(weekday_avg, 2),
        "total_transactions": len(df),
        "avg_transaction": round(float(df["amount"].mean()), 2),
        "monthly_totals": monthly.reset_index().rename(columns={"amount":"total"}).to_dict(orient="records"),
        "category_totals": cat_totals.reset_index().rename(columns={"amount":"total"}).to_dict(orient="records"),
    }