from pydantic import BaseModel
from typing import Optional

class ForecastRequest(BaseModel):
    model_name: str = "Prophet"   # "Prophet" or "XGBoost"
    periods: int = 30             # 7, 30, 90

class CategoryPredictRequest(BaseModel):
    notes: str

class CategoryPredictResponse(BaseModel):
    predicted_category: str
    confidence: Optional[float] = None