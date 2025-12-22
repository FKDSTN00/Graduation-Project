import request from './request'

export const createTask = (data) => {
    return request.post('/tasks/', data)
}

export const getTasks = () => {
    return request.get('/tasks/')
}

export const updateTask = (id, data) => {
    return request.put(`/tasks/${id}`, data)
}

export const deleteTask = (id) => {
    return request.delete(`/tasks/${id}`)
}
