<template>
  <div class="document-container">
  <!-- 侧边栏 -->
    <div class="sidebar">
      <!-- 全部文档区域 -->
      <div class="view-section">
        <div 
          class="view-header" 
          :class="{ active: currentView === 'all' && !currentFolder }"
          @click="switchView('all')"
        >
          <el-icon><Document /></el-icon> 全部文档
        </div>
        
        <div class="folder-group" v-show="currentView === 'all'">
          <div class="folder-header">
            <span>文件夹</span>
            <el-button link type="primary" @click="handleCreateFolder">
              <el-icon><Plus /></el-icon>
            </el-button>
          </div>
          <div 
            v-for="(folder, index) in folders" 
            :key="folder.id"
            class="nav-item folder-item"
            :class="{ active: currentFolder?.id === folder.id, 'draggable-folder': folder.name !== '未分组' }"
            @click="selectFolder(folder)"
            :draggable="folder.name !== '未分组'"
            @dragstart="onDragStart($event, index)"
            @dragover="onDragOver($event)"
            @drop="onDrop($event, index)"
          >
            <span class="folder-name"><el-icon><Folder /></el-icon> {{ folder.name }}</span>
            <el-dropdown trigger="click" @command="(cmd) => handleFolderAction(cmd, folder)">
              <span class="folder-actions" @click.stop>
                <el-icon><More /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="rename" :disabled="folder.name === '未分组'">重命名</el-dropdown-item>
                  <el-dropdown-item command="delete" class="text-danger" :disabled="folder.name === '未分组'">删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>

      <!-- 隐私空间区域 -->
      <div class="view-section">
        <div 
          class="view-header" 
          :class="{ active: currentView === 'privacy' }"
          @click="switchView('privacy')"
        >
          <el-icon><Lock /></el-icon> 隐私空间
        </div>
        <!-- 隐私空间不显示文件夹列表 -->
      </div>

      <!-- 回收站 -->
      <div class="view-section">
        <div 
          class="view-header" 
          :class="{ active: currentView === 'recycle' }"
          @click="switchView('recycle')"
        >
          <el-icon><Delete /></el-icon> 回收站
        </div>
      </div>
    </div>

  <!-- 主内容区域 -->
    <div class="main-content">
      <div class="toolbar">
        <div class="left-tools">
          <h2 class="view-title">{{ viewTitle }}</h2>
          <el-button type="primary" @click="handleCreate" v-if="currentView !== 'recycle'">
            <el-icon><Plus /></el-icon> 新建文档
          </el-button>
          <el-button type="success" plain @click="handleImport" v-if="currentView !== 'recycle'">
            <el-icon><Upload /></el-icon> 导入文档
          </el-button>
          <el-button type="warning" plain @click="handleChangePrivacyPassword" v-if="currentView === 'privacy'">
            <el-icon><Lock /></el-icon> 修改隐私密码
          </el-button>
          <el-button type="danger" plain @click="handleClearRecycle" v-if="currentView === 'recycle'">
            清空回收站
          </el-button>
        </div>
        
        <div class="right-tools">
          <el-input
            v-model="searchQuery"
            placeholder="搜索文档..."
            prefix-icon="Search"
            style="width: 200px"
            @input="handleSearch"
          />
          <el-dropdown @command="handleSort">
            <el-button>
              排序: {{ sortLabel }} <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="created_at|desc">创建时间 (倒序)</el-dropdown-item>
                <el-dropdown-item command="created_at|asc">创建时间 (正序)</el-dropdown-item>
                <el-dropdown-item command="updated_at|desc">更新时间 (倒序)</el-dropdown-item>
                <el-dropdown-item command="updated_at|asc">更新时间 (正序)</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <div class="bulk-actions" v-if="selectedDocs.size > 0 && currentView !== 'recycle'">
        <span>已选中 {{ selectedDocs.size }} 个文档</span>
        <el-button size="small" @click="selectAllDocs">{{ selectedDocs.size === documents.length ? '取消全选' : '全选当前列表' }}</el-button>
        <el-button size="small" @click="openBulkMove">移动至...</el-button>
        <el-button size="small" @click="toggleBulkPrivacy(true)" v-if="currentView !== 'privacy'">移入隐私空间</el-button>
        <el-button size="small" @click="toggleBulkPrivacy(false)" v-if="currentView === 'privacy'">移出隐私空间</el-button>
        <el-button size="small" type="danger" @click="handleBulkDelete">删除</el-button>
      </div>

  <!-- 文档列表 -->
      <div class="doc-list" v-loading="loading">
        <div v-if="documents.length === 0" class="empty-state">
          <el-empty description="暂无文档" />
        </div>
        
        <div 
          v-for="doc in documents" 
          :key="doc.id" 
          class="doc-item"
          :class="{ 'is-pinned': doc.is_pinned, 'is-selected': selectedDocs.has(doc.id) }"
          @click.self="toggleSelect(doc)"
        >
          <div class="doc-select" @click.stop>
            <el-checkbox 
              :model-value="selectedDocs.has(doc.id)" 
              @change="(checked) => setSelect(doc, checked)" 
            />
          </div>
          <div class="doc-content" @click="handlePreview(doc)">
            <div class="doc-header">
              <span class="doc-title">{{ doc.title }}</span>
              <el-tag v-if="doc.is_pinned" size="small" type="warning" effect="plain">置顶</el-tag>
            </div>
            <div class="doc-preview" v-html="highlight(doc.content)"></div>
            <div class="doc-meta">
              <span>{{ displayedTime(doc) }}</span>
            </div>
          </div>
          
          <div class="doc-actions">
            <template v-if="currentView === 'recycle'">
              <el-button link type="primary" @click="handleRestore(doc)">恢复</el-button>
              <el-button link type="danger" @click="handleDelete(doc, true)">彻底删除</el-button>
            </template>
            <template v-else>
              <el-tooltip content="置顶" placement="top" v-if="currentView !== 'privacy'">
                <el-button link @click.stop="handlePin(doc)">
                  <el-icon :class="{ 'is-active': doc.is_pinned }"><Top /></el-icon>
                </el-button>
              </el-tooltip>
              
              <el-dropdown trigger="click" @command="(cmd) => handleDocAction(cmd, doc)">
                <el-button link>
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="edit">编辑</el-dropdown-item>
                    <el-dropdown-item command="move" v-if="currentView !== 'privacy'">移动至...</el-dropdown-item>
                    <el-dropdown-item command="privacy" v-if="currentView !== 'privacy'">移入隐私空间</el-dropdown-item>
                    <el-dropdown-item command="public" v-if="currentView === 'privacy'">移出隐私空间</el-dropdown-item>
                    <el-dropdown-item command="share">分享</el-dropdown-item>
                    <el-dropdown-item divided command="delete" class="text-danger">删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
          </div>
        </div>
      </div>
    </div>

  <!-- 各类弹窗 -->
    <el-dialog v-model="previewVisible" :title="currentDoc?.title" width="70%" top="5vh">
      <div class="preview-content" v-html="currentDoc?.content"></div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleAISummary(currentDoc)">
            <el-icon><MagicStick /></el-icon> AI总结
          </el-button>
          <el-button type="primary" @click="handleEdit(currentDoc)">编辑</el-button>
          <el-button type="danger" @click="handleDelete(currentDoc)">删除</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="folderDialogVisible" :title="folderDialogTitle" width="30%">
      <el-input v-model="folderForm.name" placeholder="请输入文件夹名称" />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="folderDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitFolder">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <el-dialog v-model="moveDialogVisible" title="移动至" width="30%">
      <div class="folder-list-select">
        <div 
          v-for="folder in folders" 
          :key="folder.id"
          class="folder-select-item"
          :class="{ active: moveTargetFolderId === folder.id }"
          @click="moveTargetFolderId = folder.id"
        >
          <el-icon><Folder /></el-icon> {{ folder.name }}
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="moveDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitMove">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 隐私空间密码设置弹窗 -->
    <el-dialog 
      v-model="privacyPasswordDialogVisible" 
      title="设置隐私空间密码" 
      width="400px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <el-alert 
        type="info" 
        :closable="false" 
        style="margin-bottom: 20px"
      >
        <template #title>
          隐私空间是您的专属安全区域，所有文档内容将被加密存储。<br/>
          请设置一个强密码（至少6位），请妥善保管，忘记密码将无法恢复文档！
        </template>
      </el-alert>
      <el-form :model="privacyPasswordForm" label-width="100px">
        <el-form-item label="密码">
          <el-input 
            v-model="privacyPasswordForm.password" 
            type="password" 
            placeholder="至少6位" 
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input 
            v-model="privacyPasswordForm.confirmPassword" 
            type="password" 
            placeholder="再次输入密码" 
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="privacyPasswordDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitPrivacyPassword">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 隐私空间密码验证弹窗 -->
    <el-dialog 
      v-model="privacyVerifyDialogVisible" 
      title="验证隐私空间密码" 
      width="400px"
      :close-on-click-modal="false"
    >
      <el-alert 
        type="warning" 
        :closable="false" 
        style="margin-bottom: 20px"
      >
        您已离开隐私空间超过3分钟，请重新输入密码以继续访问。
      </el-alert>
      <el-input 
        v-model="privacyVerifyPassword" 
        type="password" 
        placeholder="请输入隐私空间密码" 
        show-password
        @keyup.enter="submitPrivacyVerify"
      />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="privacyVerifyDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitPrivacyVerify">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 修改隐私密码对话框 -->
    <el-dialog 
      v-model="changePrivacyPasswordDialogVisible" 
      title="修改隐私空间密码" 
      width="400px"
    >
      <el-form :model="changePasswordForm" label-width="100px">
        <el-form-item label="当前密码">
          <el-input v-model="changePasswordForm.oldPassword" type="password" placeholder="请输入当前密码" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="changePasswordForm.newPassword" type="password" placeholder="至少6位" show-password />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input v-model="changePasswordForm.confirmPassword" type="password" placeholder="再次输入新密码" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="changePrivacyPasswordDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitChangePrivacyPassword">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <input 
      ref="importInput" 
      type="file" 
      accept=".txt,.md,.json" 
      style="display: none" 
      @change="onImportChange"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Document, Folder, Delete, Plus, Search, ArrowDown, 
  Top, More, MoreFilled, Lock, Upload, MagicStick 
} from '@element-plus/icons-vue'
import request from '../api/request'
import dayjs from 'dayjs'
import { usePrivacyStore } from '../store'
import { 
  checkPrivacyPassword, 
  setPrivacyPassword, 
  verifyPrivacyPassword 
} from '../api/privacy'

