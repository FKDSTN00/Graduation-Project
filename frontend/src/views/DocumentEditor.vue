<template>
  <div class="document-editor">
    <div class="editor-header">
      <el-button @click="handleBack">返回列表</el-button>
      <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
    </div>
    
    <div class="editor-content">
      <el-form :model="form" label-width="80px">
        <el-form-item label="文件夹" v-if="!isPrivacyDoc && route.query.privacy !== 'true'">
          <el-select v-model="form.folder_id" placeholder="选择文件夹" style="width: 100%">
            <el-option
              v-for="folder in folders"
              :key="folder.id"
              :label="folder.name"
              :value="folder.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="请输入文档标题" style="width: 100%" />
        </el-form-item>
        <el-form-item label="内容" class="editor-item">
          <div id="toolbar-container"></div>
          <div id="editor-container"></div>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../api/request'
import { usePrivacyStore } from '../store'
import { Document } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const privacyStore = usePrivacyStore()

const form = ref({
  title: '',
  content: '',
  folder_id: null,
  attachments: []
})
const uploadedImages = ref([]) // 记录本次编辑上传的所有图片URL
let editorInstance = null

const folders = ref([])

const saving = ref(false)
const documentId = ref(null)
const isPrivacyDoc = ref(false)

// 如果有 ID 参数，则是编辑模式
onMounted(async () => {
  // Initialize wangEditor
  if (window.wangEditor) {
    const { createEditor, createToolbar } = window.wangEditor
    
    const editorConfig = {
      placeholder: '请输入文档内容...',
      onChange(editor) {
        form.value.content = editor.getHtml()
      },
      MENU_CONF: {
        uploadImage: {
          async customUpload(file, insertFn) {
            // 使用现有的附件上传接口
            const formData = new FormData()
            formData.append('file', file)
            
            try {
              const res = await request.post('/docs/attachments', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
              })
              
              // 插入图片到编辑器
              insertFn(res.url, file.name, res.url)
              
              // 记录上传的图片
              uploadedImages.value.push(res.url)
              
              ElMessage.success('图片上传成功')
            } catch (error) {
              ElMessage.error('图片上传失败：' + (error.response?.data?.msg || error.message))
            }
          }
        }
      }
    }
    
    const editor = createEditor({
      selector: '#editor-container',
      html: form.value.content,
      config: editorConfig,
      mode: 'default'
    })
    
    const toolbarConfig = {
      toolbarKeys: [
        'headerSelect',
        'bold',
        'italic',
        'underline',
        'through',
        '|',
        'bulletedList',
        'numberedList',
        '|',
        'color',
        'bgColor',
        '|',
        'fontSize',
        'fontFamily',
        '|',
        'justifyLeft',
        'justifyCenter',
        'justifyRight',
        '|',
        'insertLink',
        'uploadImage',
        'insertTable',
        '|',
        'codeBlock',
        'blockquote',
        '|',
        'undo',
        'redo',
        'clearStyle'
      ]
    }
    
    const toolbar = createToolbar({
      editor,
      selector: '#toolbar-container',
      config: toolbarConfig,
      mode: 'default'
    })
    
    editorInstance = editor // Assign the editor instance
  }

  await fetchFolders()
  
  // 检查是否是隐私空间文档
  if (route.query.privacy === 'true') {
    isPrivacyDoc.value = true
    // 确保有隐私空间权限
    if (!privacyStore.accessToken || privacyStore.needsReauth()) {
      ElMessage.error('请先进入隐私空间')
      router.push('/documents')
      return
    }
  }
  
  if (route.params.id) {
    documentId.value = route.params.id
    await fetchDocument()
  } else {
    // 新建模式，设置默认文件夹
    if (route.query.folderId) {
      form.value.folder_id = parseInt(route.query.folderId)
    } else {
      // 默认选中"未分组"
      const uncategorized = folders.value.find(f => f.name === '未分组')
      if (uncategorized) {
        form.value.folder_id = uncategorized.id
      }
    }
  }
})

onBeforeUnmount(() => {
  if (editorInstance) {
    editorInstance.destroy()
    editorInstance = null
  }
})

