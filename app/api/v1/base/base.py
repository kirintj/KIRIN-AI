from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from app.services.user import user_service
from app.core.ctx import CTX_USER_ID
from app.core.dependency import DependAuth
from app.models.admin import Api, Menu, User
from app.schemas.base import Fail, Success
from app.schemas.login import *
from app.schemas.users import UpdatePassword, UserCreate
from app.settings import settings
import jwt as pyjwt
from app.core.security import create_access_token, create_refresh_token, decode_token, get_password_hash, verify_password

router = APIRouter()


@router.post("/access_token", summary="获取token")
async def login_access_token(credentials: CredentialsSchema):
    user: User = await user_service.authenticate(credentials)
    await user_service.update_last_login(user.id)

    access_expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data=JWTPayload(user_id=user.id, username=user.username, is_superuser=user.is_superuser, exp=access_expire)
    )
    refresh_token = create_refresh_token(
        data=JWTPayload(user_id=user.id, username=user.username, is_superuser=user.is_superuser, exp=refresh_expire)
    )

    data = JWTOut(access_token=access_token, refresh_token=refresh_token, username=user.username)
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


@router.post("/refresh_token", summary="刷新token")
async def refresh_token(req_in: RefreshTokenIn):
    try:
        decode_data = decode_token(req_in.refresh_token)
    except pyjwt.ExpiredSignatureError:
        return Fail(code=401, msg="Refresh Token已过期")
    except Exception:
        return Fail(code=401, msg="无效的Refresh Token")

    if decode_data.get("type") != "refresh":
        return Fail(code=401, msg="请使用Refresh Token刷新")

    user_id = decode_data.get("user_id")
    if not user_id:
        return Fail(code=401, msg="Token中缺少用户信息")

    user = await User.filter(id=user_id).first()
    if not user:
        return Fail(code=401, msg="用户不存在")
    if not user.is_active:
        return Fail(code=401, msg="用户已被禁用")

    access_expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES)

    new_access_token = create_access_token(
        data=JWTPayload(user_id=user.id, username=user.username, is_superuser=user.is_superuser, exp=access_expire)
    )
    new_refresh_token = create_refresh_token(
        data=JWTPayload(user_id=user.id, username=user.username, is_superuser=user.is_superuser, exp=refresh_expire)
    )

    data = JWTOut(access_token=new_access_token, refresh_token=new_refresh_token, username=user.username)
    return Success(data=data.model_dump())
