import axios from 'axios'

// 创建 axios 实例
const request = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
    timeout: 60000 // 请求超时时间：60秒
})

// 请求拦截器
request.interceptors.request.use(
    config => {
        // 从 localStorage 获取 token
        const token = localStorage.getItem('token')
        console.log('请求拦截器 - URL:', config.url, 'Token存在:', !!token)

        if (token) {
            // 如果有 token，添加到请求头中
            config.headers['Authorization'] = `Bearer ${token}`
        } else {
            console.warn('警告: 请求没有 JWT token!')
        }

        // 如果请求中包含隐私空间令牌，添加到请求头
        const privacyToken = sessionStorage.getItem('privacy_token')
        if (privacyToken && (config.url.includes('/docs/') || config.url.includes('/privacy/'))) {
            config.headers['X-Privacy-Token'] = privacyToken
            console.log('添加隐私令牌到请求头')
        }

        return config
    },
    error => {
        return Promise.reject(error)
    }
)

// 响应拦截器
request.interceptors.response.use(
    response => {
        // 直接返回数据部分
        return response.data
    },
    error => {
        // 处理 401 未授权错误
        if (error.response && error.response.status === 401) {
            const currentPath = window.location.pathname
            const requestUrl = error.config?.url || ''
            // 识别隐私空间相关请求（携带隐私令牌或访问隐私接口/隐私文档）
            const hasPrivacyHeader = !!error.config?.headers?.['X-Privacy-Token']
            const isPrivacyEndpoint = requestUrl.includes('/privacy/')
            const isPrivacyDoc = requestUrl.includes('/docs/') && (hasPrivacyHeader || error.config?.params?.privacy_space)
            const isPrivacyRequest = isPrivacyEndpoint || isPrivacyDoc

            // 如果是隐私空间相关的 401（访问令牌过期），不强制退出登录
            // 只是让隐私空间模块自己处理重新验证
            if (isPrivacyRequest && requestUrl !== '/privacy/check-password') {
                // 隐私令牌过期，不需要退出登录，只需要重新验证隐私密码
                console.log('隐私空间访问令牌过期，需要重新验证')
                return Promise.reject(error)
            }

            // 其他 401 错误（JWT token 过期），才需要退出登录
            if (currentPath !== '/login' && currentPath !== '/register') {
                console.error('JWT token 过期或无效，需要重新登录')
                localStorage.removeItem('token')
                sessionStorage.removeItem('privacy_token')
                window.location.href = '/login'
            }
        }
        return Promise.reject(error)
    }
)

export default request
