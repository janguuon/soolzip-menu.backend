from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
from datetime import datetime

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# 전역 주문 데이터
orders_data: Dict[str, dict] = {}

@app.get("/")
async def root():
    return {"message": "Cocktail Order API"}

@app.get("/api/orders")
async def get_orders():
    # 현재 저장된 주문 데이터 출력
    print("\n=== 프론트엔드 어드민 요청 ===")
    print("요청 시간:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("현재 저장된 주문 목록:")
    for order in orders_data.values():
        print(f"- ID: {order['id']}")
        print(f"  주문자: {order.get('customerName', '미입력')}")
        print(f"  이름: {order['name']}")
        print(f"  가격: {order['price']}")
        print(f"  수량: {order['quantity']}")
        print(f"  주문시간: {order['created_at']}")
    print("=========================\n")
    
    return list(orders_data.values())

@app.post("/api/orders/place")
async def create_order(request: Request):
    try:
        # 쿠키에서 주문 데이터 가져오기
        order_data = await request.json()
        
        # 쿠키 데이터 출력
        print("\n=== 새로운 주문 생성 ===")
        print("요청 시간:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # 여러 주문 처리
        created_orders = []
        for order in order_data:
            # 주문 ID 생성
            order_id = str(len(orders_data) + 1)
            
            # 현재 시간 추가
            current_time = datetime.now().isoformat()
            
            # 주문 데이터 구성
            new_order = {
                "id": order_id,
                "name": order.get("name", ""),
                "price": order.get("price", 0),
                "quantity": order.get("quantity", 1),
                "created_at": current_time,
                "customerName": order.get("customerName", "미입력")
            }
            
            # 주문 데이터 저장
            orders_data[order_id] = new_order
            created_orders.append(new_order)
            
            # 주문 데이터 출력
            print(f"\n주문 {order_id}:")
            print(f"- 주문자: {new_order['customerName']}")
            print(f"- 이름: {new_order['name']}")
            print(f"- 가격: {new_order['price']}")
            print(f"- 수량: {new_order['quantity']}")
            print(f"- 주문시간: {new_order['created_at']}")
        
        print("\n=====================\n")
        return created_orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/orders/{order_id}")
async def delete_order(order_id: str):
    try:
        if order_id in orders_data:
            del orders_data[order_id]
            return {"message": f"주문 {order_id}가 삭제되었습니다."}
        else:
            raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 