export type MethodType = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'

export interface ApiInfo {
  path: string
  summary: string
  method: MethodType
  tags: string
}

export interface ApiCreate extends ApiInfo {}

export interface ApiUpdate extends ApiInfo {
  id: number
}
