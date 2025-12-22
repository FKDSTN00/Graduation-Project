import { defineStore } from 'pinia'
import { createTask, getTasks, updateTask, deleteTask } from '../api/task'
import { ElMessage } from 'element-plus'

export const useUserStore = defineStore('user', {
    state: () => ({
        userInfo: JSON.parse(localStorage.getItem('userInfo')) || null,
        token: localStorage.getItem('token') || ''
    }),
    actions: {
        // 设置 Token
        setToken(token) {
            this.token = token
            localStorage.setItem('token', token)
        },
        // 设置用户信息
        setUserInfo(info) {
            this.userInfo = info
            // 持久化到 localStorage
            localStorage.setItem('userInfo', JSON.stringify(info))
        },
        // 退出登录
        logout() {
            this.token = ''
            this.userInfo = null
            localStorage.removeItem('token')
            localStorage.removeItem('userInfo')
        }
    }
})

// 隐私空间状态管理
export const usePrivacyStore = defineStore('privacy', {
    state: () => ({
        accessToken: sessionStorage.getItem('privacy_token') || '',
        password: sessionStorage.getItem('privacy_password') || '', // 从 sessionStorage 恢复密码
        lastAccessTime: parseInt(sessionStorage.getItem('privacy_last_access')) || 0,
        isAuthenticated: false
    }),
    actions: {
        setAccessToken(token) {
            this.accessToken = token
            this.isAuthenticated = true
            this.lastAccessTime = Date.now()
            sessionStorage.setItem('privacy_token', token)
            sessionStorage.setItem('privacy_last_access', this.lastAccessTime.toString())
        },
        setPassword(password) {
            this.password = password
            // 持久化密码到 sessionStorage（仅在当前标签页有效）
            sessionStorage.setItem('privacy_password', password)
        },
        clearAuth() {
            this.accessToken = ''
            this.password = ''
            this.isAuthenticated = false
            this.lastAccessTime = 0
            sessionStorage.removeItem('privacy_token')
            sessionStorage.removeItem('privacy_password')
            sessionStorage.removeItem('privacy_last_access')
        },
        // 检查是否需要重新验证（超过3分钟）
        needsReauth() {
            if (!this.accessToken) return true
            const now = Date.now()
            const elapsed = (now - this.lastAccessTime) / 1000 // 转换为秒
            return elapsed > 180 // 3分钟 = 180秒
        },
        updateLastAccessTime() {
            this.lastAccessTime = Date.now()
            sessionStorage.setItem('privacy_last_access', this.lastAccessTime.toString())
        }
    }
})

// 任务管理状态
export const useTaskStore = defineStore('task', {
    state: () => ({
        tasks: []
    }),
    getters: {
        // 获取所有待办任务(不包括已完成)
        pendingTasks: (state) => state.tasks.filter(t => t.status !== 'completed').sort((a, b) => {
            // 优先级排序 High > Medium > Low
            const priorityMap = { High: 3, Medium: 2, Low: 1 }
            return priorityMap[b.priority] - priorityMap[a.priority]
        }),
        // 获取任务完成统计
        stats: (state) => {
            const total = state.tasks.length
            const completed = state.tasks.filter(t => t.status === 'completed').length
            const inProgress = state.tasks.filter(t => t.status === 'in-progress').length
            const pending = state.tasks.filter(t => t.status === 'pending').length
            const percentage = total === 0 ? 0 : Math.round((completed / total) * 100)
            return { total, completed, inProgress, pending, percentage }
        }
    },
    actions: {
        async fetchTasks() {
            try {
                const res = await getTasks()
                this.tasks = res
                // Remove success message after debugging to avoid spam
                // ElMessage.success(`成功加载 ${res.length} 个任务`) 
            } catch (error) {
                console.error('获取任务失败', error)
                ElMessage.error('无法加载任务列表，请检查网络或刷新页面')
            }
        },
        async addTask(task) {
            try {
                const res = await createTask(task)
                if (res.code === 200) {
                    this.fetchTasks()
                }
            } catch (error) {
                console.error('创建任务失败', error)
            }
        },
        async updateTask(id, updatedFields) {
            try {
                const res = await updateTask(id, updatedFields)
                if (res.code === 200) {
                    // 局部更新以提高响应速度，或者重新拉取
                    const index = this.tasks.findIndex(t => t.id === id)
                    if (index !== -1) {
                        this.tasks[index] = { ...this.tasks[index], ...updatedFields }
                    }
                }
            } catch (error) {
                console.error('更新任务失败', error)
            }
        },
        async deleteTask(id) {
            try {
                const res = await deleteTask(id)
                if (res.code === 200) {
                    this.tasks = this.tasks.filter(t => t.id !== id)
                }
            } catch (error) {
                console.error('删除任务失败', error)
            }
        },
        async toggleTaskStatus(id) {
            const task = this.tasks.find(t => t.id === id)
            if (task) {
                let nextStatus = 'pending'
                // 循环切换状态: pending -> in-progress -> completed -> pending
                if (task.status === 'pending') {
                    nextStatus = 'in-progress'
                } else if (task.status === 'in-progress') {
                    nextStatus = 'completed'
                } else {
                    nextStatus = 'pending'
                }

                await this.updateTask(id, { status: nextStatus })
            }
        }
    }
})
