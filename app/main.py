from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import orders

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(orders.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Cocktail Order API"} 