const fetchFolders = async () => {
  try {
    const res = await request.get('/docs/folders')
    folders.value = res
  } catch (error) {
    console.error('获取文件夹失败:', error)
  }
}

const fetchDocument = async () => {
  try {
    // 如果有隐私密码，总是传递（让后端决定是否需要）
    const params = {}
    if (privacyStore.password) {
      params._privacy_password = privacyStore.password
    }
    
    const res = await request.get(`/docs/${documentId.value}`, { params })
    form.value.title = res.title
    form.value.content = res.content
    form.value.folder_id = res.folder_id
    isPrivacyDoc.value = res.in_privacy_space
    form.value.attachments = res.attachments || []

    if (editorInstance && res.content) {
      editorInstance.setHtml(res.content)
    }
    
    // 提取已有内容中的图片URL
    if (res.content) {
      const imgRegex = /<img[^>]+src="([^">]+)"/g
      let match
      while ((match = imgRegex.exec(res.content)) !== null) {
        if (match[1] && !uploadedImages.value.includes(match[1])) {
          uploadedImages.value.push(match[1])
        }
      }
    }
  } catch (error) {
    console.error('获取文档失败:', error)
    ElMessage.error(error.response?.data?.msg || '获取文档失败')
  }
}

const handleSave = async () => {
  if (!form.value.title) {
    ElMessage.warning('请输入文档标题')
    return
  }

  saving.value = true
  try {
    // 1. 清理未使用的图片
    const currentContent = form.value.content || ''
    const currentImages = []
    const imgRegex = /<img[^>]+src="([^">]+)"/g
    let match
    while ((match = imgRegex.exec(currentContent)) !== null) {
      if (match[1]) currentImages.push(match[1])
    }
    
    // 找出已上传但不在当前内容中的图片
    const imagesToDelete = uploadedImages.value.filter(url => !currentImages.includes(url))
    
    // 异步删除，不阻塞保存流程
    if (imagesToDelete.length > 0) {
      Promise.all(imagesToDelete.map(url => 
        request.delete('/docs/attachments', { data: { url } }).catch(e => console.error('清理图片失败:', e))
      ))
    }

    const data = { ...form.value }
    data.attachments = form.value.attachments || []
    
    // 如果是隐私空间文档，需要传递密码用于加密
    if (isPrivacyDoc.value || route.query.privacy === 'true') {
      data.in_privacy_space = true
      data._privacy_password = privacyStore.password
      
      if (!data._privacy_password) {
        ElMessage.error('隐私空间密码不可用，请重新进入隐私空间')
        handleBack()
        return
      }
    }
    
    if (documentId.value) {
      // 编辑模式 - 更新文档
      await request.put(`/docs/${documentId.value}`, data)
      ElMessage.success('文档更新成功')
    } else {
      // 创建模式 - 新建文档
      await request.post('/docs/', data)
      ElMessage.success('文档创建成功')
    }
    handleBack()
  } catch (error) {
    console.error('保存文档失败:', error)
    ElMessage.error(error.response?.data?.msg || '保存文档失败')
  } finally {
    saving.value = false
  }
}

const handleBack = () => {
  // 从 query 参数中获取返回状态
  const { view, folderId } = route.query
  
  // 构造返回路径，保持用户之前的状态
  const returnQuery = {}
  if (view) returnQuery.view = view
  if (folderId) returnQuery.folderId = folderId
  
  router.push({ path: '/documents', query: returnQuery })
}
</script>

<style scoped>
.document-editor {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 20px;
  box-sizing: border-box;
}

.editor-header {
  flex-shrink: 0;
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}

.editor-content {
  flex: 1;
  background: var(--el-bg-color);
  padding: 20px;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  width: 100%;
  max-width: 100%;
}

.editor-content :deep(.el-form) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.editor-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-bottom: 0 !important;
}

.editor-item :deep(.el-form-item__content) {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: 0 !important;
}

