from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mvp_main_v3 import app as backend_app

app = FastAPI(title="AI Industry Report Gateway", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/", backend_app)