const router = useRouter()
const route = useRoute()
const privacyStore = usePrivacyStore()
const loading = ref(false)
const documents = ref([])
const folders = ref([])
const selectedDocs = ref(new Set())
const clearSelection = () => {
  selectedDocs.value = new Set()
}
const searchQuery = ref('')
const currentView = ref('all') // 视图类型：全部/隐私/回收站
const currentFolder = ref(null)
const sortBy = ref('updated_at')
const sortOrder = ref('desc')
let searchTimer = null

// 弹窗相关状态
const previewVisible = ref(false)
const currentDoc = ref(null)
const folderDialogVisible = ref(false)
const folderDialogTitle = ref('新建文件夹')
const folderForm = ref({ id: null, name: '' })
const moveDialogVisible = ref(false)
const moveTargetFolderId = ref(null)
const docToMove = ref(null)
const isBulkMove = ref(false)
const importInput = ref(null)
const draggingIndex = ref(null)

// 隐私空间相关状态
const privacyPasswordDialogVisible = ref(false)
const privacyPasswordForm = ref({
  password: '',
  confirmPassword: ''
})
const isSettingPassword = ref(false) // 是否是首次设置密码
const privacyVerifyDialogVisible = ref(false)
const privacyVerifyPassword = ref('')
// 修改隐私密码相关状态
const changePrivacyPasswordDialogVisible = ref(false)
const changePasswordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const viewTitle = computed(() => {
  if (currentView.value === 'privacy') return '隐私空间'
  if (currentView.value === 'recycle') return '回收站'
  if (currentFolder.value) return currentFolder.value.name
  return '全部文档'
})

