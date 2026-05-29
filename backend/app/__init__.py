from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import router as scheduling_router
from .api.production_lines import router as lines_router
from .api.delivery_plans import router as plans_router
from .database import init_db

app = FastAPI(
    title="智能排产POC系统",
    description="基于 Google OR-Tools CP-SAT 约束优化的智能生产排产系统",
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scheduling_router)
app.include_router(lines_router)
app.include_router(plans_router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
async def root():
    return {"message": "智能排产POC系统API", "version": "2.1.0"}
