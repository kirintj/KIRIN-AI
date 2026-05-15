import os
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


async def _ensure_business_tables():
    conn = Tortoise.get_connection("postgres")
    create_sqls = [
        """CREATE TABLE IF NOT EXISTS "todo_item" (
            "id" BIGSERIAL PRIMARY KEY,
            "user_id" VARCHAR(50) NOT NULL,
            "content" TEXT NOT NULL,
            "priority" VARCHAR(10) NOT NULL DEFAULT 'medium',
            "category" VARCHAR(20) NOT NULL DEFAULT 'other',
            "due_date" VARCHAR(20) NOT NULL DEFAULT '',
            "done" BOOLEAN NOT NULL DEFAULT FALSE,
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS "tracker_application" (
            "id" BIGSERIAL PRIMARY KEY,
            "user_id" VARCHAR(50) NOT NULL,
            "company" VARCHAR(100) NOT NULL DEFAULT '',
            "position" VARCHAR(100) NOT NULL DEFAULT '',
            "status" VARCHAR(20) NOT NULL DEFAULT 'applied',
            "salary" VARCHAR(50) NOT NULL DEFAULT '',
            "location" VARCHAR(50) NOT NULL DEFAULT '',
            "source" VARCHAR(50) NOT NULL DEFAULT '',
            "notes" TEXT NOT NULL DEFAULT '',
            "contact" VARCHAR(100) NOT NULL DEFAULT '',
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS "feedback_item" (
            "id" BIGSERIAL PRIMARY KEY,
            "user_id" VARCHAR(50) NOT NULL,
            "rating" VARCHAR(10) NOT NULL DEFAULT '',
            "comment" TEXT NOT NULL DEFAULT '',
            "related_query" TEXT NOT NULL DEFAULT '',
            "related_answer" TEXT NOT NULL DEFAULT '',
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS "conversation" (
            "id" BIGSERIAL PRIMARY KEY,
            "user_id" VARCHAR(50) NOT NULL,
            "title" VARCHAR(200) NOT NULL DEFAULT '新对话',
            "message_count" INT NOT NULL DEFAULT 0,
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS "conversation_message" (
            "id" BIGSERIAL PRIMARY KEY,
            "conversation_id" BIGINT NOT NULL REFERENCES "conversation"("id") ON DELETE CASCADE,
            "role" VARCHAR(20) NOT NULL,
            "content" TEXT NOT NULL,
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS "memory_item" (
            "id" BIGSERIAL PRIMARY KEY,
            "user_id" VARCHAR(50) NOT NULL,
            "user_msg" TEXT NOT NULL,
            "assistant_msg" TEXT NOT NULL,
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )""",
    ]
    index_sqls = [
        'CREATE INDEX IF NOT EXISTS "todo_item_user_id" ON "todo_item" ("user_id")',
        'CREATE INDEX IF NOT EXISTS "tracker_app_user_id" ON "tracker_application" ("user_id")',
        'CREATE INDEX IF NOT EXISTS "tracker_app_status" ON "tracker_application" ("status")',
        'CREATE INDEX IF NOT EXISTS "feedback_item_user_id" ON "feedback_item" ("user_id")',
        'CREATE INDEX IF NOT EXISTS "conversation_user_id" ON "conversation" ("user_id")',
        'CREATE INDEX IF NOT EXISTS "memory_item_user_id" ON "memory_item" ("user_id")',
    ]
    for sql in create_sqls:
        try:
            await conn.execute_script(sql)
        except Exception as e:
            logger.warning("Failed to create business table: %s", e)
    for sql in index_sqls:
        try:
            await conn.execute_script(sql)
        except Exception:
            pass


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

    await _ensure_business_tables()


async def init_superuser():
    from app.repositories.user import user_repository
    user = await user_repository.model.exists()
    if not user:
        admin_password = os.getenv("ADMIN_PASSWORD", "changeme")
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        if admin_password == "changeme":
            logger.warning("ADMIN_PASSWORD 未设置，使用默认密码，请尽快修改")
        await user_service.create_user(
            UserCreate(
                username="admin",
                email=admin_email,
                password=admin_password,
                avatar="",
                is_active=True,
                is_superuser=True,
            )
        )


async def init_menus():
    job_menu, _ = await Menu.update_or_create(
        name="求职助手",
        defaults={
            "menu_type": MenuType.CATALOG,
            "path": "/job-assistant",
            "order": 3,
            "parent_id": 0,
            "icon": "icon-park-outline:robot",
            "is_hidden": False,
            "component": "Layout",
            "keepalive": False,
            "redirect": "",
        },
    )
    job_submenus = [
        ("简历优化", "pipeline", 1, "icon-park-outline:clipboard", "/job-assistant"),
        ("面试问答", "interview", 2, "icon-park-outline:chat", "/job-assistant"),
        ("薪资谈判", "salary", 3, "icon-park-outline:finance", "/job-assistant"),
        ("求职攻略", "guide", 4, "icon-park-outline:map-draw", "/job-assistant"),
    ]
    for name, path, order, icon, component in job_submenus:
        await Menu.update_or_create(
            name=name,
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
        )
    sys_parent, _ = await Menu.update_or_create(
        name="系统管理",
        defaults={
            "menu_type": MenuType.CATALOG,
            "path": "/system",
            "order": 8,
            "parent_id": 0,
            "icon": "icon-park-outline:all-application",
            "is_hidden": False,
            "component": "Layout",
            "keepalive": False,
            "redirect": "/system/user",
        },
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
        await Menu.update_or_create(
            name=name,
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
        )


async def init_apis():
    apis = await Api.exists()
    if not apis:
        await api_service.refresh_api()


async def init_roles():
    admin_role, _ = await Role.get_or_create(name="管理员", defaults={"desc": "管理员角色"})
    user_role, _ = await Role.get_or_create(name="普通用户", defaults={"desc": "普通用户角色"})

    all_apis = await Api.all()
    await admin_role.apis.add(*all_apis)
    all_menus = await Menu.all()
    await admin_role.menus.add(*all_menus)

    admin_only_menu_names = {"用户管理", "角色管理", "菜单管理", "API管理", "审计日志"}
    user_menus = [m for m in all_menus if m.name not in admin_only_menu_names]
    await user_role.menus.clear()
    await user_role.menus.add(*user_menus)

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
