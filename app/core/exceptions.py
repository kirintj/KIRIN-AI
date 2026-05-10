import logging

from fastapi.exceptions import (
    HTTPException,
    RequestValidationError,
    ResponseValidationError,
)
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from tortoise.exceptions import DoesNotExist, IntegrityError

_logger = logging.getLogger(__name__)


class SettingNotFound(Exception):
    pass


async def DoesNotExistHandle(req: Request, exc: DoesNotExist) -> JSONResponse:
    _logger.warning("DoesNotExist: %s", exc)
    content = dict(code=404, msg="请求的资源不存在")
    return JSONResponse(content=content, status_code=404)


async def IntegrityHandle(_: Request, exc: IntegrityError) -> JSONResponse:
    _logger.warning("IntegrityError: %s", exc)
    content = dict(code=400, msg="数据完整性错误，请检查输入")
    return JSONResponse(content=content, status_code=400)


async def HttpExcHandle(_: Request, exc: HTTPException) -> JSONResponse:
    content = dict(code=exc.status_code, msg=exc.detail, data=None)
    return JSONResponse(content=content, status_code=exc.status_code)


async def RequestValidationHandle(_: Request, exc: RequestValidationError) -> JSONResponse:
    _logger.debug("RequestValidationError: %s", exc)
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        errors.append(f"{loc}: {err.get('msg', '')}")
    msg = "; ".join(errors) if errors else "请求参数验证失败"
    content = dict(code=422, msg=msg)
    return JSONResponse(content=content, status_code=422)


async def ResponseValidationHandle(_: Request, exc: ResponseValidationError) -> JSONResponse:
    _logger.error("ResponseValidationError: %s", exc)
    content = dict(code=500, msg="服务端响应异常")
    return JSONResponse(content=content, status_code=500)
