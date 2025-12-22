<template>
  <div class="personal-center">
    <el-card class="profile-card">
      <template #header>
        <div class="card-header">
          <span>个人信息</span>
        </div>
      </template>
      
      <el-form :model="profileForm" label-width="100px">
        <el-form-item label="头像">
          <div class="avatar-upload">
            <el-avatar :size="80" :src="profileForm.avatar" icon="UserFilled" />
            <el-button size="small" @click="handleAvatarUpload" style="margin-left: 20px">更换头像</el-button>
            <input 
              ref="avatarInput" 
              type="file" 
              accept="image/*" 
              style="display: none" 
              @change="onAvatarChange"
            />
          </div>
        </el-form-item>
        
        <el-form-item label="用户名">
          <el-input v-model="profileForm.username" placeholder="请输入用户名" style="max-width: 300px" />
        </el-form-item>
        
        <el-form-item label="邮箱">
          <el-input v-model="profileForm.email" placeholder="请输入邮箱" style="max-width: 300px" disabled />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleUpdateProfile">保存个人信息</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="password-card">
      <template #header>
        <div class="card-header">
          <span>修改密码</span>
        </div>
      </template>
      
      <el-form :model="passwordForm" label-width="100px">
        <el-form-item label="当前密码">
          <el-input v-model="passwordForm.oldPassword" type="password" placeholder="请输入当前密码" style="max-width: 300px" />
        </el-form-item>
        
        <el-form-item label="新密码">
          <el-input v-model="passwordForm.newPassword" type="password" placeholder="请输入新密码" style="max-width: 300px" />
        </el-form-item>
        
        <el-form-item label="确认密码">
          <el-input v-model="passwordForm.confirmPassword" type="password" placeholder="请再次输入新密码" style="max-width: 300px" />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleChangePassword">修改密码</el-button>
        </el-form-item>
      </el-form>
    </el-card>

<el-card class="backup-card">
      <template #header>
        <div class="card-header">
          <span>备份与恢复</span>
        </div>
      </template>
      
      <el-form label-width="120px">
        <el-form-item label="备份数据">
          <el-button @click="handleBackup" icon="Download" :loading="isBackingUp">导出备份</el-button>
          <span class="hint">备份包括个人偏好设置和文档数据</span>
        </el-form-item>

        <el-form-item label="恢复数据">
          <el-button @click="handleRestoreClick" icon="Upload" :loading="isRestoring">选择备份文件</el-button>
          <input 
            ref="restoreInput" 
            type="file" 
            accept=".json" 
            style="display: none" 
            @change="onRestoreChange"
          />
          <span class="hint">从之前的备份文件恢复数据</span>
        </el-form-item>
      </el-form>

      <!-- 备份时输入隐私密码弹窗 -->
      <el-dialog 
        v-model="backupDialogVisible" 
        title="备份隐私空间"
        width="420px"
        :close-on-click-modal="false"
      >
        <p>检测到当前会话缺少隐私空间密码，如需同时备份隐私文档请输入密码。</p>
        <el-input 
          v-model="backupPrivacyPassword" 
          type="password" 
          placeholder="请输入隐私空间密码" 
          show-password
          @keyup.enter="confirmPrivacyBackup"
        />
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="backupDialogVisible = false">取消</el-button>
            <el-button @click="skipPrivacyBackup">跳过隐私文档</el-button>
            <el-button type="primary" @click="confirmPrivacyBackup">确认并备份</el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 恢复时输入隐私密码弹窗 -->
      <el-dialog
        v-model="restoreDialogVisible"
        title="恢复隐私空间文档"
        width="420px"
        :close-on-click-modal="false"
      >
        <p>备份中包含隐私文档，需要提供隐私空间密码才能恢复。您也可以选择跳过。</p>
        <el-input
          v-model="restorePrivacyPassword"
          type="password"
          placeholder="请输入隐私空间密码"
          show-password
          @keyup.enter="confirmPrivacyRestore"
        />
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="restoreDialogVisible = false">取消</el-button>
            <el-button @click="skipPrivacyRestore">跳过隐私文档</el-button>
            <el-button type="primary" @click="confirmPrivacyRestore">确认并恢复</el-button>
          </span>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore, usePrivacyStore } from '../store'
