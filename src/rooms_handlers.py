import asyncio
import logging
from typing import Any
from datetime import datetime

import sqlalchemy.exc
from sqlalchemy import select, or_
from models.db import Room, ContentType
from fastapi import APIRouter, Request, Response

from db import async_session
from models.validators import BadResponse


room_router = APIRouter()
logger = logging.getLogger("main")


async def get_room_content(uri_hash: str, request: Request) -> Any | BadResponse:
    logger.debug(f"Request content {uri_hash}", extra={"request_id": request.state.id})
    if not request.state.auth:
        logger.warning("Trying get room content unauthorized", extra={"request_id": request.state.id})
        return BadResponse(
            error_code=401,
            message="Unauthorized"
        )
    start_processing = datetime.now()
    async with async_session() as session:
        q = select(Room, ContentType.content_type).where(Room.uri_hash == uri_hash) \
            .join(ContentType, Room.content_type_id == ContentType.id) \
            .where(or_(Room.deleted_at > datetime.utcnow(), Room.deleted_at.is_(None))).limit(1)
        check_room = await session.execute(q)
        try:
            room, content_type = check_room.one()
        except sqlalchemy.exc.NoResultFound:
            logger.debug(f"Authorized, invalid hash", extra={"request_id": request.state.id})
            return BadResponse(
                message="Room does not exists or expired"
            )
    for k in room.require_parameters.keys():
        if request.query_params.get(k) != room.require_parameters[k]:
            return Response(status_code=room.on_invalid_status_code)
    resp = Response(content=room.content, status_code=200)
    resp.headers["Content-Type"] = content_type
    for k in room.headers.keys():
        resp.headers[k] = room.headers[k]
    if room.wait_microseconds > 0:
        passed = (datetime.now() - start_processing).microseconds / 100
        if passed < room.wait_microseconds:
            await asyncio.sleep((room.wait_microseconds - passed) / 1000)
    logger.debug(f"Successfully return answer: " + room.content, extra={"request_id": request.state.id})
    return resp


room_router.add_api_route("/{uri_hash}", get_room_content, methods=[
    "GET",
    "POST",
    "PUT",
    "DELETE",
    "CREATE",
    "OPTIONS",
    "PATCH",
    "COPY",
    "HEAD",
    "LINK",
    "UNLINK",
    "LOCK",
    "UNLOCK",
    "PURGE",
    "PROPFIND",
    "VIEW",
    ])
