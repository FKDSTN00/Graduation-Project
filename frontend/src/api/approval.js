import request from './request'

// 提交审批申请
export function createApproval(data) {
    return request({
        url: '/approval/',
        method: 'post',
        data
    })
}

// 获取审批列表
export function getApprovals() {
    return request({
        url: '/approval/',
        method: 'get'
    })
}

// 更新审批状态 (管理员)
export function updateApprovalStatus(id, action) {
    return request({
        url: `/approval/${id}/status`,
        method: 'put',
        data: { action }
    })
}
// 清空已处理记录 (管理员)
export function clearProcessedApprovals() {
    return request({
        url: '/approval/processed',
        method: 'delete'
    })
}
