import request from './request'

// 获取文件列表
export function getFiles(parentId = null) {
    return request({
        url: '/files/list',
        method: 'get',
        params: { parent_id: parentId }
    })
}

// 获取所有文件夹
export function getAllFolders() {
    return request({
        url: '/files/all_folders',
        method: 'get'
    })
}

// 创建文件夹 (管理员)
export function createFolder(data) {
    return request({
        url: '/files/folders',
        method: 'post',
        data
    })
}

// 上传文件 (管理员)
export function uploadFile(formData) {
    return request({
        url: '/files/upload',
        method: 'post',
        data: formData,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}

// 预览文件
export function previewFile(id) {
    return request({
        url: `/files/files/${id}/preview`,
        method: 'get'
    })
}

// 下载文件
export function downloadFile(id) {
    return request({
        url: `/files/files/${id}/download`,
        method: 'get'
    })
}

// 更新文件夹 (管理员)
export function updateFolder(id, data) {
    return request({
        url: `/files/folders/${id}`,
        method: 'put',
        data
    })
}

// 更新文件 (管理员)
export function updateFile(id, data) {
    return request({
        url: `/files/files/${id}`,
        method: 'put',
        data
    })
}

// 删除文件夹 (管理员)
export function deleteFolder(id) {
    return request({
        url: `/files/folders/${id}`,
        method: 'delete'
    })
}

// 删除文件 (管理员)
export function deleteFile(id) {
    return request({
        url: `/files/files/${id}`,
        method: 'delete'
    })
}
