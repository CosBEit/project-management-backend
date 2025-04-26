import os
import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv
from server.api.login import router as login_router
from server.api.projects import router as projects_router
from server.api.tasks import router as tasks_router
from server.api.users import router as users_router
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

app.include_router(login_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")

if __name__ == "__main__":
    print("The server runing with database=", os.getenv('server_port'))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv('server_port')),
        reload=True,
    )
