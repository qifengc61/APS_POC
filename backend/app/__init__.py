from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .api import router
from .core.database import engine, Base
import time
import logging
import os
from logging.handlers import RotatingFileHandler

os.makedirs("logs", exist_ok=True)

file_handler = RotatingFileHandler(
    "logs/aps.log",
    maxBytes=5 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8",
)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)-7s | %(name)-15s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
))

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

logger = logging.getLogger("aps")

app = FastAPI(
    title="智能排产POC系统",
    description="基于 Google OR-Tools CP-SAT 约束优化的智能生产排产系统",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = (time.time() - start_time) * 1000
    status_code = response.status_code
    level = logging.WARNING if status_code >= 400 else logging.INFO
    logger.log(
        level,
        f"{request.method:6s} {status_code} {duration:7.1f}ms {request.url.path}{'?' + str(request.url.query) if request.url.query else ''}",
    )
    return response

app.include_router(router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表已就绪")


@app.get("/")
async def root():
    return {"message": "智能排产POC系统API", "version": "1.0.0"}