const sortLabel = computed(() => {
  const map = {
    'created_at': '创建时间',
    'updated_at': '更新时间'
  }
  const orderMap = { 'asc': '正序', 'desc': '倒序' }
  return `${map[sortBy.value]} (${orderMap[sortOrder.value]})`
})

// 数据获取：文档 & 文件夹
const fetchDocuments = async () => {
  loading.value = true
  try {
    const params = {
      sort_by: sortBy.value,
      order: sortOrder.value,
      q: searchQuery.value
    }
    
    if (currentView.value === 'recycle') {
      params.recycle_bin = true
    } else if (currentView.value === 'privacy') {
      params.privacy_space = true
      // 传递密码用于解密
      if (privacyStore.password) {
        params._privacy_password = privacyStore.password
      }
      // 如果选中了文件夹，只显示该文件夹下的文档
      if (currentFolder.value) {
        params.folder_id = currentFolder.value.id
      }
    } else if (currentFolder.value) {
      // 选中了具体文件夹，只显示该文件夹下的文档
      params.folder_id = currentFolder.value.id
    }
    // 否则是"全部文档"视图，不传 folder_id，后端会返回所有非隐私文档
    
    const res = await request.get('/docs/', { params })
    documents.value = res
    clearSelectionInvalid()
  } catch (error) {
    ElMessage.error('获取文档列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    fetchDocuments()
  }, 400)
}

