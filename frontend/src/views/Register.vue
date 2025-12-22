<template>
  <div class="register-container">
    <div class="theme-switch">
      <el-switch
        v-model="isDark"
        inline-prompt
        active-icon="Moon"
        inactive-icon="Sunny"
        @change="toggleDark"
      />
    </div>
    <el-card class="register-card">
      <h2>企业知识协同平台 - 注册</h2>
      <el-form :model="registerForm" @submit.prevent="handleRegister">
        <el-form-item>
          <el-input v-model="registerForm.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="registerForm.email" type="email" placeholder="邮箱" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="registerForm.password" type="password" placeholder="密码" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="registerForm.confirmPassword" type="password" placeholder="确认密码" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" style="width: 100%">注册</el-button>
        </el-form-item>
        <el-form-item>
          <el-button type="text" @click="goToLogin" style="width: 100%">已有账号？立即登录</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Moon, Sunny } from '@element-plus/icons-vue'
import request from '../api/request'

const router = useRouter()
const isDark = ref(false)

const registerForm = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

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

const handleRegister = async () => {
  // 简单验证
  if (!registerForm.value.username || !registerForm.value.email || !registerForm.value.password) {
    ElMessage.error('请填写所有字段')
    return
  }

  if (registerForm.value.password !== registerForm.value.confirmPassword) {
    ElMessage.error('两次输入的密码不一致')
    return
  }

  try {
    await request.post('/auth/register', {
      username: registerForm.value.username,
      email: registerForm.value.email,
      password: registerForm.value.password
    })
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (error) {
    console.error('注册错误:', error)
    const errorMsg = error.response?.data?.msg || '注册失败'
    console.log('错误消息:', errorMsg)
    ElMessage.error(errorMsg)
  }
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  transition: background 0.3s;
  position: relative;
}

/* 主题切换按钮 */
.theme-switch {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 10;
}

/* 暗黑模式下的背景 */
:global(.dark) .register-container {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
}

.register-card {
  width: 400px;
  padding: 20px;
}

h2 {
  text-align: center;
  margin-bottom: 30px;
  color: var(--el-text-color-primary);
}
</style>
