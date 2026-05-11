import logging

from fastapi import APIRouter, Body, Query
from tortoise.expressions import Q

from app.services.user import user_service
from app.schemas.base import Fail, Success, SuccessExtra
from app.schemas.users import UserCreate, UserUpdate

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/list", summary="查看用户列表")
async def list_user(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    username: str = Query("", description="用户名称，用于搜索"),
    email: str = Query("", description="邮箱地址"),
    dept_id: int = Query(None, description="部门ID"),
):
    q = Q()
    if username:
        q &= Q(username__contains=username)
    if email:
        q &= Q(email__contains=email)
    if dept_id is not None:
        q &= Q(dept_id=dept_id)
    total, user_objs = await user_service.list(page=page, page_size=page_size, search=q)

    # Batch prefetch roles for all users (avoids N+1)
    for user in user_objs:
        await user.fetch_related("roles")

    # Batch fetch departments
    dept_ids = {u.dept_id for u in user_objs if u.dept_id}
    dept_map = {}
    if dept_ids:
        from app.models.admin import Dept
        dept_objs = await Dept.filter(id__in=dept_ids)
        dept_map = {d.id: d for d in dept_objs}

    data = []
    for user in user_objs:
        d = await user.to_dict(exclude_fields=["password"])
        d["roles"] = [{"id": r.id, "name": r.name} for r in user.roles]
        dept = dept_map.get(user.dept_id)
        d["dept"] = await dept.to_dict() if dept else {}
        data.append(d)

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看用户")
async def get_user(
    user_id: int = Query(..., description="用户ID"),
):
    user_obj = await user_service.get(id=user_id)
    user_dict = await user_obj.to_dict(exclude_fields=["password"])
    return Success(data=user_dict)


@router.post("/create", summary="创建用户")
async def create_user(
    user_in: UserCreate,
):
    user = await user_service.get_by_email(user_in.email)
    if user:
        return Fail(code=400, msg="该邮箱已被注册")
    new_user = await user_service.create_user(obj_in=user_in)
    await user_service.update_roles(new_user, user_in.role_ids or [])
    return Success(msg="创建成功")


@router.post("/update", summary="更新用户")
async def update_user(
    user_in: UserUpdate,
):
    user = await user_service.update(id=user_in.id, obj_in=user_in)
    await user_service.update_roles(user, user_in.role_ids or [])
    return Success(msg="更新成功")


@router.delete("/delete", summary="删除用户")
async def delete_user(
    user_id: int = Query(..., description="用户ID"),
):
    await user_service.remove(id=user_id)
    return Success(msg="删除成功")


@router.post("/reset_password", summary="重置密码")
async def reset_password(user_id: int = Body(..., description="用户ID", embed=True)):
    new_password = await user_service.reset_password(user_id)
    return Success(msg="密码已重置", data={"new_password": new_password})
