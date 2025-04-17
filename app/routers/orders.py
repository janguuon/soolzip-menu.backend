from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from ..database import get_db
from ..schemas.order import Order, OrderCreate, OrderItemCreate
from ..database import Order as OrderModel, OrderItem as OrderItemModel
import json
import logging
import httpx

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

async def notify_admin(orders: List[Dict]):
    """frontend-admin으로 주문 데이터를 전송하는 함수"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:3001/api/orders/update",
                json={"orders": orders},
                headers={"Content-Type": "application/json"}
            )
            if response.status_code != 200:
                logger.error(f"관리자 페이지 업데이트 실패: {response.text}")
    except Exception as e:
        logger.error(f"관리자 페이지 알림 중 오류 발생: {str(e)}")

@router.post("/orders/", response_model=Order)
async def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    db_order = OrderModel(
        customer_name=order.customer_name,
        total_price=order.total_price,
        status=order.status
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    for item in order.items:
        db_item = OrderItemModel(
            order_id=db_order.id,
            cocktail_id=item.cocktail_id,
            quantity=item.quantity,
            price=item.price
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_order)
    return db_order

@router.get("/orders/", response_model=List[Order])
async def get_orders(db: Session = Depends(get_db)):
    orders = db.query(OrderModel).all()
    return orders

@router.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.put("/orders/{order_id}/status")
async def update_order_status(order_id: int, status: str, db: Session = Depends(get_db)):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = status
    db.commit()
    return {"message": "Order status updated successfully"}

@router.get("/orders")
async def get_orders_cookie(orders_cookie: Optional[str] = Cookie(None)):
    try:
        if not orders_cookie:
            logger.info("주문이 없습니다.")
            return []
            
        orders = json.loads(orders_cookie)
        logger.info(f"주문 조회: 총 {len(orders)}개의 주문")
        return orders
    except Exception as e:
        logger.error(f"주문 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/orders/add")
async def add_order(
    order_data: dict,
    response: Response,
    orders_cookie: Optional[str] = Cookie(None)
):
    try:
        logger.info(f"새로운 주문 추가 요청: {order_data}")
        
        # 기존 주문 데이터 가져오기
        orders = []
        if orders_cookie:
            orders = json.loads(orders_cookie)
            logger.info(f"기존 주문 수: {len(orders)}")
        
        # 새로운 주문 추가
        new_order = {
            "id": order_data["id"],
            "name": order_data["name"],
            "price": order_data["price"],
            "quantity": 1
        }
        
        # 이미 있는 주문인지 확인
        existing_order = next(
            (order for order in orders if order["id"] == new_order["id"]), 
            None
        )
        
        if existing_order:
            existing_order["quantity"] += 1
            logger.info(f"기존 주문 수량 증가: {existing_order['name']} - {existing_order['quantity']}개")
        else:
            orders.append(new_order)
            logger.info(f"새 주문 추가: {new_order['name']}")
        
        # 쿠키에 주문 데이터 저장
        response.set_cookie(
            key="orders",
            value=json.dumps(orders),
            max_age=3600,
            httponly=True,
            secure=True,
            samesite="lax"
        )
        
        # frontend-admin으로 주문 데이터 전송
        await notify_admin(orders)
        
        logger.info(f"현재 총 주문 수: {len(orders)}")
        return {"message": "주문이 추가되었습니다."}
    except Exception as e:
        logger.error(f"주문 추가 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/orders/{order_id}")
async def remove_order(
    order_id: str,
    response: Response,
    orders_cookie: Optional[str] = Cookie(None)
):
    try:
        if not orders_cookie:
            logger.warning("삭제할 주문이 없습니다.")
            raise HTTPException(status_code=404, detail="주문이 없습니다.")
        
        orders = json.loads(orders_cookie)
        before_count = len(orders)
        orders = [order for order in orders if order["id"] != order_id]
        after_count = len(orders)
        
        if before_count == after_count:
            logger.warning(f"주문 ID {order_id}를 찾을 수 없습니다.")
        else:
            logger.info(f"주문 ID {order_id} 삭제 완료")
        
        response.set_cookie(
            key="orders",
            value=json.dumps(orders),
            max_age=3600,
            httponly=True,
            secure=True,
            samesite="lax"
        )
        
        # frontend-admin으로 업데이트된 주문 데이터 전송
        await notify_admin(orders)
        
        return {"message": "주문이 삭제되었습니다."}
    except Exception as e:
        logger.error(f"주문 삭제 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/orders/place")
async def place_order(
    order_data: dict,
    response: Response,
    orders_cookie: Optional[str] = Cookie(None)
):
    try:
        if not order_data.get("orders"):
            raise HTTPException(status_code=400, detail="주문 데이터가 없습니다.")
            
        logger.info("새로운 주문 요청 받음")
        logger.info(f"주문 데이터: {order_data}")
        
        # 주문 데이터를 쿠키에 저장
        response.set_cookie(
            key="placed_orders",
            value=json.dumps(order_data["orders"]),
            max_age=3600,
            httponly=True,
            secure=True,
            samesite="lax"
        )
        
        # 기존 장바구니 비우기
        response.set_cookie(
            key="orders",
            value=json.dumps([]),
            max_age=3600,
            httponly=True,
            secure=True,
            samesite="lax"
        )
        
        # frontend-admin으로 빈 주문 데이터 전송
        await notify_admin([])
        
        logger.info("주문이 성공적으로 처리되었습니다.")
        return {"message": "주문이 성공적으로 처리되었습니다."}
    except Exception as e:
        logger.error(f"주문 처리 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/orders")
async def add_order(order: Dict, response: Response):
    try:
        # 기존 주문 데이터 가져오기
        orders_cookie = response.cookies.get("orders")
        orders = json.loads(orders_cookie) if orders_cookie else []
        
        # 새 주문 추가
        orders.append(order)
        
        # 쿠키에 주문 데이터 저장
        response.set_cookie(
            key="orders",
            value=json.dumps(orders),
            httponly=True,
            samesite="lax"
        )
        
        return {"message": "주문이 추가되었습니다."}
    except Exception as e:
        print(f"Error adding order: {e}")
        raise HTTPException(status_code=500, detail="주문 추가에 실패했습니다.")

@router.delete("/orders/{order_id}")
async def delete_order(order_id: str, response: Response):
    try:
        # 기존 주문 데이터 가져오기
        orders_cookie = response.cookies.get("orders")
        if not orders_cookie:
            raise HTTPException(status_code=404, detail="주문이 없습니다.")
        
        orders = json.loads(orders_cookie)
        
        # 주문 삭제
        orders = [order for order in orders if order["id"] != order_id]
        
        # 쿠키에 업데이트된 주문 데이터 저장
        response.set_cookie(
            key="orders",
            value=json.dumps(orders),
            httponly=True,
            samesite="lax"
        )
        
        return {"message": "주문이 삭제되었습니다."}
    except Exception as e:
        print(f"Error deleting order: {e}")
        raise HTTPException(status_code=500, detail="주문 삭제에 실패했습니다.") 