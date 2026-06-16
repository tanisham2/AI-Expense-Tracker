from pydantic import BaseModel
from typing import Optional
from datetime import date

class ExpenseCreate(BaseModel):
    date: date
    category: str
    amount: float
    payment_mode: str = "Cash"
    notes: Optional[str] = ""

class ExpenseUpdate(BaseModel):
    date: Optional[date]
    category: Optional[str]
    amount: Optional[float]
    payment_mode: Optional[str]
    notes: Optional[str]

class ExpenseResponse(BaseModel):
    id: int
    date: date
    category: str
    amount: float
    payment_mode: str
    notes: Optional[str]

    class Config:
        from_attributes = True

class BudgetCreate(BaseModel):
    month: str
    category: str
    budget_amount: float

class BudgetResponse(BaseModel):
    id: int
    month: str
    category: str
    budget_amount: float

    class Config:
        from_attributes = True