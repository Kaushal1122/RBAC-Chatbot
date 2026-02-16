from fastapi import FastAPI
from milestone_3.routes import router as auth_router
from milestone_3.ai_routes import router as ai_router
from milestone_3.init_db import init_db

app = FastAPI(title="Company Chatbot Backend")
@app.on_event("startup")
def startup_event():
    init_db()


app.include_router(auth_router)
app.include_router(ai_router)

@app.get("/")
def root():
    return {"message": "Backend is running"}

@app.get("/health")
def health_check():
    return {"status": "OK"}



#server command : uvicorn milestone_3.main:app --workers 2
#swagger command : http://127.0.0.1:8000/docs