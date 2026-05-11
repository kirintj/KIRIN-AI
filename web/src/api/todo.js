import { request } from '@/utils'

export default {
  getTodoList: (params = {}) => request.get('/chat/todos', { params }),
  createTodo: (data = {}) => request.post('/chat/todos', data),
  toggleTodo: (data = {}) => request.put('/chat/todos/toggle', data),
  updateTodo: (data = {}) => request.put('/chat/todos', data),
  deleteTodo: (params = {}) => request.delete('/chat/todos', { params }),
  clearCompletedTodos: () => request.delete('/chat/todos/completed'),
}
