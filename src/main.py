import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler

import uvicorn
from fastapi import FastAPI, APIRouter

from utils import Config
from handlers import v1_router
from rooms_handlers import room_router
from middlewares import WrapRequestMiddleware

conf = Config()

#  setup logger
logger = logging.getLogger("main")
formatter = logging.Formatter(conf.get("logging", "format"))
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
path = conf.get("logging", "path")
if not os.path.isdir(path):
    os.mkdir(path)
file_handler = TimedRotatingFileHandler(path + "/" + conf.get("logging", "name"), "midnight")
file_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
logger.addHandler(file_handler)
logger.setLevel(conf.get("logging", "level").upper())

app = FastAPI()

main_router = APIRouter()
main_router.include_router(v1_router, prefix="/api/v1")
main_router.include_router(room_router, prefix="/room")
app.include_router(main_router)
app.add_middleware(WrapRequestMiddleware)

logger.info("Application started", extra={"request_id": None})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, headers=[
        ("X-Powered-By", "FastApi"),
        ("X-Python-Version", sys.version),
    ])
