import request from './request'

// 获取所有用户（管理员）
export function getUsers(params) {
    return request({
        url: '/admin/users',
        method: 'get',
        params
    })
}

// 获取个人信息
export function getProfile() {
    return request({
        url: '/users/profile',
        method: 'get'
    })
}

// 获取通知
export function getNotifications() {
    return request({
        url: '/users/notifications',
        method: 'get'
    })
}

// 标记通知已读
export function markRead(id) {
    return request({
        url: `/users/notifications/${id}/read`,
        method: 'put'
    })
}

// 全部已读
export function markAllRead() {
    return request({
        url: '/users/notifications/read-all',
        method: 'put'
    })
}

// 清空所有
export function clearAllNotifications() {
    return request({
        url: '/users/notifications/clear-all',
        method: 'delete'
    })
}