#editor-container {
  flex: 1;
  border: 1px solid var(--el-border-color-light);
  border-top: none;
  border-radius: 0 0 4px 4px;
  overflow-x: hidden;
  overflow-y: auto;
  width: 100%;
  min-width: 100%;
  max-width: 100%;
  max-height: 500px;
  min-height: 300px;
}

#toolbar-container {
  border: 1px solid var(--el-border-color-light);
  border-radius: 4px 4px 0 0;
  width: 100%;
  min-width: 100%;
  max-width: 100%;
}

/* wangEditor 内容区域样式 */
#editor-container :deep(.w-e-text-container) {
  width: 100% !important;
  min-width: 100% !important;
  max-width: 100% !important;
}

#editor-container :deep(.w-e-text-placeholder) {
  width: 100% !important;
}

#editor-container :deep(.w-e-scroll) {
  width: 100% !important;
  overflow-x: hidden !important;
  overflow-y: auto !important;
  max-height: 100% !important;
}

#editor-container :deep([data-slate-editor]) {
  width: 100% !important;
  word-wrap: break-word !important;
  word-break: break-word !important;
  white-space: pre-wrap !important;
  overflow-wrap: break-word !important;
}

#editor-container :deep(p),
#editor-container :deep(div),
#editor-container :deep(span) {
  word-wrap: break-word !important;
  word-break: break-word !important;
  white-space: pre-wrap !important;
  max-width: 100% !important;
}

/* 深色模式适配 */
#toolbar-container :deep(.w-e-toolbar) {
  background-color: var(--el-fill-color-lighter) !important;
  border-color: var(--el-border-color-light) !important;
}

#toolbar-container :deep(.w-e-bar-item button) {
  color: var(--el-text-color-primary) !important;
}

#toolbar-container :deep(.w-e-bar-item button:hover) {
  background-color: var(--el-fill-color) !important;
  color: var(--el-color-primary) !important;
}

#toolbar-container :deep(.w-e-bar-item-active button) {
  color: var(--el-color-primary) !important;
}

#toolbar-container :deep(.w-e-select-list) {
  background-color: var(--el-bg-color-overlay) !important;
  border-color: var(--el-border-color-light) !important;
}

#toolbar-container :deep(.w-e-select-list ul li) {
  color: var(--el-text-color-primary) !important;
}

#toolbar-container :deep(.w-e-select-list ul li:hover) {
  background-color: var(--el-fill-color) !important;
}

#editor-container :deep(.w-e-text-container) {
  background-color: var(--el-bg-color) !important;
}

#editor-container :deep([data-slate-editor]) {
  color: var(--el-text-color-primary) !important;
  background-color: var(--el-bg-color) !important;
}

#editor-container :deep(.w-e-text-placeholder) {
  color: var(--el-text-color-placeholder) !important;
}

/* 编辑器内容样式 */
#editor-container :deep(p) {
  color: var(--el-text-color-primary) !important;
}

#editor-container :deep(h1),
#editor-container :deep(h2),
#editor-container :deep(h3),
#editor-container :deep(h4),
#editor-container :deep(h5),
#editor-container :deep(h6) {
  color: var(--el-text-color-primary) !important;
}

#editor-container :deep(a) {
  color: var(--el-color-primary) !important;
}

#editor-container :deep(blockquote) {
  border-left-color: var(--el-border-color) !important;
  color: var(--el-text-color-secondary) !important;
}

#editor-container :deep(code) {
  background-color: var(--el-fill-color-light) !important;
  color: var(--el-color-danger) !important;
}

#editor-container :deep(pre) {
  background-color: var(--el-fill-color-darker) !important;
  border-color: var(--el-border-color) !important;
}

#editor-container :deep(pre code) {
  color: var(--el-text-color-primary) !important;
  background-color: transparent !important;
}

#editor-container :deep(table) {
  border-color: var(--el-border-color-light) !important;
}

#editor-container :deep(table td),
#editor-container :deep(table th) {
  border-color: var(--el-border-color-light) !important;
  background-color: var(--el-bg-color) !important;
}

#editor-container :deep(table th) {
  background-color: var(--el-fill-color-light) !important;
}


</style>