const fetchFolders = async () => {
  // 隐私空间不使用文件夹功能
  if (currentView.value === 'privacy') {
    folders.value = []
    clearSelection()
    return
  }
  
  try {
    const isPrivacy = currentView.value === 'privacy'
    const params = { in_privacy_space: isPrivacy }
    const res = await request.get('/docs/folders', { params })
    
    // 确保"未分组"文件夹存在
    let uncategorized = res.find(f => f.name === '未分组')
    if (!uncategorized) {
      // 如果不存在则创建未分组文件夹
      try {
        uncategorized = await request.post('/docs/folders', { 
          name: '未分组',
          in_privacy_space: isPrivacy
        })
        res.push(uncategorized)
      } catch (error) {
        console.error('创建未分组文件夹失败', error)
      }
    }
    
    // 前端强制排序：未分组在最前，其他按 order 排序
    folders.value = res.sort((a, b) => {
      if (a.name === '未分组') return -1
      if (b.name === '未分组') return 1
      return a.order - b.order
    })
  } catch (error) {
    console.error('获取文件夹失败', error)
  }
}

// 列表动作：视图切换、排序、跳转
const switchView = async (view) => {
  // 如果切换到隐私空间，需要先验证
  if (view === 'privacy') {
    await handlePrivacyAccess()
    return
  }
  
  currentView.value = view
  currentFolder.value = null
  clearSelection()
  fetchFolders()
  fetchDocuments()
}

// 隐私空间访问控制
const handlePrivacyAccess = async () => {
  try {
    console.log('开始访问隐私空间，检查密码状态...')
    
    // 1. 检查是否已设置密码
    const { has_password } = await checkPrivacyPassword()
    console.log('密码检查结果:', has_password)
    
    if (!has_password) {
      // 首次进入，引导设置密码
      isSettingPassword.value = true
      privacyPasswordForm.value = { password: '', confirmPassword: '' }
      privacyPasswordDialogVisible.value = true
      return
    }
    
    // 2. 检查是否需要重新验证（超过3分钟或没有令牌）
    if (privacyStore.needsReauth()) {
      console.log('需要重新验证密码')
      // 需要输入密码验证
      privacyVerifyPassword.value = ''
      privacyVerifyDialogVisible.value = true
      return
    }
    
    // 3. 已验证，直接进入
    console.log('已验证，直接进入隐私空间')
    privacyStore.updateLastAccessTime()
    currentView.value = 'privacy'
    currentFolder.value = null
    fetchDocuments()
  } catch (error) {
    console.error('检查隐私空间状态失败:', error)
    console.error('错误详情:', error.response?.data)
    ElMessage.error(error.response?.data?.msg || '检查隐私空间状态失败')
  }
}

