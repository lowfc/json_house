from datetime import datetime

from db import async_session
from sqlalchemy import select
from fastapi import Request, Response
from models.db import Session, RequestIdSeq
from starlette.middleware.base import BaseHTTPMiddleware


class WrapRequestMiddleware(BaseHTTPMiddleware):
    def __init__(
            self,
            app
    ):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start_request = datetime.now()
        request.state.auth = False
        token = request.headers.get("x-session-token")
        request.state.id = None
        async with async_session() as session:
            request_id = await session.execute(RequestIdSeq.next_value())
            request.state.id = f"r{request_id.scalar()} > {request.client.host}"
            if token is not None:
                session_info_query = select(Session).where(Session.token == token, Session.deleted_at.is_(None))
                result_token = await session.execute(session_info_query)
                result_token = result_token.scalar()
                if result_token is not None:
                    request.state.auth = True
                    request.state.session_id = result_token.id
                    request.state.session_token = result_token.token

        response: Response = await call_next(request)

        response.headers["X-Process-Time-Microseconds"] = str((datetime.now() - start_request).microseconds)
        response.headers["Real-Server-Time"] = start_request.isoformat()

        return response
