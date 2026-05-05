export type MenuType = 'catalog' | 'menu'

export interface MenuItem {
  id: number
  name: string
  path: string
  remark: Record<string, unknown> | null
  menu_type: MenuType | null
  icon: string | null
  order: number
  parent_id: number
  is_hidden: boolean
  component: string
  keepalive: boolean
  redirect: string | null
  children?: MenuItem[] | null
}

export interface MenuCreate {
  menu_type?: MenuType
  name: string
  icon?: string | null
  path: string
  order?: number | null
  parent_id?: number | null
  is_hidden?: boolean
  component?: string
  keepalive?: boolean
  redirect?: string | null
}

export interface MenuUpdate {
  id: number
  menu_type?: MenuType | null
  name?: string | null
  icon?: string | null
  path?: string | null
  order?: number | null
  parent_id?: number | null
  is_hidden?: boolean
  component?: string
  keepalive?: boolean
  redirect?: string | null
}
