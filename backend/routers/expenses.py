from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date
import pandas as pd

from backend.database import get_db
from backend.models.expense import Expense, Budget
from backend.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse, BudgetCreate
from backend.routers.auth import get_current_user

router = APIRouter(prefix="/expenses", tags=["Expenses"])

def auth_user(authorization: str = Header(...), db: Session = Depends(get_db)):
    token = authorization.replace("Bearer ", "")
    return get_current_user(token, db)

@router.get("/", response_model=List[ExpenseResponse])
def get_expenses(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category: Optional[str] = None,
    payment_mode: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(auth_user)
):
    query = db.query(Expense).filter(Expense.user_id == current_user.id)
    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)
    if category and category != "All":
        query = query.filter(Expense.category == category)
    if payment_mode and payment_mode != "All":
        query = query.filter(Expense.payment_mode == payment_mode)
    return query.order_by(Expense.date.desc()).all()

@router.post("/", status_code=201)
def add_expense(req: ExpenseCreate, db: Session = Depends(get_db), current_user=Depends(auth_user)):
    expense = Expense(user_id=current_user.id, **req.dict())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return {"id": expense.id, "message": "Expense added"}

@router.put("/{expense_id}")
def update_expense(expense_id: int, req: ExpenseUpdate, db: Session = Depends(get_db),
                   current_user=Depends(auth_user)):
    expense = db.query(Expense).filter(
        Expense.id == expense_id, Expense.user_id == current_user.id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    for field, val in req.dict(exclude_none=True).items():
        setattr(expense, field, val)
    db.commit()
    return {"message": "Updated"}

@router.delete("/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db), current_user=Depends(auth_user)):
    expense = db.query(Expense).filter(
        Expense.id == expense_id, Expense.user_id == current_user.id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(expense)
    db.commit()
    return {"message": "Deleted"}

@router.get("/summary/categories")
def category_summary(db: Session = Depends(get_db), current_user=Depends(auth_user)):
    expenses = db.query(Expense).filter(Expense.user_id == current_user.id).all()
    if not expenses:
        return []
    df = pd.DataFrame([{"category": e.category, "amount": e.amount} for e in expenses])
    summary = df.groupby("category")["amount"].agg(["sum","count","mean"]).reset_index()
    return summary.to_dict(orient="records")

# Budget endpoints
@router.post("/budgets/")
def set_budget(req: BudgetCreate, db: Session = Depends(get_db), current_user=Depends(auth_user)):
    existing = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.month == req.month,
        Budget.category == req.category
    ).first()
    if existing:
        existing.budget_amount = req.budget_amount
    else:
        budget = Budget(user_id=current_user.id, **req.dict())
        db.add(budget)
    db.commit()
    return {"message": "Budget set"}

@router.get("/budgets/{month}")
def get_budgets(month: str, db: Session = Depends(get_db), current_user=Depends(auth_user)):
    budgets = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.month == month
    ).all()
    return [{"id": b.id, "category": b.category, "budget_amount": b.budget_amount} for b in budgets]