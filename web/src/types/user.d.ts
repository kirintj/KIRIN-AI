export interface UserInfo {
  id: number
  email: string | null
  username: string | null
  avatar: string | null
  is_active: boolean | null
  is_superuser: boolean | null
  created_at: string | null
  updated_at: string | null
  last_login: string | null
  roles: unknown[] | null
}

export interface UserCreate {
  email: string
  username: string
  password: string
  avatar?: string | null
  is_active?: boolean
  is_superuser?: boolean
  role_ids?: number[]
  dept_id?: number
}

export interface UserUpdate {
  id: number
  email: string
  username: string
  avatar?: string | null
  is_active?: boolean
  password?: string | null
  is_superuser?: boolean
  role_ids?: number[]
  dept_id?: number
}

export interface UpdatePassword {
  old_password: string
  new_password: string
}