import { UserFilled, Download, Upload } from '@element-plus/icons-vue'
import request from '../api/request'
import { verifyPrivacyPassword } from '../api/privacy'

const userStore = useUserStore()
const privacyStore = usePrivacyStore()
const avatarInput = ref(null)
const restoreInput = ref(null)
const backupDialogVisible = ref(false)
const backupPrivacyPassword = ref('')
const isBackingUp = ref(false)
const isRestoring = ref(false)
const restoreDialogVisible = ref(false)
const restorePrivacyPassword = ref('')
let pendingBackupData = null

const profileForm = reactive({
  username: '',
  email: '',
  avatar: ''
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

onMounted(async () => {
  // 从 store 加载用户数据
  if (userStore.userInfo) {
    profileForm.username = userStore.userInfo.username
    profileForm.email = userStore.userInfo.email
    profileForm.avatar = userStore.userInfo.avatar || ''
  } else {
    // 如果 store 中没有用户信息，从后端获取
    try {
      const res = await request.get('/users/profile')
      profileForm.username = res.username
      profileForm.email = res.email
      profileForm.avatar = res.avatar || ''
      // 更新 store
      userStore.setUserInfo(res)
    } catch (error) {
      console.error('获取用户信息失败:', error)
      ElMessage.error('获取用户信息失败')
    }
  }
})

const handleAvatarUpload = () => {
  avatarInput.value.click()
}

const onAvatarChange = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  // 检查文件大小（限制为 2MB）
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.error('头像文件大小不能超过 2MB')
    return
  }
  
  // 检查文件类型
  const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    ElMessage.error('仅支持 PNG、JPG、GIF、WEBP 格式的图片')
    return
  }
  
  try {
    // 创建 FormData 上传文件
    const formData = new FormData()
    formData.append('file', file)
    
    // 上传到后端（MinIO）
    const res = await request.post('/users/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    // 更新头像URL
    profileForm.avatar = res.avatar_url
    
    // 更新 store
    userStore.setUserInfo({
      ...userStore.userInfo,
      avatar: res.avatar_url
    })
    
    ElMessage.success('头像上传成功')
  } catch (error) {
    ElMessage.error('头像上传失败: ' + (error.response?.data?.msg || error.message))
  }
}

const handleUpdateProfile = async () => {
  try {
    // 调用 API 更新个人资料
    const res = await request.put('/users/profile', {
      username: profileForm.username,
      avatar: profileForm.avatar
    })
    
    // 更新本地 store
    userStore.setUserInfo(res.user)
    
    ElMessage.success('个人信息更新成功')
  } catch (error) {
    ElMessage.error('更新失败: ' + (error.response?.data?.msg || error.message))
  }
}

const handleChangePassword = async () => {
  if (!passwordForm.oldPassword || !passwordForm.newPassword || !passwordForm.confirmPassword) {
    ElMessage.warning('请填写所有密码字段')
    return
  }
  
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  
  if (passwordForm.newPassword.length < 6) {
    ElMessage.warning('新密码长度不能少于6位')
    return
  }
  
  try {
    // 调用 API 修改密码
    await request.put('/users/password', {
      old_password: passwordForm.oldPassword,
      new_password: passwordForm.newPassword
    })
    
    ElMessage.success('密码修改成功，请重新登录')
    
    // 清空密码表单
    passwordForm.oldPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
  } catch (error) {
    ElMessage.error('修改失败: ' + (error.response?.data?.msg || error.message))
  }
}

const handleBackup = async () => {
  // 如果没有隐私空间密码，先弹窗让用户输入或跳过
  if (!privacyStore.password) {
    backupPrivacyPassword.value = ''
    backupDialogVisible.value = true
    return
  }
  performBackup(true)
}

const confirmPrivacyBackup = async () => {
  if (!backupPrivacyPassword.value) {
    ElMessage.warning('请输入隐私空间密码或选择跳过')
    return
  }
  try {
    // 验证密码并刷新隐私令牌，避免备份过程中令牌无效
    const { access_token } = await verifyPrivacyPassword(backupPrivacyPassword.value)
    privacyStore.setAccessToken(access_token)
    privacyStore.setPassword(backupPrivacyPassword.value)
    backupDialogVisible.value = false
    performBackup(true)
  } catch (error) {
    ElMessage.error(error.response?.data?.msg || '隐私空间密码验证失败')
  }
}

