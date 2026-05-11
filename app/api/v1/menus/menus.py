import logging

from fastapi import APIRouter, Query

from app.services.menu import menu_service
from app.schemas.base import Fail, Success, SuccessExtra
from app.schemas.menus import *

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/list", summary="查看菜单列表")
async def list_menu(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
):
    res_menu = await menu_service.get_menu_tree()
    return SuccessExtra(data=res_menu, total=len(res_menu), page=page, page_size=page_size)


@router.get("/get", summary="查看菜单")
async def get_menu(
    menu_id: int = Query(..., description="菜单id"),
):
    result = await menu_service.get(id=menu_id)
    return Success(data=result)


@router.post("/create", summary="创建菜单")
async def create_menu(
    menu_in: MenuCreate,
):
    await menu_service.create(obj_in=menu_in)
    return Success(msg="创建成功")


@router.post("/update", summary="更新菜单")
async def update_menu(
    menu_in: MenuUpdate,
):
    await menu_service.update(id=menu_in.id, obj_in=menu_in)
    return Success(msg="更新成功")


@router.delete("/delete", summary="删除菜单")
async def delete_menu(
    id: int = Query(..., description="菜单id"),
):
    child_menu_count = await menu_service.count_children(parent_id=id)
    if child_menu_count > 0:
        return Fail(msg="存在子菜单，无法删除")
    await menu_service.remove(id=id)
    return Success(msg="删除成功")
