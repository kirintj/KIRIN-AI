from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from app.services.user import user_service
from app.core.ctx import CTX_USER_ID
from app.core.dependency import DependAuth
from app.models.admin import Api, Menu, Role, User
from app.schemas.base import Fail, Success
from app.schemas.login import *
from app.schemas.users import UpdatePassword, UserCreate
from app.settings import settings
from app.core.security import create_access_token, get_password_hash, verify_password

router = APIRouter()


@router.post("/access_token", summary="获取token")
async def login_access_token(credentials: CredentialsSchema):
    user: User = await user_service.authenticate(credentials)
    await user_service.update_last_login(user.id)
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + access_token_expires

    data = JWTOut(
        access_token=create_access_token(
            data=JWTPayload(
                user_id=user.id,
                username=user.username,
                is_superuser=user.is_superuser,
                exp=expire,
            )
        ),
        username=user.username,
    )
    return Success(data=data.model_dump())


@router.get("/userinfo", summary="查看用户信息", dependencies=[DependAuth])
async def get_userinfo():
    user_id = CTX_USER_ID.get()
    user_obj = await user_service.get(id=user_id)
    data = await user_obj.to_dict(exclude_fields=["password"])
    return Success(data=data)


@router.get("/usermenu", summary="查看用户菜单", dependencies=[DependAuth])
async def get_user_menu():
    user_id = CTX_USER_ID.get()
    user_obj = await User.filter(id=user_id).first()
    if user_obj.is_superuser:
        menus = await Menu.all()
    else:
        role_objs = await user_obj.roles.all().prefetch_related("menus")
        menu_set: dict[int, Menu] = {}
        for role_obj in role_objs:
            for menu in role_obj.menus:
                menu_set[menu.id] = menu
        menus = list(menu_set.values())

    menu_map = {menu.id: menu for menu in menus}
    parent_menus = [menu for menu in menus if menu.parent_id == 0]

    res = []
    for parent_menu in parent_menus:
        parent_menu_dict = await parent_menu.to_dict()
        children = []
        for menu in menus:
            if menu.parent_id == parent_menu.id:
                children.append(await menu.to_dict())
        children.sort(key=lambda x: x.get("order", 0))
        parent_menu_dict["children"] = children
        res.append(parent_menu_dict)
    return Success(data=res)


@router.get("/userapi", summary="查看用户API", dependencies=[DependAuth])
async def get_user_api():
    user_id = CTX_USER_ID.get()
    user_obj = await User.filter(id=user_id).first()
    if user_obj.is_superuser:
        api_objs = await Api.all()
        apis = [api.method.lower() + api.path for api in api_objs]
        return Success(data=apis)
    role_objs = await user_obj.roles.all().prefetch_related("apis")
    api_set: set[str] = set()
    for role_obj in role_objs:
        for api in role_obj.apis:
            api_set.add(api.method.lower() + api.path)
    return Success(data=list(api_set))


@router.post("/register", summary="用户注册")
async def register(req_in: UserCreate):
    try:
        existing = await user_service.get_by_username(req_in.username)
        if existing:
            return Fail(code=400, msg="用户名已存在")
        existing_email = await user_service.get_by_email(req_in.email)
        if existing_email:
            return Fail(code=400, msg="邮箱已被注册")
        await user_service.create_user(obj_in=req_in)
        return Success(msg="注册成功")
    except Exception:
        return Fail(code=500, msg="注册失败，请稍后重试")


@router.post("/update_password", summary="修改密码", dependencies=[DependAuth])
async def update_user_password(req_in: UpdatePassword):
    user_id = CTX_USER_ID.get()
    user = await user_service.get(user_id)
    verified = verify_password(req_in.old_password, user.password)
    if not verified:
        return Fail(msg="旧密码验证错误！")
    user.password = get_password_hash(req_in.new_password)
    await user.save()
    return Success(msg="修改成功")
