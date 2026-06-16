from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.expense import Expense
from backend.schemas.forecast import ForecastRequest, CategoryPredictRequest
from backend.routers.auth import get_current_user
from backend.services.forecast_service import get_forecast
from backend.services.ml_service import predict_category

router = APIRouter(prefix="/forecast", tags=["Forecasting"])

def auth_user(authorization: str = Header(...), db: Session = Depends(get_db)):
    token = authorization.replace("Bearer ", "")
    return get_current_user(token, db)

@router.post("/predict")
def forecast(req: ForecastRequest, db: Session = Depends(get_db), current_user=Depends(auth_user)):
    expenses = db.query(Expense).filter(Expense.user_id == current_user.id).all()
    if not expenses:
        return {"error": "No expense data found"}

    data = [{"date": str(e.date), "amount": e.amount} for e in expenses]
    try:
        result = get_forecast(data, model_name=req.model_name, periods=req.periods)
        return result
    except Exception as e:
        return {"error": str(e)}

@router.post("/categorize")
def categorize_expense(req: CategoryPredictRequest, current_user=Depends(auth_user)):
    """Uses your expense_category_model.pkl from Colab"""
    return predict_category(req.notes)