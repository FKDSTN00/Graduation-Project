/**
 * 隐私空间 API
 */
import request from './request'

/**
 * 检查是否已设置隐私空间密码
 */
export const checkPrivacyPassword = () => {
  return request.get('/privacy/check-password')
}

/**
 * 设置隐私空间密码
 */
export const setPrivacyPassword = (password, oldPassword = null) => {
  return request.post('/privacy/set-password', {
    password,
    old_password: oldPassword
  })
}

/**
 * 验证隐私空间密码
 */
export const verifyPrivacyPassword = (password) => {
  return request.post('/privacy/verify-password', { password })
}

/**
 * 验证隐私空间访问令牌
 */
export const verifyPrivacyToken = (token) => {
  return request.post('/privacy/verify-token', { token })
}

/**
 * 刷新隐私空间访问令牌
 */
export const refreshPrivacyToken = (token) => {
  return request.post('/privacy/refresh-token', { token })
}

/**
 * 撤销隐私空间访问令牌（退出）
 */
export const revokePrivacyToken = () => {
  return request.post('/privacy/revoke-token')
}
