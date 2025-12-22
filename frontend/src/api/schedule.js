import request from './request'

// 获取所有事件
export function getEvents(params) {
    return request({
        url: '/schedule/',
        method: 'get',
        params
    })
}

// 创建日程
export function createSchedule(data) {
    return request({
        url: '/schedule/schedules',
        method: 'post',
        data
    })
}

// 更新日程
export function updateSchedule(id, data) {
    return request({
        url: `/schedule/schedules/${id}`,
        method: 'put',
        data
    })
}

// 删除日程
export function deleteSchedule(id) {
    return request({
        url: `/schedule/schedules/${id}`,
        method: 'delete'
    })
}

// 创建会议
export function createMeeting(data) {
    return request({
        url: '/schedule/meetings',
        method: 'post',
        data
    })
}

// 更新会议
export function updateMeeting(id, data) {
    return request({
        url: `/schedule/meetings/${id}`,
        method: 'put',
        data
    })
}

// 删除会议
export function deleteMeeting(id) {
    return request({
        url: `/schedule/meetings/${id}`,
        method: 'delete'
    })
}
