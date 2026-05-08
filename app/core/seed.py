import shutil

from aerich import Command
from tortoise import Tortoise
from tortoise.expressions import Q

from app.log import logger
from app.models.admin import Api, Menu, Role
from app.schemas.menus import MenuType
from app.schemas.users import UserCreate
from app.services.api import api_service
from app.services.user import user_service
from app.settings.config import settings


async def init_db():
    command = Command(tortoise_config=settings.TORTOISE_ORM)
    try:
        await command.init_db(safe=True)
    except FileExistsError:
        pass

    await command.init()
    try:
        await command.migrate()
    except AttributeError:
        logger.warning("unable to retrieve model history from database, model history will be created from scratch")
        shutil.rmtree("migrations")
        await command.init_db(safe=True)
    except UnboundLocalError as e:
        logger.warning("aerich migrate encountered known bug, skipping migration: %s", e)

    try:
        await command.upgrade(run_in_transaction=True)
    except Exception:
        logger.warning("aerich upgrade failed, skipping")

    try:
        await Tortoise.init(config=settings.TORTOISE_ORM, _enable_global_fallback=True)
    except TypeError:
        await Tortoise.init(config=settings.TORTOISE_ORM)
    await Tortoise.generate_schemas()


async def init_superuser():
    from app.repositories.user import user_repository
    user = await user_repository.model.exists()
    if not user:
        await user_service.create_user(
            UserCreate(
                username="admin",
                email="admin@admin.com",
                password="123456",
                avatar="https://th.bing.com/th/id/OIP.OnlQGCq7OZG8-Qth4MIm_QHaEK?o=7rm=3&rs=1&pid=ImgDetMain&o=7&rm=3",
                is_active=True,
                is_superuser=True,
            )
        )


async def init_menus():
    job_menu, _ = await Menu.get_or_create(
        defaults={
            "menu_type": MenuType.CATALOG,
            "path": "/job-assistant",
            "order": 1,
            "parent_id": 0,
            "icon": "icon-park-outline:robot",
            "is_hidden": False,
            "component": "Layout",
            "keepalive": False,
            "redirect": "",
        },
        name="求职助手",
    )
    job_submenus = [
        ("简历优化", "pipeline", 1, "icon-park-outline:clipboard", "/job-assistant"),
        ("面试问答", "interview", 2, "icon-park-outline:chat", "/job-assistant"),
        ("薪资谈判", "salary", 3, "icon-park-outline:finance", "/job-assistant"),
        ("求职攻略", "guide", 4, "icon-park-outline:map-draw", "/job-assistant"),
    ]
    for name, path, order, icon, component in job_submenus:
        await Menu.get_or_create(
            defaults={
                "menu_type": MenuType.MENU,
                "path": path,
                "order": order,
                "parent_id": job_menu.id,
                "icon": icon,
                "is_hidden": False,
                "component": component,
                "keepalive": False,
            },
            name=name,
        )
    sys_parent, _ = await Menu.get_or_create(
        defaults={
            "menu_type": MenuType.CATALOG,
            "path": "/system",
            "order": 2,
            "parent_id": 0,
            "icon": "icon-park-outline:all-application",
            "is_hidden": False,
            "component": "Layout",
            "keepalive": False,
            "redirect": "/system/user",
        },
        name="系统管理",
    )

    sys_submenus = [
        ("用户管理", "user", 1, "icon-park-outline:user", "/system/user"),
        ("角色管理", "role", 2, "icon-park-outline:people", "/system/role"),
        ("菜单管理", "menu", 3, "icon-park-outline:application-menu", "/system/menu"),
        ("API管理", "api", 4, "icon-park-outline:api", "/system/api"),
        ("审计日志", "auditlog", 5, "icon-park-outline:audit", "/system/auditlog"),
        ("对话历史", "chathistory", 6, "icon-park-outline:history", "/system/chathistory"),
        ("AI模型配置", "ai-config", 7, "icon-park-outline:setting-config", "/system/ai-config"),
    ]

    for name, path, order, icon, component in sys_submenus:
        await Menu.get_or_create(
            defaults={
                "menu_type": MenuType.MENU,
                "path": path,
                "order": order,
                "parent_id": sys_parent.id,
                "icon": icon,
                "is_hidden": False,
                "component": component,
                "keepalive": False,
            },
            name=name,
        )


async def init_apis():
    apis = await Api.exists()
    if not apis:
        await api_service.refresh_api()


async def init_roles():
    roles = await Role.exists()
    if not roles:
        admin_role = await Role.create(
            name="管理员",
            desc="管理员角色",
        )
        user_role = await Role.create(
            name="普通用户",
            desc="普通用户角色",
        )

        all_apis = await Api.all()
        await admin_role.apis.add(*all_apis)
        all_menus = await Menu.all()
        await admin_role.menus.add(*all_menus)
        await user_role.menus.add(*all_menus)

        basic_apis = await Api.filter(Q(method__in=["GET"]) | Q(tags="基础模块"))
        await user_role.apis.add(*basic_apis)


async def init_config():
    from app.services.config import sysconfig_service
    await sysconfig_service.init_defaults()


async def init_data():
    await init_db()
    await init_superuser()
    await init_menus()
    await init_apis()
    await init_roles()
    await init_config()
