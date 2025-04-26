import os
import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv
from server.api import login
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(title="Coseb Project Management")

# More explicit CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600
)

app.include_router(login.router, prefix="/api/v1")

if __name__ == "__main__":
    print("The server runing with database=",os.getenv('server_port'))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv('server_port')),
        reload=True,
    )