// 提交设置隐私空间密码
const submitPrivacyPassword = async () => {
  const { password, confirmPassword } = privacyPasswordForm.value
  
  if (!password || password.length < 6) {
    ElMessage.warning('密码长度不能少于6位')
    return
  }
  
  if (password !== confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  
  try {
    await setPrivacyPassword(password)
    ElMessage.success('隐私空间密码设置成功')
    
    // 自动验证并进入
    const { access_token } = await verifyPrivacyPassword(password)
    privacyStore.setAccessToken(access_token)
    privacyStore.setPassword(password)
    
    privacyPasswordDialogVisible.value = false
    currentView.value = 'privacy'
    currentFolder.value = null
    fetchFolders()
    fetchDocuments()
  } catch (error) {
    ElMessage.error(error.response?.data?.msg || '设置失败')
  }
}

// 提交验证隐私空间密码
const submitPrivacyVerify = async () => {
  if (!privacyVerifyPassword.value) {
    ElMessage.warning('请输入密码')
    return
  }
  
  try {
    const { access_token } = await verifyPrivacyPassword(privacyVerifyPassword.value)
    privacyStore.setAccessToken(access_token)
    privacyStore.setPassword(privacyVerifyPassword.value)
    
    ElMessage.success('验证成功')
    privacyVerifyDialogVisible.value = false
    currentView.value = 'privacy'
    currentFolder.value = null
    fetchFolders()
    fetchDocuments()
  } catch (error) {
    ElMessage.error(error.response?.data?.msg || '密码错误')
  }
}

// 打开修改隐私密码对话框
const handleChangePrivacyPassword = () => {
  changePasswordForm.value = {
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
  changePrivacyPasswordDialogVisible.value = true
}

// 提交修改隐私密码
const submitChangePrivacyPassword = async () => {
  const { oldPassword, newPassword, confirmPassword } = changePasswordForm.value
  
  if (!oldPassword) {
    ElMessage.warning('请输入当前密码')
    return
  }
  
  if (!newPassword || newPassword.length < 6) {
    ElMessage.warning('新密码长度不能少于6位')
    return
  }
  
  if (newPassword !== confirmPassword) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  
  try {
    await setPrivacyPassword(newPassword, oldPassword)
    ElMessage.success('密码修改成功')
    
    // 修改成功后，更新密码并刷新令牌
    const { access_token } = await verifyPrivacyPassword(newPassword)
    privacyStore.setAccessToken(access_token)
    privacyStore.setPassword(newPassword)
    
    changePrivacyPasswordDialogVisible.value = false
  } catch (error) {
    ElMessage.error(error.response?.data?.msg || '修改失败')
  }
}

const selectFolder = (folder) => {
  currentFolder.value = folder
  clearSelection()
  fetchDocuments()
}

const handleSort = (command) => {
  const [field, order] = command.split('|')
  sortBy.value = field
  sortOrder.value = order
  fetchDocuments()
}

const handleCreate = () => {
  // 直接跳转到创建页面，携带当前状态用于返回
  const query = {
    view: currentView.value  // 添加视图状态
  }
  if (currentFolder.value) {
    query.folderId = currentFolder.value.id
    query.folderName = currentFolder.value.name  // 用于显示
  }
  if (currentView.value === 'privacy') {
    query.privacy = 'true'
  }
  router.push({ path: '/documents/create', query })
}

const onDragStart = (event, index) => {
  draggingIndex.value = index
  event.dataTransfer.effectAllowed = 'move'
}

const onDragOver = (event) => {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
}

const onDrop = async (event, index) => {
  event.preventDefault()
  const fromIndex = draggingIndex.value
  const toIndex = index
  
  if (fromIndex === null || fromIndex === toIndex) return
  
  // 不允许移动"未分组"文件夹（它在 index 0）
  // 也不允许将其他文件夹移动到 index 0
  if (folders.value[fromIndex].name === '未分组' || folders.value[toIndex].name === '未分组') {
    return
  }
  
  // 移动数组元素
  const item = folders.value.splice(fromIndex, 1)[0]
  folders.value.splice(toIndex, 0, item)
  
  // 更新后端排序
  try {
    const updates = folders.value.map((f, idx) => ({
      id: f.id,
      order: idx
    }))
    await request.put('/docs/folders/reorder', updates)
  } catch (error) {
    ElMessage.error('排序更新失败')
    fetchFolders() // 恢复原状
  }
  
  draggingIndex.value = null
}

const handleImport = () => {
  importInput.value.click()
}

const onImportChange = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  try {
    const reader = new FileReader()
    reader.onload = async (e) => {
      try {
        const content = e.target.result
        
        // 从文件名提取标题
        const title = file.name.replace(/\.[^/.]+$/, '')
        
        // 使用导入的内容创建文档
        // 强制导入到"未分组"文件夹
        const uncategorized = folders.value.find(f => f.name === '未分组')
        const folderId = uncategorized?.id
        
        if (!folderId) {
           ElMessage.error('未找到"未分组"文件夹，无法导入')
           return
        }
        
        await request.post('/docs/', {
          title,
          content,
          folder_id: folderId,
          in_privacy_space: currentView.value === 'privacy'
        })
        
        ElMessage.success('文档导入成功')
        fetchDocuments()
      } catch (error) {
        ElMessage.error('文档导入失败')
      }
    }
    reader.readAsText(file)
  } catch (error) {
    ElMessage.error('文件读取失败')
  } finally {
    // 清空输入框以便下次导入
    event.target.value = ''
  }
}

const handlePreview = async (doc) => {
  // 先显示部分内容的预览，避免卡顿
  currentDoc.value = doc
  previewVisible.value = true
  
  try {
    const params = {}
    if (doc.in_privacy_space && privacyStore.password) {
      params._privacy_password = privacyStore.password
    }
    const fullDoc = await request.get(`/docs/${doc.id}`, { params })
    currentDoc.value = fullDoc
  } catch (err) {
    console.error('获取完整文档失败', err)
    // 失败时不报错，就显示列表里的部分内容
  }
}

const handleEdit = (doc) => {
  previewVisible.value = false
  // 带上当前视图与文件夹信息，编辑后返回原列表状态
  const query = {}
  if (currentView.value) query.view = currentView.value
  if (currentFolder.value) {
    query.folderId = currentFolder.value.id
    query.folderName = currentFolder.value.name
  }
  if (doc.in_privacy_space || currentView.value === 'privacy') {
    query.privacy = 'true'
  }
  router.push({ path: `/documents/edit/${doc.id}`, query })
}

const handleAISummary = (doc) => {
  if (!doc.content) {
    ElMessage.warning('文档内容为空，无法总结')
    return
  }
  
  // 关闭预览弹窗
  previewVisible.value = false
  
  // 将文档信息存入 sessionStorage，跳转到 AI 聊天页处理
  // 这样可以避免在当前页等待 AI 响应超时的问题，也能让用户直接看到 AI 生成过程
  try {
    sessionStorage.setItem('ai_summary_doc', JSON.stringify({
      title: doc.title,
      content: doc.content
    }))
    
    ElMessage.success('正在跳转到 AI 助手...')
    router.push({ path: '/ai-chat', query: { action: 'summary' } })
    
  } catch (e) {
    ElMessage.error('无法跳转：' + e.message)
  }
}


const toggleSelect = (doc) => {
  const next = new Set(selectedDocs.value)
  if (next.has(doc.id)) {
    next.delete(doc.id)
  } else {
    next.add(doc.id)
  }
  selectedDocs.value = next
}

const setSelect = (doc, checked) => {
  const next = new Set(selectedDocs.value)
  if (checked) {
    next.add(doc.id)
  } else {
    next.delete(doc.id)
  }
  selectedDocs.value = next
}

const selectAllDocs = () => {
  if (selectedDocs.value.size === documents.value.length) {
    clearSelection()
  } else {
    selectedDocs.value = new Set(documents.value.map(d => d.id))
  }
}

const handlePin = async (doc) => {
  try {
    await request.put(`/docs/${doc.id}`, { is_pinned: !doc.is_pinned })
    ElMessage.success(doc.is_pinned ? '已取消置顶' : '已置顶')
    fetchDocuments()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleDocAction = (cmd, doc) => {
  if (cmd === 'edit') handleEdit(doc)
  if (cmd === 'delete') handleDelete(doc)
  if (cmd === 'move') {
    docToMove.value = doc
    isBulkMove.value = false
    // 如果文档有文件夹，选中当前文件夹；否则选中第一个文件夹
    moveTargetFolderId.value = doc.folder_id || (folders.value.length > 0 ? folders.value[0].id : null)
    moveDialogVisible.value = true
  }
  if (cmd === 'privacy') togglePrivacy(doc, true)
  if (cmd === 'public') togglePrivacy(doc, false)
  if (cmd === 'share') handleShare(doc)
}

const togglePrivacy = async (doc, isPrivacy) => {
  try {
    await request.put(`/docs/${doc.id}`, { in_privacy_space: isPrivacy })
    ElMessage.success(isPrivacy ? '已移入隐私空间' : '已移出隐私空间')
    fetchDocuments()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (doc, hardDelete = false) => {
  try {
    const msg = hardDelete || currentView.value === 'privacy' 
      ? '确定要彻底删除这个文档吗？此操作无法恢复。' 
      : '确定要删除这个文档吗？它将被移入回收站。'
      
    await ElMessageBox.confirm(msg, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await request.delete(`/docs/${doc.id}`, { 
      params: { hard_delete: hardDelete } 
    })
    ElMessage.success('删除成功')
    previewVisible.value = false
    fetchDocuments()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

const handleRestore = async (doc) => {
  try {
    await request.put(`/docs/${doc.id}`, { restore: true })
    ElMessage.success('恢复成功')
    fetchDocuments()
  } catch (error) {
    ElMessage.error('恢复失败')
  }
}

const handleClearRecycle = async () => {
  try {
    await ElMessageBox.confirm('确定要清空回收站吗？所有文档将无法恢复。', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await request.delete('/docs/recycle-bin/clear')
    ElMessage.success('回收站已清空')
    fetchDocuments()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('清空失败')
  }
}

const handleShare = (doc) => {
  ElMessage.success('分享链接已复制到剪贴板 (模拟)')
}

// 文件夹管理：创建/重命名/删除
const handleCreateFolder = () => {
  folderForm.value = { id: null, name: '' }
  folderDialogTitle.value = '新建文件夹'
  folderDialogVisible.value = true
}

const handleFolderAction = (cmd, folder) => {
  if (cmd === 'rename') {
    if (folder.name === '未分组') {
      ElMessage.warning('未分组文件夹不可重命名')
      return
    }
    folderForm.value = { id: folder.id, name: folder.name }
    folderDialogTitle.value = '重命名文件夹'
    folderDialogVisible.value = true
  }
  if (cmd === 'delete') {
    if (folder.name === '未分组') {
      ElMessage.warning('未分组文件夹不可删除')
      return
    }
    ElMessageBox.confirm('确定要删除这个文件夹吗？', '提示', {
      type: 'warning'
    }).then(async () => {
      try {
        await request.delete(`/docs/folders/${folder.id}`)
        ElMessage.success('删除成功')
        if (currentFolder.value?.id === folder.id) {
          currentFolder.value = null
          currentView.value = 'all'
        }
        fetchFolders()
      } catch (error) {
        ElMessage.error(error.response?.data?.msg || '删除失败')
      }
    })
  }
}

const submitFolder = async () => {
  if (!folderForm.value.name) return
  try {
    if (folderForm.value.id) {
      await request.put(`/docs/folders/${folderForm.value.id}`, { name: folderForm.value.name })
    } else {
      const isPrivacy = currentView.value === 'privacy'
      await request.post('/docs/folders', { 
        name: folderForm.value.name,
        in_privacy_space: isPrivacy
      })
    }
    folderDialogVisible.value = false
    fetchFolders()
    ElMessage.success('操作成功')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const submitMove = async () => {
  try {
    if (isBulkMove.value) {
      const ids = Array.from(selectedDocs.value)
      if (currentView.value === 'privacy' && !privacyStore.password) {
        ElMessage.error('缺少隐私空间密码，无法移动隐私文档')
        return
      }
      await Promise.all(ids.map(id => {
        const payload = { folder_id: moveTargetFolderId.value }
        if (currentView.value === 'privacy') {
          payload._privacy_password = privacyStore.password
        }
        return request.put(`/docs/${id}`, payload)
      }))
      ElMessage.success('批量移动成功')
      clearSelection()
    } else if (docToMove.value) {
      const payload = { folder_id: moveTargetFolderId.value }
      if (docToMove.value.in_privacy_space) {
        payload._privacy_password = privacyStore.password
      }
      await request.put(`/docs/${docToMove.value.id}`, payload)
      ElMessage.success('移动成功')
    }
    moveDialogVisible.value = false
    fetchDocuments()
  } catch (error) {
    ElMessage.error('移动失败')
  }
}

const formatTime = (time) => {
  return dayjs(time).format('YYYY年 M月 D日 HH:mm:ss')
}

const escapeHtml = (str = '') => str
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;')

const highlight = (text) => {
  // Strip HTML tags first
  const plainText = (text || '').replace(/<[^>]+>/g, '')
  
  const q = (searchQuery.value || '').trim()
  if (!q) return plainText || '无内容'
  
  const safe = escapeHtml(plainText)
  if (!safe) return '无内容'
  
  try {
    const escaped = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const reg = new RegExp(escaped, 'gi')
    return safe.replace(reg, (m) => `<span class="hl">${m}</span>`)
  } catch (e) {
    return safe
  }
}

const displayedTime = (doc) => {
  // 如果按创建时间排序，则展示创建时间；否则展示更新时间
  const useCreated = sortBy.value === 'created_at'
  const ts = useCreated ? doc.created_at : doc.updated_at
  return formatTime(ts)
}

// 批量操作
const openBulkMove = () => {
  if (selectedDocs.value.size === 0) return
  isBulkMove.value = true
  moveTargetFolderId.value = currentFolder.value?.id || (folders.value[0]?.id ?? null)
  moveDialogVisible.value = true
}

const toggleBulkPrivacy = async (toPrivacy) => {
  if (selectedDocs.value.size === 0) return
  if (!toPrivacy && !privacyStore.password) {
    ElMessage.error('缺少隐私空间密码，无法移出隐私空间')
    return
  }
  try {
    await Promise.all(Array.from(selectedDocs.value).map(id => {
      const payload = { in_privacy_space: toPrivacy }
      if (!toPrivacy) {
        // 从隐私移出需要密码
        payload._privacy_password = privacyStore.password
      }
      return request.put(`/docs/${id}`, payload)
    }))
    ElMessage.success(toPrivacy ? '已移入隐私空间' : '已移出隐私空间')
    clearSelection()
    fetchDocuments()
  } catch (error) {
    ElMessage.error('批量操作失败')
  }
}

const handleBulkDelete = async () => {
  if (selectedDocs.value.size === 0) return
  try {
    await ElMessageBox.confirm('确定要删除选中文档吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await Promise.all(Array.from(selectedDocs.value).map(id => {
      return request.delete(`/docs/${id}`, { params: { hard_delete: currentView.value === 'privacy' } })
    }))
    ElMessage.success('删除成功')
    clearSelection()
    fetchDocuments()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(() => {
  // 从 URL 参数恢复状态
  const { view, folderId } = route.query
  
  if (view) {
    currentView.value = view
  }
  
  fetchFolders()
  
  // 如果有 folderId，需要等待文件夹加载后再设置
  if (folderId) {
    // 使用 nextTick 确保 folders 已加载
    setTimeout(() => {
      const folder = folders.value.find(f => f.id === parseInt(folderId))
      if (folder) {
        currentFolder.value = folder
      }
      fetchDocuments()
    }, 100)
  } else {
    fetchDocuments()
  }
})

onBeforeUnmount(() => {
  if (searchTimer) clearTimeout(searchTimer)
})

const clearSelectionInvalid = () => {
  const ids = new Set(documents.value.map(d => d.id))
  const next = new Set()
  selectedDocs.value.forEach(id => {
    if (ids.has(id)) next.add(id)
  })
  selectedDocs.value = next
}
</script>

<style scoped>
.document-container {
  display: flex;
  height: calc(100vh - 84px); /* Adjust based on layout */
  background: var(--el-bg-color-page);
}

.sidebar {
  width: 240px;
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
  padding: 20px 0;
}

.nav-item {
  padding: 10px 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--el-text-color-regular);
  transition: all 0.3s;
}

.nav-item:hover {
  background-color: var(--el-fill-color-light);
  color: var(--el-color-primary);
}

.nav-item.active {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  border-right: 3px solid var(--el-color-primary);
}

.view-section {
  margin-bottom: 10px;
}

.view-header {
  padding: 12px 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--el-text-color-regular);
  transition: all 0.3s;
  font-weight: 500;
  border-radius: 6px;
  margin: 0 10px;
}

.view-header:hover {
  background-color: var(--el-fill-color-light);
  color: var(--el-color-primary);
}

.view-header.active {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-weight: 600;
}

.folder-group {
  margin-top: 8px;
  padding-left: 10px;
}

.folder-header {
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  margin-bottom: 5px;
}

.folder-item {
  justify-content: space-between;
}

.folder-name {
  display: flex;
  align-items: center;
  gap: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.folder-actions {
  opacity: 0;
  transition: opacity 0.2s;
}

.folder-item:hover .folder-actions {
  opacity: 1;
}

.main-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background: var(--el-bg-color);
  padding: 15px;
  border-radius: 8px;
  box-shadow: var(--el-box-shadow-light);
}

.left-tools {
  display: flex;
  align-items: center;
  gap: 20px;
}

.view-title {
  margin: 0;
  font-size: 18px;
  color: var(--el-text-color-primary);
}

.right-tools {
  display: flex;
  gap: 15px;
}

.doc-list {
  flex: 1;
}

.doc-item {
  background: var(--el-bg-color);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 15px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  transition: all 0.3s;
  border: 1px solid transparent;
  cursor: pointer;
  gap: 12px;
  align-items: center;
}

.doc-item:hover {
  box-shadow: var(--el-box-shadow);
  transform: translateY(-2px);
}

.doc-item.is-pinned {
  border-color: var(--el-color-warning);
  background: var(--el-color-warning-light-9);
}

.doc-content {
  flex: 1;
}

.doc-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.doc-title {
  font-size: 16px;
  font-weight: bold;
  color: var(--el-text-color-primary);
}

.doc-preview {
  color: var(--el-text-color-secondary);
  font-size: 14px;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.5;
}

:deep(.doc-preview .hl) {
  background: #fff3cd;
  color: #d48806;
  padding: 0 2px;
  border-radius: 2px;
}

.doc-meta {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.doc-actions {
  display: flex;
  gap: 10px;
  margin-left: 20px;
}

.doc-select {
  display: flex;
  align-items: center;
}

.doc-item.is-selected {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.bulk-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: -10px 0 10px 0;
  padding: 10px 12px;
  background: var(--el-fill-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
}

/* Ensure images in preview are visible and responsive */
:deep(.preview-content img) {
  max-width: 100% !important;
  height: auto !important;
  display: block;
  margin: 10px auto;
  border-radius: 4px;
}

.preview-content {
  min-height: 400px;
  max-height: 70vh;
  overflow-y: auto;
  white-space: normal;
  word-break: break-word; /* Ensure long words break */
  line-height: 1.8;
  padding: 24px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 4px;
  color: var(--el-text-color-primary);
  font-size: 16px;
}

.folder-list-select {
  max-height: 300px;
  overflow-y: auto;
}

.folder-select-item {
  padding: 10px;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--el-text-color-regular);
}

.folder-select-item:hover {
  background: var(--el-fill-color-light);
}

.folder-select-item.active {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.text-danger {
  color: var(--el-color-danger);
}

@media (max-width: 768px) {
  .document-container {
    flex-direction: column;
    height: auto;
  }
  .sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--el-border-color-light);
    padding: 10px 0;
    flex-direction: row;
    overflow-x: auto;
    gap: 10px;
  }
  .view-section {
    min-width: 140px;
  }
  .main-content {
    padding: 10px;
  }
  .toolbar {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  .left-tools {
    flex-wrap: wrap;
    gap: 10px;
  }
  .right-tools {
    width: 100%;
    justify-content: flex-start;
    gap: 8px;
  }
  .doc-item {
    flex-direction: column;
    padding: 12px;
    gap: 8px;
  }
  .doc-actions {
    margin-left: 0;
    width: 100%;
    justify-content: flex-end;
  }
  .bulk-actions {
    flex-direction: column;
    align-items: flex-start;
    width: 100%;
  }
  .doc-header {
    flex-wrap: wrap;
  }
  .doc-meta {
    margin-top: 4px;
  }
  .right-tools .el-input {
    width: 100%;
  }
  .toolbar .left-tools .el-button {
    padding: 8px 10px;
  }
}
</style>
