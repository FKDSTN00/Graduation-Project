import request from './request'

// 获取公告列表
export function getNotices() {
    return request({
        url: '/notice/',
        method: 'get'
    })
}

// 创建公告
export function createNotice(data) {
    return request({
        url: '/notice/',
        method: 'post',
        data
    })
}

// 更新公告
export function updateNotice(id, data) {
    return request({
        url: `/notice/${id}`,
        method: 'put',
        data
    })
}

// 删除公告
// 删除公告
export function deleteNotice(id) {
    return request({
        url: `/notice/${id}`,
        method: 'delete'
    })
}

// 获取公告详情
export function getNotice(id) {
    return request({
        url: `/notice/${id}`,
        method: 'get'
    })
}

// 投票 API
export function getVotes() {
    return request({
        url: '/notice/votes',
        method: 'get'
    })
}

export function createVote(data) {
    return request({
        url: '/notice/votes',
        method: 'post',
        data
    })
}

export function submitVote(id, option_key) {
    return request({
        url: `/notice/votes/${id}/submit`,
        method: 'post',
        data: { option_key }
    })
}

export function deleteVote(id) {
    return request({
        url: `/notice/votes/${id}`,
        method: 'delete'
    })
}
