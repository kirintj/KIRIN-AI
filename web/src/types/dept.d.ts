export interface DeptInfo {
  name: string
  desc: string
  order: number
  parent_id: number
}

export interface DeptCreate extends DeptInfo {}

export interface DeptUpdate extends DeptInfo {
  id: number
}
