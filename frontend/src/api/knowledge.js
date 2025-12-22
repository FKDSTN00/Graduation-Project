import request from './request'

// 分类管理
export const getCategories = () => {
    return request.get('/knowledge/categories')
}

export const createCategory = (data) => {
    return request.post('/knowledge/categories', data)
}

export const updateCategory = (id, data) => {
    return request.put(`/knowledge/categories/${id}`, data)
}

export const deleteCategory = (id) => {
    return request.delete(`/knowledge/categories/${id}`)
}

// 文章管理
export const getArticles = (categoryId) => {
    const params = categoryId ? { category_id: categoryId } : {}
    return request.get('/knowledge/articles', { params })
}

export const getArticle = (id) => {
    return request.get(`/knowledge/articles/${id}`)
}

export const createArticle = (data) => {
    return request.post('/knowledge/articles', data)
}

export const updateArticle = (id, data) => {
    return request.put(`/knowledge/articles/${id}`, data)
}

export const deleteArticle = (id) => {
    return request.delete(`/knowledge/articles/${id}`)
}
