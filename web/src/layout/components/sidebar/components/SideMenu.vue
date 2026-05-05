<template>
  <n-menu
    ref="menu"
    class="side-menu"
    accordion
    :indent="20"
    :collapsed-icon-size="20"
    :collapsed-width="64"
    :options="menuOptions"
    :value="activeKey"
    @update:value="handleMenuSelect"
  />
</template>

<script setup>
import { usePermissionStore, useAppStore } from '@/store'
import { renderCustomIcon, renderIcon, isExternal } from '@/utils'

const router = useRouter()
const curRoute = useRoute()
const permissionStore = usePermissionStore()
const appStore = useAppStore()

const activeKey = computed(() => curRoute.meta?.activeMenu || curRoute.name)

const menuOptions = computed(() => {
  return permissionStore.menus.map((item) => getMenuItem(item)).sort((a, b) => a.order - b.order)
})

const menu = ref(null)
watch(curRoute, async () => {
  await nextTick()
  menu.value?.showOption()
})

function resolvePath(basePath, path) {
  if (isExternal(path)) return path
  return (
    '/' +
    [basePath, path]
      .filter((path) => !!path && path !== '/')
      .map((path) => path.replace(/(^\/)|(\/$)/g, ''))
      .join('/')
  )
}

function getMenuItem(route, basePath = '') {
  let menuItem = {
    label: (route.meta && route.meta.title) || route.name,
    key: route.name,
    path: resolvePath(basePath, route.path),
    icon: getIcon(route.meta),
    order: route.meta?.order || 0,
  }

  const visibleChildren = route.children
    ? route.children.filter((item) => item.name && !item.isHidden)
    : []

  if (!visibleChildren.length) return menuItem

  if (visibleChildren.length === 1) {
    const singleRoute = visibleChildren[0]
    menuItem = {
      ...menuItem,
      label: singleRoute.meta?.title || singleRoute.name,
      key: singleRoute.name,
      path: resolvePath(menuItem.path, singleRoute.path),
      icon: getIcon(singleRoute.meta),
    }
    const visibleItems = singleRoute.children
      ? singleRoute.children.filter((item) => item.name && !item.isHidden)
      : []

    if (visibleItems.length === 1) {
      menuItem = getMenuItem(visibleItems[0], menuItem.path)
    } else if (visibleItems.length > 1) {
      menuItem.children = visibleItems
        .map((item) => getMenuItem(item, menuItem.path))
        .sort((a, b) => a.order - b.order)
    }
  } else {
    menuItem.children = visibleChildren
      .map((item) => getMenuItem(item, menuItem.path))
      .sort((a, b) => a.order - b.order)
  }
  return menuItem
}

function getIcon(meta) {
  if (meta?.customIcon) return renderCustomIcon(meta.customIcon, { size: 18 })
  if (meta?.icon) return renderIcon(meta.icon, { size: 18 })
  return null
}

function handleMenuSelect(key, item) {
  if (isExternal(item.path)) {
    window.open(item.path)
  } else {
    if (item.path === curRoute.path) {
      appStore.reloadPage()
    } else {
      router.push(item.path)
    }
  }
}
</script>

<style lang="scss">
.side-menu:not(.n-menu--collapsed) {
  .n-menu-item-content {
    &::before {
      left: 8px;
      right: 8px;
      border-radius: var(--hm-radius-md);
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    &.n-menu-item-content--selected,
    &:hover {
      &::before {
        border-left: none;
        background: var(--hm-brand-light);
      }
    }
    &.n-menu-item-content--selected {
      .n-menu-item-content-header {
        color: var(--hm-brand);
        font-weight: 500;
      }
      .n-menu-item-content__icon {
        color: var(--hm-brand);
        transform: scale(1.08);
        transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      }
    }
    .n-menu-item-content__icon {
      transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), color 0.25s;
    }
  }
}

.side-menu.n-menu--collapsed {
  .n-menu-item-content {
    &::before {
      border-radius: var(--hm-radius-md);
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    &.n-menu-item-content--selected,
    &:hover {
      &::before {
        border-left: none;
        background: var(--hm-brand-light);
      }
    }
    &.n-menu-item-content--selected {
      .n-menu-item-content__icon {
        color: var(--hm-brand);
        transform: scale(1.12);
        transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      }
    }
    .n-menu-item-content__icon {
      transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), color 0.25s;
    }
  }
}
</style>
