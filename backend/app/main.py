from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.ws import router as ws_router
from dotenv import load_dotenv
load_dotenv()



app = FastAPI(title="AI Interviewer – Day 1")




app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_router)

@app.get("/")
def health():
    return {"status": "running"}
