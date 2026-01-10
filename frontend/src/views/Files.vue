<template>
  <div class="file-center" :class="{ 'is-embedded': embedded }">
    <!-- 工具栏 -->
    <div class="toolbar">
      <!-- 面包屑导航 -->
      <div class="breadcrumbs">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item>
            <a @click="navigateTo(null)" class="breadcrumb-link">根目录</a>
          </el-breadcrumb-item>
          <el-breadcrumb-item v-for="(folder, index) in breadcrumbStack" :key="folder.id">
            <a @click="navigateTo(folder.id, index)" class="breadcrumb-link">{{ folder.name }}</a>
          </el-breadcrumb-item>
        </el-breadcrumb>
      </div>
      
      <div class="right-actions">
        <el-button 
          v-if="isAdmin" 
          type="primary" 
          @click="openCreateFolderDialog"
        >
          <el-icon><FolderAdd /></el-icon> 新建文件夹
        </el-button>
        <el-upload
          v-if="isAdmin"
          class="upload-demo"
          action="#"
          :show-file-list="false"
          :http-request="handleUpload"
          :disabled="uploading"
          accept="*" 
        >
          <el-button type="success" :loading="uploading">
            <el-icon><Upload /></el-icon> 上传文件
          </el-button>
        </el-upload>
      </div>
    </div>

    <!-- 文件列表 -->
    <div v-loading="loading" class="file-list-container">
      <el-empty v-if="!loading && combinedList.length === 0" description="暂无文件" />
      <el-table v-else :data="combinedList" style="width: 100%" @row-click="handleRowClick">
        <el-table-column label="名称" min-width="250">
          <template #default="{ row }">
            <div class="file-name-cell">
              <el-icon v-if="row.isFolder" class="file-icon folder-icon"><Folder /></el-icon>
              <el-icon v-else class="file-icon"><Document /></el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="size" label="大小" width="120">
          <template #default="{ row }">
            {{ formatSize(row.size) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="creator" label="创建者/上传者" width="150">
          <template #default="{ row }">
            {{ row.creator || row.uploader }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <div class="actions" @click.stop>
              <!-- 文件夹操作 -->
              <template v-if="row.isFolder">
                <el-button link type="primary" @click="enterFolder(row)">打开</el-button>
                <template v-if="isAdmin">
                  <el-button link type="warning" @click="openRenameDialog(row)">重命名</el-button>
                  <el-button link type="danger" @click="deleteItem(row)">删除</el-button>
                </template>
              </template>
              <!-- 文件操作 -->
              <template v-else>
                <el-button link type="primary" @click="previewFileItem(row)">预览</el-button>
                <el-button link type="primary" @click="downloadFileItem(row)">下载</el-button>
                <template v-if="isAdmin">
                  <el-button link type="warning" @click="openRenameDialog(row)">重命名</el-button>
                  <el-button link type="danger" @click="deleteItem(row)">删除</el-button>
                </template>
              </template>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 对话框：新建文件夹 -->
    <el-dialog v-model="createFolderVisible" title="新建文件夹" width="400px">
      <el-form :model="folderForm">
        <el-form-item label="文件夹名称">
          <el-input v-model="folderForm.name" placeholder="请输入名称" @keyup.enter="submitCreateFolder" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createFolderVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreateFolder">确定</el-button>
      </template>
    </el-dialog>

    <!-- 对话框：重命名 -->
    <el-dialog v-model="renameVisible" title="重命名" width="400px">
      <el-form :model="renameForm">
        <el-form-item label="新名称">
          <el-input v-model="renameForm.name" placeholder="请输入新名称" @keyup.enter="submitRename" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="renameVisible = false">取消</el-button>
        <el-button type="primary" @click="submitRename">确定</el-button>
      </template>
    </el-dialog>

    <!-- 对话框：文档预览 -->
    <el-dialog 
      v-model="previewVisible" 
      :title="currentPreviewFile.name" 
      width="80%" 
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div v-loading="previewLoading" class="preview-container">
        <div v-if="currentPreviewFile.type === 'docx'" ref="docxPreviewRef" class="docx-preview"></div>
        <div v-else-if="['txt', 'html'].includes(currentPreviewFile.type)" class="text-preview">
          <iframe :src="currentPreviewFile.url" frameborder="0" style="width: 100%; height: 600px;"></iframe>
        </div>
        <div v-else-if="['md', 'markdown'].includes(currentPreviewFile.type)" class="markdown-preview">
             <div class="markdown-body" v-html="currentPreviewFile.details"></div>
        </div>
        <div v-else-if="currentPreviewFile.type === 'pdf'" class="pdf-preview">
          <!-- 使用 vue-pdf-embed 替代 iframe -->
          <vue-pdf-embed :source="currentPreviewFile.url" />
        </div>
        <div v-else-if="['jpg', 'jpeg', 'png', 'gif'].includes(currentPreviewFile.type)" class="image-preview" style="text-align: center;">
          <img :src="currentPreviewFile.url" style="max-width: 100%; max-height: 80vh;" />
        </div>
        <div v-else class="unsupported-preview">
          <el-empty description="此文件类型暂不支持在线预览">
            <el-button type="primary" @click="window.open(currentPreviewFile.url, '_blank')">在新窗口打开</el-button>
          </el-empty>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Folder, Document, FolderAdd, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import { renderAsync } from 'docx-preview'
import VuePdfEmbed from 'vue-pdf-embed'
// import 'vue-pdf-embed/dist/style/index.css'

// 手动设置 pdfjs worker
import * as pdfjsLib from 'pdfjs-dist'
// 这里是一个 trick，利用 URL 构造 worker script，因为直接 import worker 可能有路径问题
// 或者直接使用 cdn (用户不允许)，或者使用 vite 显式 worker import
// 为了兼容离线，我们需要确保 worker 是本地资源。
// 在 Vite 中，可以 import workerUrl from 'pdfjs-dist/build/pdf.worker?url'
import pdfWorker from 'pdfjs-dist/build/pdf.worker.js?url'
pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorker

import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css' // 或者其他主题

import { getFiles, createFolder, uploadFile, updateFolder, updateFile, deleteFolder, deleteFile, previewFile, downloadFile } from '../api/files'
import request from '../api/request'

const props = defineProps({
  embedded: {
    type: Boolean,
    default: false
  }
})

// 状态
const loading = ref(false)
const uploading = ref(false)
const currentFolderId = ref(null)
const files = ref([])
const folders = ref([])
const breadcrumbStack = ref([]) // 存储面包屑路径对象 {id, name}

// 预览相关状态
const previewVisible = ref(false)
const previewLoading = ref(false)
const currentPreviewFile = ref({ name: '', url: '', type: '' })
const docxPreviewRef = ref(null)

// 用户权限 (安全版)
const isAdmin = computed(() => {
  try {
    const userInfoStr = localStorage.getItem('userInfo')
    if (!userInfoStr) return false
    const userInfo = JSON.parse(userInfoStr)
    return userInfo.role === 'admin'
  } catch (e) {
    console.warn('UserInfo parse check error', e)
    return false
  }
})

// 表单状态
const createFolderVisible = ref(false)
const folderForm = ref({ name: '' })

const renameVisible = ref(false)
const renameForm = ref({ id: null, name: '', type: '' })

// 组合列表（文件夹在前）
const combinedList = computed(() => {
  const folderItems = folders.value.map(f => ({ ...f, isFolder: true }))
  const fileItems = files.value.map(f => ({ ...f, isFolder: false }))
  return [...folderItems, ...fileItems]
})

// 加载数据
const loadData = async (folderId = null) => {
  loading.value = true
  try {
    const res = await getFiles(folderId)
    folders.value = res.folders || []
    files.value = res.files || []
    
    if (folderId === null) {
      breadcrumbStack.value = []
    }
  } catch (error) {
    console.error('加载文件列表失败 - 详细错误:', error)
    console.error('错误响应:', error.response)
    console.error('错误数据:', error.response?.data)
    console.error('错误状态:', error.response?.status)
    ElMessage.error(`加载失败: ${error.response?.data?.error || error.response?.data?.msg || error.message || '未知错误'}`)
  } finally {
    loading.value = false
  }
}

// 导航
const enterFolder = (folder) => {
  currentFolderId.value = folder.id
  breadcrumbStack.value.push({ id: folder.id, name: folder.name })
  loadData(folder.id)
}

const navigateTo = (folderId, index = -1) => {
  currentFolderId.value = folderId
  if (folderId === null) {
    breadcrumbStack.value = []
  } else if (index !== -1) {
    breadcrumbStack.value = breadcrumbStack.value.slice(0, index + 1)
  }
  loadData(folderId)
}

const handleRowClick = (row) => {
  if (row.isFolder) {
    enterFolder(row)
  }
}

// 文件夹操作
const openCreateFolderDialog = () => {
  folderForm.value.name = ''
  createFolderVisible.value = true
}

const submitCreateFolder = async () => {
  if (!folderForm.value.name) return
  try {
    await createFolder({
      name: folderForm.value.name,
      parent_id: currentFolderId.value
    })
    ElMessage.success('创建成功')
    createFolderVisible.value = false
    loadData(currentFolderId.value)
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

// 文件操作
const handleUpload = async (options) => {
  const formData = new FormData()
  formData.append('file', options.file)
  if (currentFolderId.value) {
    formData.append('parent_id', currentFolderId.value)
  }
  
  uploading.value = true
  try {
    await uploadFile(formData)
    ElMessage.success('上传成功')
    loadData(currentFolderId.value)
  } catch (error) {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

// 预览文件
const previewFileItem = async (file) => {
  try {
    const res = await previewFile(file.id)
    if (!res.url) {
      ElMessage.warning('获取预览链接失败')
      return
    }

    currentPreviewFile.value = {
      name: file.name,
      url: res.url,
      type: file.type
    }

    // 对于 docx 文件，使用 docx-preview 库渲染
    if (file.type === 'docx') {
      previewVisible.value = true
      previewLoading.value = true
      
      try {
        // Switch back to Backend Proxy to avoid Vite proxy dependency
        // This is more robust as it uses internal Docker network
        // Note: Backend route is /api/files/files/<id>/proxy, so we need double 'files' path segment
        const blob = await request.get(`/files/files/${file.id}/proxy`, { responseType: 'blob' })
        
        // Check if we got a JSON error response masquerading as a blob
        if (blob.type === 'application/json') {
            const text = await blob.text()
            const errorData = JSON.parse(text)
            throw new Error(errorData.error || '下载失败')
        }

        // Diagnostic: Check if we received XML/HTML (MinIO error)
        if (blob.type.includes('xml') || blob.type.includes('html')) {
             const text = await blob.text()
             console.error('Proxy returned XML/HTML:', text)
             throw new Error(`代理返回了非文件数据 (${blob.type}): ${text.substring(0, 200)}`)
        }
        
        // Diagnostic: Check ZIP Header (PK = 50 4B)
        const headerBuffer = await blob.slice(0, 2).arrayBuffer()
        const headerView = new Uint8Array(headerBuffer)
        if (headerView[0] !== 0x50 || headerView[1] !== 0x4B) {
            // Check for OLE2 signature (legacy .doc)
            if (headerView[0] === 0xD0 && headerView[1] === 0xCF) {
                 throw new Error('该文件似乎是旧版 Word (.doc) 格式（尽管后缀是 .docx）。网页预览仅支持标准 .docx 格式，请下载后查看或转换为 .docx 后上传。')
            }
            
            const text = await blob.text() // Read as text to see if it's an error message
            console.error('Invalid ZIP header:', headerView, text)
            // Show start of text to help debug
            throw new Error(`文件数据头无效 (Hex: ${headerView[0].toString(16)} ${headerView[1].toString(16)}). 可能不是有效的 DOCX 文件. 内容预览: ${text.substring(0, 50)}`)
        }
        
        const arrayBuffer = await blob.arrayBuffer()
        
        // Wait for DOM update
        await new Promise(resolve => setTimeout(resolve, 100))
        
        // 使用 docx-preview 渲染
        if (docxPreviewRef.value) {
          await renderAsync(arrayBuffer, docxPreviewRef.value, null, {
            className: 'docx-wrapper',
            inWrapper: true,
            ignoreWidth: false,
            ignoreHeight: false,
            ignoreFonts: false,
            breakPages: true,
            ignoreLastRenderedPageBreak: true,
            experimental: true,
            trimXmlDeclaration: true,
            useBase64URL: true,
            renderHeaders: true,
            renderFooters: true,
            renderFootnotes: true,
            renderEndnotes: true
          })
        }
      } catch (error) {
        console.error('渲染 docx 失败:', error)
        let msg = error.message
        
        // Try to parse parsing JSON error from Blob response
        if (error.response && error.response.data instanceof Blob) {
           try {
              const text = await error.response.data.text()
              const json = JSON.parse(text)
              if (json.error) msg = json.error
           } catch(e) {}
        }
        
        ElMessage.error(`文档渲染失败: ${msg}`)
        previewVisible.value = false
      } finally {
        previewLoading.value = false
      }
    } else if (file.type === 'md' || file.type === 'markdown') {
        // Markdown 预览
        currentPreviewFile.value.details = '加载中...'
        previewVisible.value = true
        previewLoading.value = true
        try {
            const response = await fetch(res.url)
            const text = await response.text()
            // 配置 marked 高亮
            marked.setOptions({
              highlight: function(code, lang) {
                const language = hljs.getLanguage(lang) ? lang : 'plaintext';
                return hljs.highlight(code, { language }).value;
              },
              langPrefix: 'hljs language-'
            })
            currentPreviewFile.value.details = marked.parse(text)
        } catch(e) {
            ElMessage.error('Markdown 加载失败')
        } finally {
            previewLoading.value = false
        }
    } else if (['xlsx', 'pptx', 'doc', 'xls', 'ppt'].includes(file.type)) {
       // 其他 Office 文件暂不支持在线渲染，直接打开
       window.open(res.url, '_blank')
    } else if (['txt', 'html', 'pdf', 'jpg', 'jpeg', 'png', 'gif'].includes(file.type)) {
      // 其他支持的文件类型，在对话框中预览
      previewVisible.value = true
    } else {
      // 不支持的文件类型，在新窗口打开
      window.open(res.url, '_blank')
    }
  } catch (error) {
    console.error('预览失败:', error)
    ElMessage.error('无法预览')
  }
}

// 下载
const downloadFileItem = async (file) => {
  try {
    const res = await downloadFile(file.id)
    if (res.url) {
      // 直接打开下载链接，MinIO 会返回 Content-Disposition: attachment
      window.open(res.url, '_blank')
    } else {
      ElMessage.warning('获取下载链接失败')
    }
  } catch (error) {
    ElMessage.error('无法下载')
  }
}

// 重命名
const openRenameDialog = (item) => {
  renameForm.value = {
    id: item.id,
    name: item.name,
    type: item.isFolder ? 'folder' : 'file'
  }
  renameVisible.value = true
}

const submitRename = async () => {
  if (!renameForm.value.name) return
  try {
    if (renameForm.value.type === 'folder') {
      await updateFolder(renameForm.value.id, { name: renameForm.value.name })
    } else {
      await updateFile(renameForm.value.id, { name: renameForm.value.name })
    }
    ElMessage.success('重命名成功')
    renameVisible.value = false
    loadData(currentFolderId.value)
  } catch (error) {
    ElMessage.error('重命名失败')
  }
}

// 删除
const deleteItem = (item) => {
  ElMessageBox.confirm(`确定删除${item.isFolder ? '文件夹' : '文件'} "${item.name}" 吗？`, '提示', {
    type: 'warning'
  }).then(async () => {
    try {
      if (item.isFolder) {
        await deleteFolder(item.id)
      } else {
        await deleteFile(item.id)
      }
      ElMessage.success('删除成功')
      loadData(currentFolderId.value)
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

// 格式化
const formatSize = (bytes) => {
  if (bytes === 0 || !bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatTime = (time) => {
  if (!time) return '-'
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

// 初始化
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.file-center {
  padding: 20px;
  background: var(--el-bg-color);
  border-radius: 8px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.file-center.is-embedded {
  padding: 0;
  box-shadow: none;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 10px;
}

.right-actions {
  display: flex;
  gap: 10px;
}

.breadcrumbs {
  font-size: 14px;
}

.breadcrumb-link {
  cursor: pointer;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.breadcrumb-link:hover {
  color: var(--el-color-primary);
}

.file-list-container {
  flex: 1;
  overflow: auto;
}

.file-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.file-icon {
  font-size: 20px;
  color: var(--el-text-color-secondary);
}

.folder-icon {
  color: #E6A23C; /* 文件夹黄色 */
}

.actions {
  display: flex;
  gap: 8px;
}

.upload-demo {
  display: inline-block;
}

/* 预览对话框样式 */
.preview-container {
  min-height: 400px;
  max-height: 80vh;
  overflow: auto;
}

.docx-preview {
  padding: 20px;
  background: #fff;
}

/* docx-preview 库的样式优化 */
.preview-container :deep(.docx-wrapper) {
  background: white;
  padding: 30px;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

.preview-container :deep(.docx-wrapper > section.docx) {
  background: white;
  margin-bottom: 10px;
  box-shadow: 0 0 5px rgba(0,0,0,0.1);
  padding: 20px;
}

.text-preview, .pdf-preview {
  width: 100%;
  min-height: 600px;
}

.unsupported-preview {
  padding: 40px;
  text-align: center;
}
</style>







