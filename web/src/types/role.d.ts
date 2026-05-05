export interface RoleInfo {
  id: number
  name: string
  desc: string
  users: unknown[] | null
  menus: unknown[] | null
  apis: unknown[] | null
  created_at: string | null
  updated_at: string | null
}

export interface RoleCreate {
  name: string
  desc?: string
}

export interface RoleUpdate {
  id: number
  name: string
  desc?: string
}

export interface RoleUpdateMenusApis {
  id: number
  menu_ids: number[]
  api_infos: Record<string, unknown>[]
}
