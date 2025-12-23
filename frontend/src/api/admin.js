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

export const exportBackup = () => {
  return request.get('/admin/backup/export', { responseType: 'blob' })
}

export const importBackup = (formData) => {
  return request.post('/admin/backup/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const getMonitorKeywords = () => {
  return request.get('/admin/monitor/keywords')
}

export const addMonitorKeyword = (keyword) => {
  return request.post('/admin/monitor/keywords', { keyword })
}

export const deleteMonitorKeyword = (id) => {
  return request.delete(`/admin/monitor/keywords/${id}`)
}
