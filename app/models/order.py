from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class OrderItem(BaseModel):
    cocktail_id: str
    quantity: int
    price: float

class Order(BaseModel):
    id: str
    customer_name: str
    items: List[OrderItem]
    total_price: float
    status: str = "pending"  # pending, preparing, completed, cancelled
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now() 