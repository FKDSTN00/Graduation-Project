import request from './request'

export const fetchUsers = () => {
  return request.get('/admin/users')
}

export const banUser = (userId, ban = true) => {
  return request.put(`/admin/users/${userId}/ban`, { ban })
}

export const deleteUser = (userId) => {
  return request.delete(`/admin/users/${userId}`)
}

export const fetchUserDocs = (userId) => {
  return request.get(`/admin/users/${userId}/docs`)
}

export const fetchAdminTasks = () => {
  return request.get('/admin/tasks')
}

export const monitorDocuments = (keywords) => {
  return request.post('/admin/monitor/docs', { keywords })
}
