import json
import re
from datetime import datetime
from typing import Any

from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.dependency import AuthControl
from app.models.admin import AuditLog, User

from .bgtask import BgTasks


class SimpleBaseMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        await self.before_request(request)
        await self.app(scope, receive, send)
        await self.after_request(request)

    async def before_request(self, request: Request):
        return None

    async def after_request(self, request: Request):
        return None


class BackGroundTaskMiddleware(SimpleBaseMiddleware):
    async def before_request(self, request):
        await BgTasks.init_bg_tasks_obj()

    async def after_request(self, request):
        await BgTasks.execute_tasks()


class HttpAuditLogMiddleware:
    """纯 ASGI 审计日志中间件，避免 BaseHTTPMiddleware 消费 multipart 请求体"""

    SENSITIVE_FIELDS = frozenset({"password", "old_password", "new_password", "token", "secret", "api_key"})

    def __init__(self, app, methods: list[str], exclude_paths: list[str]):
        self.app = app
        self.methods = methods
        self.exclude_paths = exclude_paths
        self.audit_log_paths = ["/api/v1/auditlog/list"]
        self.max_body_size = 1024 * 1024

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        start_time = datetime.now()

        request_args = await self._get_request_args(request)

        content_type = request.headers.get("content-type", "")
        is_stream_body = (
            "multipart/form-data" in content_type
            or "application/octet-stream" in content_type
            or "image/" in content_type
        )

        if is_stream_body:
            inner_receive = receive
        else:
            body_bytes = await request.body()
            received = False

            async def inner_receive():
                nonlocal received
                if not received:
                    received = True
                    return {"type": "http.request", "body": body_bytes, "more_body": False}
                return {"type": "http.disconnect"}

        response_status = 0
        response_headers = []
        response_body_chunks = []

        async def send_wrapper(message):
            nonlocal response_status, response_headers
            if message["type"] == "http.response.start":
                response_status = message["status"]
                response_headers = message.get("headers", [])
            elif message["type"] == "http.response.body":
                response_body_chunks.append(message.get("body", b""))
            await send(message)

        await self.app(scope, inner_receive, send_wrapper)

        end_time = datetime.now()
        process_time = int((end_time.timestamp() - start_time.timestamp()) * 1000)

        if request.method in self.methods:
            should_log = True
            for path in self.exclude_paths:
                if re.search(path, request.url.path, re.I) is not None:
                    should_log = False
                    break

            if should_log:
                data = await self._get_request_log(request, response_status)
                data["response_time"] = process_time
                data["request_args"] = request_args
                data["response_body"] = self._parse_response_body(
                    request, response_headers, response_body_chunks
                )
                await AuditLog.create(**data)

    async def _get_request_args(self, request: Request) -> dict:
        args = {}
        for key, value in request.query_params.items():
            args[key] = value

        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                content_type = request.headers.get("content-type", "")
                if "multipart/form-data" in content_type or "application/octet-stream" in content_type or "image/" in content_type:
                    args["_content_type"] = content_type
                    content_length = request.headers.get("content-length")
                    if content_length:
                        args["_content_length"] = content_length
                else:
                    body = await request.json()
                    args.update(self._mask_sensitive_fields(body))
            except Exception:
                pass

        return args

    @classmethod
    def _mask_sensitive_fields(cls, data: dict) -> dict:
        if not isinstance(data, dict):
            return data
        return {
            k: "******" if k in cls.SENSITIVE_FIELDS else v
            for k, v in data.items()
        }

    def _parse_response_body(self, request: Request, headers: list, body_chunks: list) -> Any:
        for name, value in headers:
            if name == b"content-length" and int(value) > self.max_body_size:
                return {"code": 0, "msg": "Response too large to log", "data": None}

        body = b"".join(body_chunks)

        if any(request.url.path.startswith(path) for path in self.audit_log_paths):
            try:
                data = self.lenient_json(body)
                if isinstance(data, dict):
                    data.pop("response_body", None)
                    if "data" in data and isinstance(data["data"], list):
                        for item in data["data"]:
                            item.pop("response_body", None)
                return data
            except Exception:
                return None

        return self.lenient_json(body)

    async def _get_request_log(self, request: Request, status_code: int) -> dict:
        data: dict = {"path": request.url.path, "status": status_code, "method": request.method}
        app: FastAPI = request.app
        for route in app.routes:
            if (
                isinstance(route, APIRoute)
                and route.path_regex.match(request.url.path)
                and request.method in route.methods
            ):
                data["module"] = ",".join(route.tags)
                data["summary"] = route.summary or ""
        try:
            token = request.headers.get("token")
            user_obj = None
            if token:
                user_obj: User | None = await AuthControl.is_authed(token)
            data["user_id"] = user_obj.id if user_obj else 0
            data["username"] = user_obj.username if user_obj else ""
        except Exception:
            data["user_id"] = 0
            data["username"] = ""
        return data

    def lenient_json(self, v: Any) -> Any:
        if isinstance(v, (str, bytes)):
            try:
                return json.loads(v)
            except (ValueError, TypeError):
                pass
        return v
