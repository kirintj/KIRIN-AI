export interface ApiResponse<T = unknown> {
  code: number
  msg: string
  data: T
}

export interface PageResponse<T = unknown> {
  code: number
  msg: string
  data: T[]
  total: number
  page: number
  page_size: number
}
