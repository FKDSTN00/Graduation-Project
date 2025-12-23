import request from './request'

// 获取反馈列表
export function getFeedbacks(params) {
    return request({
        url: '/feedback/',
        method: 'get',
        params
    })
}

// 创建反馈
export function createFeedback(data) {
    return request({
        url: '/feedback/',
        method: 'post',
        data
    })
}

// 获取反馈详情
export function getFeedbackDetail(id) {
    return request({
        url: `/feedback/${id}`,
        method: 'get'
    })
}

// 回复反馈
export function replyFeedback(id, data) {
    return request({
        url: `/feedback/${id}/reply`,
        method: 'post',
        data
    })
}

// 删除反馈
export function deleteFeedback(id) {
    return request({
        url: `/feedback/${id}`,
        method: 'delete'
    })
}

// 删除回复
export function deleteReply(id) {
    return request({
        url: `/feedback/reply/${id}`,
        method: 'delete'
    })
}

// 点赞/取消点赞 反馈
export function likeFeedback(id) {
    return request({
        url: `/feedback/${id}/like`,
        method: 'post'
    })
}

// 点赞/取消点赞 回复
export function likeReply(id) {
    return request({
        url: `/feedback/reply/${id}/like`,
        method: 'post'
    })
}
