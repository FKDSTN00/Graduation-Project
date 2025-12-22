<template>
  <div class="login-container">
    <div class="theme-switch">
      <el-switch
        v-model="isDark"
        inline-prompt
        active-icon="Moon"
        inactive-icon="Sunny"
        @change="toggleDark"
      />
    </div>
    <el-card class="login-card">
      <div class="logo-container">
        <img src="../assets/logo.svg" alt="Logo" class="logo" />
        <h2>企业知识协同平台</h2>
      </div>
      <el-form :model="loginForm" @submit.prevent="handleLogin">
        <el-form-item>
          <el-input v-model="loginForm.username" placeholder="用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="loginForm.password" type="password" placeholder="密码" prefix-icon="Lock" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" style="width: 100%">登录</el-button>
        </el-form-item>
        <div class="form-footer">
          <el-button type="text" @click="goToRegister">还没有账号？立即注册</el-button>
          <el-button type="text" @click="handleForgotPassword">忘记密码</el-button>
        </div>
      </el-form>
    </el-card>

    <el-dialog v-model="forgotPasswordVisible" title="忘记密码" width="30%">
      <el-form :model="forgotPasswordForm" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="forgotPasswordForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="forgotPasswordForm.email" placeholder="请输入注册邮箱" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="forgotPasswordVisible = false">取消</el-button>
          <el-button type="primary" @click="handleResetPassword">发送申请</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Moon, Sunny } from '@element-plus/icons-vue'
import request from '../api/request'
import { useUserStore } from '../store'

const router = useRouter()
const userStore = useUserStore()

const loginForm = ref({
  username: '',
  password: ''
})

const isDark = ref(false)

onMounted(() => {
  // 从 localStorage 读取主题设置
  const theme = localStorage.getItem('theme')
  if (theme === 'dark') {
    isDark.value = true
    document.documentElement.classList.add('dark')
  } else {
    isDark.value = false
    document.documentElement.classList.remove('dark')
  }
})

const toggleDark = (val) => {
  const html = document.documentElement
  if (val) {
    html.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  } else {
    html.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  }
}

const handleLogin = async () => {
  try {
    const res = await request.post('/auth/login', loginForm.value)
    userStore.setToken(res.access_token)
    if (res.user) {
      userStore.setUserInfo(res.user)
    }
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error) {
    console.error('登录错误:', error)
    const errorMsg = error.response?.data?.msg || '登录失败'
    console.log('错误消息:', errorMsg)
    ElMessage.error(errorMsg)
  }
}

const goToRegister = () => {
  router.push('/register')
}

const handleForgotPassword = () => {
  forgotPasswordVisible.value = true
}

const forgotPasswordVisible = ref(false)
const forgotPasswordForm = ref({
  username: '',
  email: ''
})

const handleResetPassword = async () => {
  if (!forgotPasswordForm.value.username || !forgotPasswordForm.value.email) {
    ElMessage.warning('请填写用户名和邮箱')
    return
  }
  
  // 模拟发送重置请求
  ElMessage.success('重置密码申请已发送给管理员')
  forgotPasswordVisible.value = false
  forgotPasswordForm.value = { username: '', email: '' }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  transition: background 0.3s;
  position: relative;
}

/* 暗黑模式下的背景 */
:global(.dark) .login-container {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
}

.theme-switch {
  position: absolute;
  top: 20px;
  right: 20px;
}

.login-card {
  width: 400px;
  padding: 20px;
}

.logo-container {
  text-align: center;
  margin-bottom: 30px;
}

.logo {
  width: 60px;
  height: 60px;
  margin-bottom: 10px;
}

h2 {
  margin: 0;
  color: var(--el-text-color-primary);
  font-size: 24px;
}

.form-footer {
  display: flex;
  justify-content: space-between;
  margin-top: -10px;
}
</style>