const skipPrivacyBackup = () => {
  backupDialogVisible.value = false
  performBackup(false)
}

const performBackup = async (includePrivacy = true) => {
  try {
    isBackingUp.value = true
    // 拉取普通文档列表并获取详情，用于备份
    const fetchDocs = async (isPrivacy = false) => {
      if (isPrivacy && !includePrivacy) return []

      const params = { sort_by: 'updated_at', order: 'desc' }
      if (isPrivacy) {
        params.privacy_space = true
        // 需要隐私密码解密内容
        if (privacyStore.password) {
          params._privacy_password = privacyStore.password
        } else {
          ElMessage.warning('缺少隐私空间密码，跳过隐私文档备份')
          return []
        }
        // 检查隐私令牌有效性
        if (!privacyStore.accessToken || privacyStore.needsReauth()) {
          ElMessage.warning('隐私空间访问已过期，请先在文档页重新验证后再备份')
          return []
        }
      }
      
      const list = await request.get('/docs/', { params })
      // 使用详情接口获取完整内容
      const details = await Promise.all(list.map(async (doc) => {
        try {
          const detailParams = {}
          if (isPrivacy && privacyStore.password) {
            detailParams._privacy_password = privacyStore.password
          }
          return await request.get(`/docs/${doc.id}`, { params: detailParams })
        } catch (err) {
          console.error('备份文档详情失败:', err)
          return null
        }
      }))
      return details.filter(Boolean)
    }

    // 拉取文件夹列表用于备份
    const fetchFolders = async (isPrivacy = false) => {
      const params = { in_privacy_space: isPrivacy }
      return await request.get('/docs/folders', { params })
    }

    const [publicDocs, privacyDocs, publicFolders, privacyFolders] = await Promise.all([
      fetchDocs(false),
      fetchDocs(true),
      fetchFolders(false),
      fetchFolders(true)
    ])

    const backupData = {
      userInfo: userStore.userInfo,
      preferences: {
        theme: localStorage.getItem('theme') || 'light'
      },
      folders: [
        ...publicFolders.map(f => ({ id: f.id, name: f.name, order: f.order, in_privacy_space: false })),
        ...privacyFolders.map(f => ({ id: f.id, name: f.name, order: f.order, in_privacy_space: true }))
      ],
      documents: {
        public: publicDocs,
        privacy: privacyDocs
      },
      timestamp: new Date().toISOString()
    }
    
    // 下载为 JSON 文件
    const blob = new Blob([JSON.stringify(backupData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `backup_${new Date().getTime()}.json`
    a.click()
    URL.revokeObjectURL(url)
    
    ElMessage.success('备份导出成功')
  } catch (error) {
    ElMessage.error('备份失败: ' + (error.response?.data?.msg || error.message))
  } finally {
    isBackingUp.value = false
  }
}

const handleRestoreClick = () => {
  restoreInput.value.click()
}

const onRestoreChange = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  try {
    await ElMessageBox.confirm(
      '恢复数据将覆盖当前设置和数据，是否继续？',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const reader = new FileReader()
    reader.onload = async (e) => {
      try {
        const backupData = JSON.parse(e.target.result)
        
        // 记录备份数据，若需要输入隐私密码则先弹窗
        pendingBackupData = backupData
        const hasPrivacyDocs = Array.isArray(backupData?.documents?.privacy) && backupData.documents.privacy.length > 0
        if (hasPrivacyDocs && !privacyStore.password) {
          restorePrivacyPassword.value = ''
          restoreDialogVisible.value = true
        } else {
          await performRestore(backupData, true)
        }
      } catch (error) {
        ElMessage.error('备份文件格式错误')
      }
    }
    reader.readAsText(file)
  } catch {
    // 用户取消
  }
}

// 确认输入隐私密码后恢复
const confirmPrivacyRestore = async () => {
  if (!restorePrivacyPassword.value) {
    ElMessage.warning('请输入隐私空间密码或选择跳过')
    return
  }
  try {
    const { access_token } = await verifyPrivacyPassword(restorePrivacyPassword.value)
    privacyStore.setAccessToken(access_token)
    privacyStore.setPassword(restorePrivacyPassword.value)
    restoreDialogVisible.value = false
    if (pendingBackupData) {
      await performRestore(pendingBackupData, true)
      pendingBackupData = null
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.msg || '隐私空间密码验证失败')
  }
}

// 跳过隐私文档恢复
const skipPrivacyRestore = async () => {
  restoreDialogVisible.value = false
  if (pendingBackupData) {
    await performRestore(pendingBackupData, false)
    pendingBackupData = null
  }
}

// 恢复备份：偏好 + 文档（含隐私，可选择跳过隐私）
const performRestore = async (backupData, includePrivacy) => {
  isRestoring.value = true
  try {
    // 恢复偏好设置
    if (backupData.preferences?.theme) {
      localStorage.setItem('theme', backupData.preferences.theme)
    }

    const documents = backupData.documents || {}
    const foldersFromBackup = backupData.folders || []
    const publicDocs = documents.public || []
    const privacyDocs = includePrivacy ? (documents.privacy || []) : []

    // 文件夹映射：按 name 和 in_privacy_space 匹配，不存在则创建
    const folderIdMap = new Map()
    const ensureFolders = async (isPrivacy = false) => {
      const existing = await request.get('/docs/folders', { params: { in_privacy_space: isPrivacy } })
      const existingByName = new Map(existing.map(f => [`${f.name}_${isPrivacy}`, f]))

      const targetFolders = foldersFromBackup.filter(f => f && typeof f.name === 'string' && f.in_privacy_space === isPrivacy)
      for (const folder of targetFolders) {
        const key = `${folder.name}_${isPrivacy}`
        if (existingByName.has(key)) {
          folderIdMap.set(folder.id, existingByName.get(key).id)
        } else {
          try {
            const created = await request.post('/docs/folders', { name: folder.name, in_privacy_space: isPrivacy })
            folderIdMap.set(folder.id, created.id)
          } catch (err) {
            console.error('创建文件夹失败:', err)
          }
        }
      }
      // 确保“未分组”映射
      const uncategorized = existing.find(f => f.name === '未分组')
      if (uncategorized) {
        folderIdMap.set('uncategorized_' + isPrivacy, uncategorized.id)
      }
    }

    await ensureFolders(false)
    await ensureFolders(true)

    // 封装文档写入逻辑
    const restoreDocs = async (docs, isPrivacy = false) => {
      if (!docs.length) return

      // 隐私文档前置验证
      if (isPrivacy) {
        if (!privacyStore.password) {
          ElMessage.warning('缺少隐私空间密码，已跳过隐私文档恢复')
          return
        }
        if (!privacyStore.accessToken || privacyStore.needsReauth()) {
          // 尝试刷新令牌
          try {
            const { access_token } = await verifyPrivacyPassword(privacyStore.password)
            privacyStore.setAccessToken(access_token)
          } catch (err) {
            ElMessage.error('隐私空间验证失败，已跳过隐私文档恢复')
            return
          }
        }
      }

      for (const doc of docs) {
        try {
          // 映射文件夹 ID，不存在则落到未分组
          let folderId = null
          if (doc.folder_id) {
            folderId = folderIdMap.get(doc.folder_id) || null
          }
          if (!folderId && folderIdMap.has('uncategorized_' + isPrivacy)) {
            folderId = folderIdMap.get('uncategorized_' + isPrivacy)
          }

          await request.post('/docs/', {
            title: doc.title,
            content: doc.content,
            folder_id: folderId,
            is_pinned: doc.is_pinned || false,
            created_at: doc.created_at,
            updated_at: doc.updated_at,
            in_privacy_space: isPrivacy,
            _privacy_password: isPrivacy ? privacyStore.password : undefined
          })
        } catch (err) {
          console.error('恢复文档失败:', err)
        }
      }
    }

    await restoreDocs(publicDocs, false)
    await restoreDocs(privacyDocs, true)

    ElMessage.success('数据恢复完成，文档已导入')
  } catch (error) {
    ElMessage.error('恢复失败: ' + (error.response?.data?.msg || error.message))
  } finally {
    isRestoring.value = false
  }
}
</script>

<style scoped>
.personal-center {
  max-width: 800px;
  margin: 0 auto;
}

.profile-card,
.password-card,
.backup-card {
  margin-bottom: 20px;
}

.card-header {
  font-weight: bold;
  font-size: 16px;
}

.avatar-upload {
  display: flex;
  align-items: center;
}

.hint {
  margin-left: 10px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
</style>
