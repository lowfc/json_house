import logging
from datetime import datetime, timedelta

from fastapi import APIRouter
from sqlalchemy import select, exists, update, or_, func

from db import async_session
from utils import get_hash, Config
from fastapi import Request, Response as FResp
from models.db import Room, ContentType, Session, DisallowedHeaders
from models.validators import Response, CreateRoom, ShowRoom, RoomResponse, BadResponse, DeleteRoom, AuthResponse


v1_router = APIRouter()
conf_timing = Config().get("app", "timing")
logger = logging.getLogger("main")


@v1_router.get("/ping")
async def pong():
    return FResp("pong")


@v1_router.put("/room")
async def create_room(request: Request, body: CreateRoom) -> RoomResponse | BadResponse:
    user_agent = str(request.headers.get("user-agent"))
    logger.info(f"Request create room ({user_agent}) {body}", extra={"request_id": request.state.id})
    if not request.state.auth:
        logger.warning("Trying create room unauthorized", extra={"request_id": request.state.id})
        return BadResponse(
            error_code=401,
            message="Unauthorized"
        )
    uri = get_hash(user_agent)
    async with async_session() as session:
        ct_q = select(ContentType).where(ContentType.id == body.type_id)
        ct = await session.execute(ct_q)
        ct: ContentType = ct.scalar()
        if ct is None:
            logger.debug("Unknown content type", extra={"request_id": request.state.id})
            return BadResponse(
                message="Content Type unknown",
                data=None
            )
        in_headers = tuple(body.headers.keys())
        if len(in_headers) > 0:
            in_headers = [x.lower() for x in in_headers]
            disallowed_headers = select(exists(DisallowedHeaders).where(DisallowedHeaders.header_name.in_(in_headers)))
            exists_disallowed_headers = await session.execute(disallowed_headers)
            if exists_disallowed_headers.scalar():
                logger.debug("Rejected due forbidden header", extra={"request_id": request.state.id})
                return BadResponse(
                    message="You have forbidden headers in your request",
                    data=None
                )
        if body.name == "":
            session_rooms_count = select([func.count()]).select_from(Room).\
                where(Room.session_id == request.state.session_id)
            max_room_no = await session.execute(session_rooms_count)
            max_room_no = max_room_no.scalar()
            max_room_no += 1
            body.name = f"Room #{max_room_no}"
        deleted_at = (datetime.utcnow() + timedelta(seconds=conf_timing.get("room", 15000)))
        new_room = Room(
            content_type_id=ct.id,
            uri_hash=uri,
            name=body.name,
            content=body.content,
            headers=body.headers,
            require_parameters=body.require_parameters,
            on_invalid_status_code=body.on_invalid_status_code,
            wait_microseconds=body.wait_microseconds,
            session_id=request.state.session_id,
            deleted_at=deleted_at
        )
        session.add(new_room)
        await session.flush()
        logger.info(f"Created room, id: {new_room.id}", extra={"request_id": request.state.id})
        result = ShowRoom(
            url="/room/" + uri,
            id=new_room.id,
            name=new_room.name,
            content=new_room.content,
            headers=new_room.headers,
            content_type={
                "id": ct.id,
                "name": ct.type_name,
                "description": ct.description
            },
            require_parameters=new_room.require_parameters,
            on_invalid_status_code=new_room.on_invalid_status_code,
            wait_microseconds=new_room.wait_microseconds,
            created_at=new_room.created_at,
            deleted_at=new_room.deleted_at,
            deleted_at_unix=int(deleted_at.timestamp())
        )
        await session.commit()
        return RoomResponse(
            data=result
        )


@v1_router.delete("/room")
async def delete_room(request: Request, body: DeleteRoom) -> Response | BadResponse:
    if not request.state.auth:
        logger.warning("Trying delete room unauthorized", extra={"request_id": request.state.id})
        return BadResponse(
            error_code=401,
            message="Unauthorized"
        )
    async with async_session() as session:
        upd_room = update(Room) \
            .where(Room.id == body.id, Room.session_id == request.state.session_id,
                   or_(Room.deleted_at > datetime.utcnow(), Room.deleted_at.is_(None))) \
            .values(deleted_at=datetime.utcnow())
        result = await session.execute(upd_room)
        if result.rowcount > 0:
            await session.commit()
            return Response(message="Room has been successfully removed")
        await session.rollback()
        return BadResponse(message="Room not found", error_code=404)


@v1_router.get("/session")
async def get_session(request: Request) -> AuthResponse:
    user_agent = str(request.headers.get("user-agent"))
    hash_ = get_hash(user_agent)
    logger.debug(f"Create session ({user_agent}), give token: {hash_}", extra={"request_id": request.state.id})
    async with async_session() as session:
        new_session = Session(
            token=hash_
        )
        session.add(new_session)
        await session.flush()
        result = AuthResponse(
            data=new_session.token,
            user_agent=user_agent,
            deleted_at=(datetime.utcnow() + timedelta(seconds=conf_timing.get("session", 100000)))
        )
        await session.commit()
        return result
