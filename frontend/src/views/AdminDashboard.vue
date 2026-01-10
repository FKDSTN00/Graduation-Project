<template>
  <div class="admin-dashboard">
    <h2 class="page-title">{{ pageTitle }}</h2>
    <el-card class="card">
      
      <!-- 公告管理 -->
      <div v-if="activeTab === 'announcement'">
        <AnnouncementManager />
      </div>

      <!-- 工作流程看板 -->
      <div v-else-if="activeTab === 'kanban'">
        <div class="toolbar" style="justify-content: space-between;">
           <span class="hint">监控所有用户的待处理和进行中任务（按用户名排序）</span>
           <el-button type="primary" link @click="loadAdminTasks">刷新</el-button>
        </div>
        
        <div v-loading="loadingTasks">
          <div v-if="adminTasks.length === 0" style="padding: 40px 0;">
            <el-empty description="暂无活动任务" />
          </div>
          
          <div v-else class="user-tasks-container">
            <el-card 
              v-for="userGroup in adminTasks" 
              :key="userGroup.user_id" 
              class="user-task-card"
              shadow="hover"
            >
              <template #header>
                <div class="user-header">
                  <el-avatar :size="40" :src="userGroup.avatar">
                    {{ userGroup.username.charAt(0).toUpperCase() }}
                  </el-avatar>
                  <div class="user-info">
                    <div class="username">{{ userGroup.username }}</div>
                    <div class="task-count">{{ userGroup.tasks.length }} 个活动任务</div>
                  </div>
                </div>
              </template>
              
              <el-table :data="userGroup.tasks" style="width: 100%" size="small">
                <el-table-column prop="title" label="任务标题" min-width="150" show-overflow-tooltip />
                <el-table-column prop="notes" label="备注" min-width="120" show-overflow-tooltip align="center">
                  <template #default="scope">
                    <span v-if="scope.row.notes">{{ scope.row.notes }}</span>
                    <span v-else style="color: var(--el-text-color-placeholder);">-</span>
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="100" align="center">
                  <template #default="scope">
                    <el-tag :type="scope.row.status === 'in-progress' ? '' : 'warning'" size="small">
                      {{ scope.row.status === 'in-progress' ? '进行中' : '待处理' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="priority" label="优先级" width="100" align="center">
                  <template #default="scope">
                    <el-tag :type="getPriorityColor(scope.row.priority)" effect="plain" size="small">
                      {{ scope.row.priority }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="deadline" label="截止时间" width="160" align="center">
                  <template #default="scope">
                    <span :class="{ 'text-danger': isOverdue(scope.row.deadline) }">
                      {{ scope.row.deadline }}
                    </span>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>
        </div>
      </div>

      <!-- 文档监控 -->
      <div v-else-if="activeTab === 'monitor'">
        <div class="toolbar">
          <el-input v-model="monitorKeyword" placeholder="输入监控关键词" style="width: 240px" clearable @keyup.enter="addMonitorKeyword" />
          <el-button type="primary" @click="addMonitorKeyword">添加关键词</el-button>
          <el-button type="success" @click="searchDocuments" :loading="loadingMonitor" :disabled="monitorKeywords.length === 0">搜索文档</el-button>
          <div class="keyword-list" v-if="monitorKeywords.length">
            <span style="margin-right: 8px; color: var(--el-text-color-secondary);">关键词：</span>
            <el-tag
              v-for="(kw, idx) in monitorKeywords"
              :key="idx"
              closable
              @close="removeMonitorKeyword(idx)"
              style="margin-right: 8px;"
            >
              {{ kw }}
            </el-tag>
          </div>
        </div>
        
        <div v-loading="loadingMonitor" style="min-height: 200px;">
          <el-table :data="flaggedDocs" style="width: 100%" border v-if="flaggedDocs.length > 0">
            <el-table-column prop="title" label="文档标题" min-width="180" show-overflow-tooltip />
            <el-table-column prop="username" label="创建用户" width="120" align="center" />
            <el-table-column prop="matched_keywords" label="匹配关键词" width="150" align="center">
              <template #default="scope">
                <el-tag 
                  v-for="(kw, idx) in scope.row.matched_keywords" 
                  :key="idx" 
                  size="small" 
                  type="danger"
                  style="margin: 2px;"
                >
                  {{ kw }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="snippet" label="内容片段" min-width="200" show-overflow-tooltip />
            <el-table-column prop="updated_at" label="更新时间" width="160" align="center" />
            <el-table-column label="操作" width="120" align="center">
              <template #default="scope">
                <el-button size="small" type="primary" link @click="viewDocument(scope.row)">查看详情</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="请添加关键词并点击搜索" />
        </div>
        
        <!-- 文档预览对话框 -->
        <el-dialog 
          v-model="previewDialogVisible" 
          title="文档预览" 
          width="70%" 
          top="5vh"
          destroy-on-close
        >
          <div v-if="previewDoc">
            <div class="preview-header">
              <h3>{{ previewDoc.title }}</h3>
              <div class="preview-meta">
                <el-tag size="small">创建用户：{{ previewDoc.username }}</el-tag>
                <el-tag size="small" type="info" style="margin-left: 8px;">更新时间：{{ previewDoc.updated_at }}</el-tag>
                <div style="margin-top: 8px;">
                  <span style="margin-right: 8px;">匹配关键词：</span>
                  <el-tag 
                    v-for="(kw, idx) in previewDoc.matched_keywords" 
                    :key="idx" 
                    size="small" 
                    type="danger"
                    style="margin-right: 4px;"
                  >
                    {{ kw }}
                  </el-tag>
                </div>
              </div>
            </div>
            <el-divider />
            <div class="preview-content" v-html="previewDoc.content"></div>
          </div>
          <template #footer>
            <el-button type="primary" @click="previewDialogVisible = false">关闭</el-button>
          </template>
        </el-dialog>
      </div>

      <!-- 知识库 -->
      <div v-else-if="activeTab === 'knowledge'">
        <!-- 分类管理 -->
        <div class="toolbar" style="margin-bottom: 16px;">
          <el-button type="primary" @click="openCategoryDialog">添加分类</el-button>
          <el-button type="success" @click="openArticleDialog()">新建文章</el-button>
        </div>

        <!-- 分类标签 -->
        <div class="category-tabs-wrapper">
          <el-tabs v-model="activeKnowledgeCategory" @tab-change="handleKnowledgeCategoryChange">
            <el-tab-pane :label="`全部 (${totalArticleCount})`" name="all" />
            <el-tab-pane 
              v-for="(cat, index) in knowledgeCategories" 
              :key="cat.id" 
              :label="`${cat.name} (${cat.article_count})`" 
              :name="String(cat.id)"
            >
              <template #label>
                <div 
                  class="category-tab-label"
                  draggable="true"
                  @dragstart="handleDragStart(index, $event)"
                  @dragover.prevent="handleDragOver(index, $event)"
                  @drop="handleDrop(index, $event)"
                  @dragend="handleDragEnd"
                >
                  <el-icon 
                    class="edit-category-icon" 
                    @click.stop="editKnowledgeCategory(cat)"
                    title="编辑分类"
                  >
                    <Edit />
                  </el-icon>
                  <span class="category-name">{{ cat.name }} ({{ cat.article_count}})</span>
                  <el-icon 
                    class="delete-category-icon"
                    @click.stop="deleteKnowledgeCategory(cat)"
                    title="删除分类"
                  >
                    <Close />
                  </el-icon>
                </div>
              </template>
            </el-tab-pane>
          </el-tabs>
        </div>

        <!-- 文章列表 -->
        <div v-loading="loadingKnowledge">
          <el-table :data="knowledgeArticles" style="width: 100%" border>
            <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
            <el-table-column prop="category_name" label="分类" width="120" align="center" />
            <el-table-column prop="author" label="作者" width="100" align="center" />
            <el-table-column prop="updated_at" label="更新时间" width="160" align="center" />
            <el-table-column label="操作" width="180" align="center">
              <template #default="scope">
                <el-button size="small" type="primary" link @click="viewKnowledgeArticle(scope.row)">预览</el-button>
                <el-button size="small" type="warning" link @click="openArticleDialog(scope.row)">编辑</el-button>
                <el-button size="small" type="danger" link @click="deleteKnowledgeArticle(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="knowledgeArticles.length === 0 && !loadingKnowledge" description="暂无文章" />
        </div>

        <!-- 分类对话框 -->
        <el-dialog v-model="categoryDialogVisible" title="添加分类" width="400px">
          <el-form :model="categoryForm" label-width="80px">
            <el-form-item label="分类名称">
              <el-input v-model="categoryForm.name" placeholder="请输入分类名称" />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="categoryDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="submitCategory">确定</el-button>
          </template>
        </el-dialog>

        <!-- 文章编辑对话框 -->
        <el-dialog 
          v-model="articleDialogVisible" 
          :title="articleForm.id ? '编辑文章' : '新建文章'" 
          width="80%" 
          top="5vh"
          destroy-on-close
          @closed="handleArticleDialogClosed"
        >
          <el-form :model="articleForm" label-width="80px">
            <el-form-item label="文章标题">
              <el-input v-model="articleForm.title" placeholder="请输入文章标题" />
            </el-form-item>
            <el-form-item label="所属分类">
              <el-select v-model="articleForm.category_id" placeholder="请选择分类" style="width: 100%;">
                <el-option label="未分类" :value="null" />
                <el-option 
                  v-for="cat in knowledgeCategories" 
                  :key="cat.id" 
                  :label="cat.name" 
                  :value="cat.id" 
                />
              </el-select>
            </el-form-item>
            <el-form-item label="文章内容">
              <div id="knowledge-editor" class="knowledge-editor-wrapper"></div>
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="articleDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="submitArticle">保存</el-button>
          </template>
        </el-dialog>

        <!-- 文章预览对话框 -->
        <el-dialog 
          v-model="knowledgePreviewVisible" 
          :title="currentKnowledgeArticle?.title" 
          width="70%" 
          top="5vh"
        >
          <div v-if="currentKnowledgeArticle" class="article-preview">
            <div class="article-info">
              <el-tag size="small">{{ currentKnowledgeArticle.category_name }}</el-tag>
              <span class="author">作者：{{ currentKnowledgeArticle.author }}</span>
              <span class="time">更新时间：{{ currentKnowledgeArticle.updated_at }}</span>
            </div>
            <el-divider />
            <div class="article-content" v-html="currentKnowledgeArticle.content"></div>
          </div>
          <template #footer>
            <el-button @click="knowledgePreviewVisible = false">关闭</el-button>
            <el-button type="success" @click="openKnowledgeInNewTab">新标签页打开</el-button>
            <el-button type="primary" @click="editFromPreview">编辑</el-button>
          </template>
        </el-dialog>
      </div>

      <!-- 文件中心 -->
      <!-- 文件中心 -->
      <!-- 文件中心 -->
      <div v-else-if="activeTab === 'files'">
        <FileCenter :embedded="true" />
      </div>

      <!-- 日程与会议 -->
      <div v-else-if="activeTab === 'schedule'" style="height: 600px;">
        <Schedule />
      </div>

      <!-- 审批流 -->
      <div v-else-if="activeTab === 'approval'" style="height: 600px;">
        <Approval />
      </div>

      <!-- 投票与问卷 -->
      <!-- 投票与问卷 -->
      <div v-else-if="activeTab === 'vote'">
        <Votes />
      </div>

      <!-- 用户管理 -->
      <div v-else-if="activeTab === 'users'">
        <div class="toolbar">
          <el-input v-model="userKeyword" placeholder="搜索用户名/邮箱" style="width: 200px" clearable />
          <el-tree-select 
            v-model="filterDept" 
            :data="deptOptions" 
            placeholder="筛选部门" 
            node-key="id"
            :props="{ label: 'label' }"
            clearable 
            check-strictly 
            :render-after-expand="false" 
            style="width: 180px; margin-left: 8px;" 
          />
          <el-select v-model="filterRole" placeholder="筛选角色" clearable style="width: 150px; margin-left: 8px;">
             <el-option v-for="r in roleOptions" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
          <el-button :loading="loadingUsers" @click="loadUsers" style="margin-left: 8px;">刷新</el-button>
        </div>
        <el-table :data="filteredUsers" style="width: 100%" border :loading="loadingUsers">
          <el-table-column prop="username" label="用户名" width="140" />
          <el-table-column prop="email" label="邮箱" />
          <el-table-column prop="department" label="部门" width="120" />
          <el-table-column prop="role" label="角色" width="100" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.status === 'normal' ? 'success' : 'danger'">
                {{ scope.row.status === 'normal' ? '正常' : '已封禁' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="280">
            <template #default="scope">
              <el-button size="small" @click="viewUserDocs(scope.row)">查看文档</el-button>
              <el-button size="small" type="primary" link @click="openEditUser(scope.row)">编辑</el-button>
              <el-button size="small" :type="scope.row.status === 'normal' ? 'danger' : 'success'" @click="toggleBan(scope.row)">
                {{ scope.row.status === 'normal' ? '封禁' : '解封' }}
              </el-button>
              <el-button size="small" type="danger" @click="removeUser(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-dialog v-model="userEditDialogVisible" title="编辑用户" width="400px">
           <el-form :model="userEditForm" label-width="80px">
              <el-form-item label="用户名">
                 <el-input v-model="userEditForm.username" disabled />
              </el-form-item>
               <el-form-item label="部门">
                  <el-tree-select 
                    v-model="userEditForm.departmentId" 
                    :data="deptOptions" 
                    node-key="id"
                    :props="{ label: 'label' }"
                    check-strictly 
                    :render-after-expand="false" 
                    style="width: 100%"
                    clearable
                    placeholder="请选择部门（可留空）"
                  />
               </el-form-item>
               <el-form-item label="角色">
                  <el-select v-model="userEditForm.roleId" style="width: 100%">
                     <el-option v-for="r in roleOptions" :key="r.id" :label="r.name" :value="r.id" />
                  </el-select>
               </el-form-item>
           </el-form>
           <template #footer>
               <span class="dialog-footer">
                   <el-button @click="userEditDialogVisible = false">取消</el-button>
                   <el-button type="primary" @click="submitEditUser">保存</el-button>
               </span>
           </template>
        </el-dialog>
      </div>

      <!-- 留言与反馈 -->
      <!-- 留言与反馈 -->
      <div v-else-if="activeTab === 'feedback'">
        <Feedback />
      </div>

      <!-- 系统级备份与恢复 -->
      <div v-else-if="activeTab === 'backup'">
        <div class="toolbar">
          <el-button type="primary" :loading="exporting" @click="handleExportBackup">导出全量备份</el-button>
          <el-upload
            class="upload-backup"
            action="#"
            :http-request="handleImportBackup"
            :show-file-list="false"
            accept=".sql"
            style="display: inline-block; margin-left: 12px; margin-right: 12px;"
          >
            <el-button type="success">导入备份文件</el-button>
          </el-upload>
          <span class="hint">用于管理员备份与恢复整个数据库。请谨慎操作，恢复将覆盖现有数据！</span>
        </div>
        <el-alert title="操作提示" type="info" :closable="false" show-icon>
            导出操作将下载当前系统所有数据的SQL文件。导入操作将清除当前数据库并应用上传的SQL文件，此过程不可逆。
        </el-alert>
      </div>

    </el-card>

    <el-drawer v-model="docDrawerVisible" size="40%" title="用户文档预览">
      <el-table :data="currentUserDocs" style="width:100%" border>
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="folder" label="文件夹" width="140" />
        <el-table-column prop="updated_at" label="更新时间" width="200">
          <template #default="scope">{{ formatTime(scope.row.updated_at) }}</template>
        </el-table-column>
      </el-table>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import dayjs from 'dayjs'
import { fetchUsers, banUser, updateUser, deleteUser as apiDeleteUser, fetchUserDocs, fetchAdminTasks, monitorDocuments, exportBackup, importBackup, getMonitorKeywords, addMonitorKeyword as apiAddMonitorKeyword, deleteMonitorKeyword as apiDeleteMonitorKeyword } from '../api/admin'

import { getCategories, createCategory, updateCategory, deleteCategory as apiDeleteCategory, getArticles, createArticle, updateArticle, deleteArticle as apiDeleteArticle } from '../api/knowledge'
import { defineAsyncComponent } from 'vue'
import request from '../api/request'
const FileCenter = defineAsyncComponent(() => import('./Files.vue'))

const Schedule = defineAsyncComponent(() => import('./Schedule.vue'))
const Approval = defineAsyncComponent(() => import('./Approval.vue'))
const AnnouncementManager = defineAsyncComponent(() => import('./AnnouncementManager.vue'))
const Votes = defineAsyncComponent(() => import('./Votes.vue'))

const Feedback = defineAsyncComponent(() => import('./Feedback.vue'))
import { Delete, Rank, Close, Edit } from '@element-plus/icons-vue'
import { createEditor, createToolbar } from '@wangeditor/editor'
import '@wangeditor/editor/dist/css/style.css'

const route = useRoute()
const router = useRouter()

// Active Tab logic
const activeTab = computed(() => route.params.tab || 'announcement')

const titleMap = {
  announcement: '公告管理',
  kanban: '工作流程看板',
  monitor: '文档监控',
  knowledge: '知识库',
  files: '文件中心',
  schedule: '日程与会议',
  approval: '审批流',
  vote: '投票与问卷',
  users: '用户管理',
  feedback: '留言与反馈',
  backup: '系统级备份与恢复'
}

const pageTitle = computed(() => titleMap[activeTab.value] || '管理员后台')

// Users Data
const users = ref([])
const loadingUsers = ref(false)
const userKeyword = ref('')
const filterDept = ref(null)
const filterRole = ref(null)
const deptOptions = ref([])
const roleOptions = ref([])
const userEditDialogVisible = ref(false)
const userEditForm = ref({ id: null, username: '', departmentId: null, roleId: null })
const docDrawerVisible = ref(false)
const currentUserDocs = ref([])


// Monitor Data
const flaggedDocs = ref([])
const loadingMonitor = ref(false)
const monitorKeyword = ref('')
const monitorKeywords = ref([])
const previewDialogVisible = ref(false)
const previewDoc = ref(null)

// Knowledge Data
const knowledgeCategories = ref([])
const activeKnowledgeCategory = ref('all')
const knowledgeArticles = ref([])
const loadingKnowledge = ref(false)
const categoryDialogVisible = ref(false)
const categoryForm = ref({ name: '' })
const articleDialogVisible = ref(false)
const articleForm = ref({ id: null, title: '', content: '', category_id: null })
const knowledgePreviewVisible = ref(false)
const currentKnowledgeArticle = ref(null)
let knowledgeEditor = null

// 拖拽排序相关
const draggedIndex = ref(null)
const dragOverIndex = ref(null)

// Computed
const filteredUsers = computed(() => {
  if (!userKeyword.value) return users.value
  const kw = userKeyword.value.toLowerCase()
  return users.value.filter(u => u.username.toLowerCase().includes(kw) || (u.email || '').toLowerCase().includes(kw))
})

const totalArticleCount = computed(() => {
  return knowledgeCategories.value.reduce((sum, cat) => sum + cat.article_count, 0)
})

// Lifecycle
onMounted(() => {
  if (activeTab.value === 'users') {
    loadDeptAndRoles()
    loadUsers()
  }

  if (activeTab.value === 'kanban') {
    loadAdminTasks()
  }
  if (activeTab.value === 'knowledge') {
    loadKnowledgeCategories()
    loadKnowledgeArticles()
  }
  if (activeTab.value === 'monitor') {
    loadMonitorKeywords()
  }
})

onBeforeUnmount(() => {
  if (knowledgeEditor) {
    knowledgeEditor.destroy()
    knowledgeEditor = null
  }
})

// Watcher to load data when tab changes
watch(activeTab, (newTab) => {
  if (newTab === 'users' && users.value.length === 0) {
    loadUsers()
  }
  if (newTab === 'kanban') {
    loadAdminTasks()
  }
  if (newTab === 'knowledge') {
    loadKnowledgeCategories()
    loadKnowledgeArticles()
  }
  if (newTab === 'monitor') {
    loadMonitorKeywords()
  }
})

// Actions
const loadDeptAndRoles = async () => {

    try {
        const d = await request.get('/org/departments/tree')
        deptOptions.value = d
        const r = await request.get('/org/roles')
        roleOptions.value = r
    } catch(e) {}
}

const loadUsers = async () => {
  loadingUsers.value = true
  try {
    const params = {}
    if (filterDept.value) params.departmentId = filterDept.value
    if (filterRole.value) params.roleId = filterRole.value
    
    const res = await fetchUsers(params)
    users.value = res
  } catch (error) {
    ElMessage.error(error.response?.data?.msg || '加载用户失败')
  } finally {
    loadingUsers.value = false
  }
}

const openEditUser = (user) => {
    userEditForm.value = { 
        id: user.id, 
        username: user.username, 
        departmentId: user.department_id, 
        roleId: user.role_id 
    }
    userEditDialogVisible.value = true
}

const submitEditUser = async () => {
    try {
        await updateUser(userEditForm.value.id, {
            departmentId: userEditForm.value.departmentId,
            roleId: userEditForm.value.roleId
        })
        ElMessage.success('更新成功')
        userEditDialogVisible.value = false
        loadUsers()
    } catch(e) {
        ElMessage.error(e.response?.data?.msg || '更新失败')
    }
}


// Kanban Logic
const adminTasks = ref([])
const loadingTasks = ref(false)

const loadAdminTasks = async () => {
    loadingTasks.value = true
    try {
        const res = await fetchAdminTasks()
        adminTasks.value = res
    } catch (error) {
        console.error('获取所有用户任务失败', error)
        ElMessage.error('获取任务列表失败')
    } finally {
        loadingTasks.value = false
    }
}


const getPriorityColor = (p) => {
   const map = { High: 'danger', Medium: 'warning', Low: 'info' }
   return map[p] || 'info'
}

const isOverdue = (dateStr) => {
  return dayjs().isAfter(dayjs(dateStr))
}

const viewUserDocs = async (user) => {
  try {
    const docs = await fetchUserDocs(user.id)
    currentUserDocs.value = docs
    docDrawerVisible.value = true
  } catch (error) {
    ElMessage.error(error.response?.data?.msg || '获取用户文档失败')
  }
}

const toggleBan = async (user) => {
  try {
    const toBan = user.status === 'normal'
    await banUser(user.id, toBan)
    user.status = toBan ? 'banned' : 'normal'
    user.role = toBan ? 'banned' : 'user'
    ElMessage.success(toBan ? '已封禁用户' : '已解封用户')
  } catch (error) {
    ElMessage.error(error.response?.data?.msg || '操作失败')
  }
}

const removeUser = (user) => {
  ElMessageBox.confirm(`确认删除用户 ${user.username} 吗？此操作不可恢复。`, '警告', {
    type: 'warning'
  }).then(async () => {
    try {
      await apiDeleteUser(user.id)
      users.value = users.value.filter(u => u.id !== user.id)
      ElMessage.success('用户已删除')
    } catch (error) {
      ElMessage.error(error.response?.data?.msg || '删除失败')
    }
  }).catch(() => {})
}

// Monitor Actions
const loadMonitorKeywords = async () => {
  try {
    const res = await getMonitorKeywords()
    monitorKeywords.value = res.map(k => k.keyword)
  } catch (error) {
    console.error('加载监控关键词失败', error)
  }
}

const addMonitorKeyword = async () => {
  const kw = monitorKeyword.value.trim()
  if (!kw) {
    ElMessage.warning('请输入关键词')
    return
  }
  if (monitorKeywords.value.includes(kw)) {
    ElMessage.warning('关键词已存在')
    return
  }
  
  try {
    await apiAddMonitorKeyword(kw)
    monitorKeywords.value.push(kw)
    monitorKeyword.value = ''
    ElMessage.success('添加成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.msg || '添加失败')
  }
}

const removeMonitorKeyword = async (idx) => {
  const keyword = monitorKeywords.value[idx]
  try {
    // 需要找到对应的 id
    const res = await getMonitorKeywords()
    const keywordObj = res.find(k => k.keyword === keyword)
    if (keywordObj) {
      await apiDeleteMonitorKeyword(keywordObj.id)
      monitorKeywords.value.splice(idx, 1)
      if (monitorKeywords.value.length === 0) {
        flaggedDocs.value = []
      }
      ElMessage.success('删除成功')
    }
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const searchDocuments = async () => {
  if (monitorKeywords.value.length === 0) {
    ElMessage.warning('请至少添加一个关键词')
    return
  }
  
  loadingMonitor.value = true
  try {
    const res = await monitorDocuments(monitorKeywords.value)
    flaggedDocs.value = res
    ElMessage.success(`搜索完成，找到 ${res.length} 个包含关键词的文档`)
  } catch (error) {
    console.error('搜索文档失败', error)
    ElMessage.error('搜索失败，请重试')
  } finally {
    loadingMonitor.value = false
  }
}

const viewDocument = (doc) => {
  // 在对话框中预览文档
  previewDoc.value = doc
  previewDialogVisible.value = true
}

const openDocInNewTab = () => {
  if (previewDoc.value) {
    window.open(`/documents/edit/${previewDoc.value.id}`, '_blank')
  }
}

const markViolation = (doc) => {
  ElMessage.info('标记违规功能待实现')
}

const markNormal = (doc) => {
  ElMessage.info('恢复正常功能待实现')
}

// Backup Actions
const exporting = ref(false)

const handleExportBackup = async () => {
  exporting.value = true
  try {
    const res = await exportBackup()
    if (res.type === 'application/json') {
       const reader = new FileReader()
       reader.onload = () => {
           let msg = '导出失败'
           try {
             msg = JSON.parse(reader.result).msg || msg
           } catch(e) {}
           ElMessage.error(msg)
       }
       reader.readAsText(res)
       return
    }
    const url = window.URL.createObjectURL(new Blob([res]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `system_backup_${dayjs().format('YYYYMMDDHHmmss')}.sql`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    ElMessage.success('备份下载成功')
  } catch (error) {
    console.error(error)
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

const handleImportBackup = async (options) => {
   ElMessageBox.confirm('确定要导入备份吗？这将覆盖当前所有数据且不可恢复！', '高风险操作警告', {
       type: 'warning',
       confirmButtonText: '确定覆盖',
       cancelButtonText: '取消'
   }).then(async () => {
       const loadingInstance = ElLoading.service({ text: '正在恢复数据，请勿关闭页面...', background: 'rgba(0,0,0,0.7)' })
       try {
           const formData = new FormData()
           formData.append('file', options.file)
           await importBackup(formData)
           loadingInstance.close()
           ElMessage.success('恢复成功，系统即将刷新')
           setTimeout(() => {
               window.location.reload()
           }, 1500)
       } catch (error) {
           loadingInstance.close()
           console.error(error)
           ElMessage.error(error.response?.data?.msg || '恢复失败')
       }
   }).catch(() => {})
}

// Knowledge Actions
const loadKnowledgeCategories = async () => {
  try {
    const res = await getCategories()
    knowledgeCategories.value = res
  } catch (error) {
    console.error('加载分类失败', error)
  }
}

const loadKnowledgeArticles = async () => {
  loadingKnowledge.value = true
  try {
    const categoryId = activeKnowledgeCategory.value === 'all' ? null : parseInt(activeKnowledgeCategory.value)
    const res = await getArticles(categoryId)
    knowledgeArticles.value = res
  } catch (error) {
    console.error('加载文章失败', error)
    ElMessage.error('加载文章失败')
  } finally {
    loadingKnowledge.value = false
  }
}

const handleKnowledgeCategoryChange = () => {
  loadKnowledgeArticles()
}

const openCategoryDialog = () => {
  categoryForm.value = { id: null, name: '' }
  categoryDialogVisible.value = true
}

const editKnowledgeCategory = (cat) => {
  categoryForm.value = { id: cat.id, name: cat.name }
  categoryDialogVisible.value = true
}

const submitCategory = async () => {
  if (!categoryForm.value.name) {
    ElMessage.warning('请输入分类名称')
    return
  }
  try {
    if (categoryForm.value.id) {
      await updateCategory(categoryForm.value.id, { name: categoryForm.value.name })
      ElMessage.success('更新成功')
    } else {
      await createCategory(categoryForm.value)
      ElMessage.success('添加成功')
    }
    categoryDialogVisible.value = false
    loadKnowledgeCategories()
  } catch (error) {
    ElMessage.error(categoryForm.value.id ? '更新失败' : '添加失败')
  }
}

const deleteKnowledgeCategory = (cat) => {
  ElMessageBox.confirm(`确定删除分类"${cat.name}"吗？该分类下的所有文章也将被删除。`, '警告', {
    type: 'warning'
  }).then(async () => {
    try {
      await apiDeleteCategory(cat.id)
      ElMessage.success('删除成功')
      loadKnowledgeCategories()
      if (activeKnowledgeCategory.value === String(cat.id)) {
        activeKnowledgeCategory.value = 'all'
      }
      loadKnowledgeArticles()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// 拖拽排序方法
const handleDragStart = (index, event) => {
  draggedIndex.value = index
  event.dataTransfer.effectAllowed = 'move'
  event.target.style.opacity = '0.5'
}

const handleDragOver = (index, event) => {
  dragOverIndex.value = index
}

const handleDrop = async (dropIndex, event) => {
  event.preventDefault()
  
  if (draggedIndex.value === null || draggedIndex.value === dropIndex) {
    return
  }
  
  // 重新排列数组
  const items = [...knowledgeCategories.value]
  const draggedItem = items[draggedIndex.value]
  items.splice(draggedIndex.value, 1)
  items.splice(dropIndex, 0, draggedItem)
  
  // 更新order字段
  const updates = items.map((item, idx) => ({
    id: item.id,
    order: idx
  }))
  
  // 更新本地状态
  knowledgeCategories.value = items.map((item, idx) => ({
    ...item,
    order: idx
  }))
  
  // 批量更新到后端
  try {
    for (const update of updates) {
      await updateCategory(update.id, { order: update.order })
    }
    ElMessage.success('分类顺序已更新')
  } catch (error) {
    console.error('更新顺序失败', error)
    ElMessage.error('更新顺序失败')
    // 失败时重新加载
    loadKnowledgeCategories()
  }
}

const handleDragEnd = (event) => {
  event.target.style.opacity = '1'
  draggedIndex.value = null
  dragOverIndex.value = null
}

const openArticleDialog = (article = null) => {
  if (article) {
    articleForm.value = {
      id: article.id,
      title: article.title,
      content: article.content || '',
      category_id: article.category_id
    }
  } else {
    articleForm.value = {
      id: null,
      title: '',
      content: '',
      category_id: activeKnowledgeCategory.value === 'all' ? null : parseInt(activeKnowledgeCategory.value)
    }
  }
  articleDialogVisible.value = true
  setTimeout(() => {
    initKnowledgeEditor()
  }, 100)
}

const initKnowledgeEditor = () => {
  // 销毁旧实例
  if (knowledgeEditor) {
    knowledgeEditor.destroy()
    knowledgeEditor = null
  }

  if (knowledgeEditor) {
    knowledgeEditor.destroy()
    knowledgeEditor = null
  }

  // Imported from npm now, so no need to check window.wangEditor
  // const { createEditor, createToolbar } = window.wangEditor
  
  const container = document.getElementById('knowledge-editor')
  if (!container) return
  
  // 清空容器
  container.innerHTML = ''
  
  // 创建工具栏和编辑器容器
  const toolbarDiv = document.createElement('div')
  toolbarDiv.id = 'knowledge-toolbar'
  toolbarDiv.style.border = '1px solid var(--el-border-color-light)'
  toolbarDiv.style.borderRadius = '4px 4px 0 0'
  
  const editorDiv = document.createElement('div')
  editorDiv.id = 'knowledge-editor-content'
  editorDiv.style.border = '1px solid var(--el-border-color-light)'
  editorDiv.style.borderTop = 'none'
  editorDiv.style.borderRadius = '0 0 4px 4px'
  editorDiv.style.minHeight = '400px'
  editorDiv.style.maxHeight = '500px'
  editorDiv.style.overflowY = 'auto'
  
  container.appendChild(toolbarDiv)
  container.appendChild(editorDiv)
  
  // 编辑器配置
  const editorConfig = {
    placeholder: '请输入文章内容...',
    onChange(editor) {
      articleForm.value.content = editor.getHtml()
    }
  }
  
  // 创建编辑器
  knowledgeEditor = createEditor({
    selector: '#knowledge-editor-content',
    html: articleForm.value.content || '',
    config: editorConfig,
    mode: 'default'
  })
  
  // 工具栏配置（与DocumentEditor一致）
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
  
  // 创建工具栏
  createToolbar({
    editor: knowledgeEditor,
    selector: '#knowledge-toolbar',
    config: toolbarConfig,
    mode: 'default'
  })
}

const handleArticleDialogClosed = () => {
  if (knowledgeEditor) {
    try {
      knowledgeEditor.destroy()
    } catch (e) {
      console.error('销毁编辑器失败', e)
    }
    knowledgeEditor = null
  }
}

const submitArticle = async () => {
  if (!articleForm.value.title) {
    ElMessage.warning('请输入文章标题')
    return
  }
  
  if (!articleForm.value.category_id) {
    ElMessage.warning('请选择所属分类')
    return
  }
  
  // 获取编辑器内容
  if (knowledgeEditor) {
    articleForm.value.content = knowledgeEditor.getHtml()
  }
  
  try {
    const data = {
      title: articleForm.value.title,
      content: articleForm.value.content,
      category_id: articleForm.value.category_id
    }
    
    if (articleForm.value.id) {
      await updateArticle(articleForm.value.id, data)
      ElMessage.success('更新成功')
    } else {
      await createArticle(data)
      ElMessage.success('创建成功')
    }
    
    articleDialogVisible.value = false
    loadKnowledgeArticles()
    loadKnowledgeCategories()
  } catch (error) {
    ElMessage.error(articleForm.value.id ? '更新失败' : '创建失败')
  }
}

const viewKnowledgeArticle = (article) => {
  currentKnowledgeArticle.value = article
  knowledgePreviewVisible.value = true
}

const deleteKnowledgeArticle = (article) => {
  ElMessageBox.confirm(`确定删除文章"${article.title}"吗？`, '警告', {
    type: 'warning'
  }).then(async () => {
    try {
      await apiDeleteArticle(article.id)
      ElMessage.success('删除成功')
      loadKnowledgeArticles()
      loadKnowledgeCategories()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const editFromPreview = () => {
  if (currentKnowledgeArticle.value) {
    knowledgePreviewVisible.value = false
    openArticleDialog(currentKnowledgeArticle.value)
  }
}

const openKnowledgeInNewTab = () => {
  if (currentKnowledgeArticle.value) {
    const { href } = router.resolve({
      name: 'knowledge-article',
      params: { id: currentKnowledgeArticle.value.id }
    })
    window.open(href, '_blank')
  }
}

const formatTime = (val) => dayjs(val).format('YYYY-MM-DD HH:mm:ss')
</script>

<style scoped>
.admin-dashboard {
  padding: 10px;
}

.page-title {
  margin-bottom: 12px;
}

.card {
  padding: 6px 0;
  min-height: 400px;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.keyword-list .el-tag {
  margin-right: 8px;
}

.hint {
  color: var(--el-text-color-secondary);
}

.user-tasks-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.user-task-card {
  margin-bottom: 0;
}

.user-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-info .username {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.user-info .task-count {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.text-danger {
  color: var(--el-color-danger);
  font-weight: 600;
}

.preview-header h3 {
  margin: 0 0 12px 0;
  font-size: 20px;
  color: var(--el-text-color-primary);
}

.preview-meta {
  margin-bottom: 8px;
}

.preview-content {
  min-height: 300px;
  max-height: 60vh;
  overflow-y: auto;
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
  line-height: 1.8;
  font-size: 15px;
}

.preview-content :deep(img) {
  max-width: 100% !important;
  height: auto !important;
  display: block;
  margin: 12px 0;
}

.preview-content :deep(p) {
  margin: 8px 0;
}

.article-preview .article-info {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.article-content {
  min-height: 300px;
  max-height: 60vh;
  overflow-y: auto;
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
  line-height: 1.8;
  font-size: 15px;
}

.article-content :deep(img) {
  max-width: 100% !important;
  height: auto !important;
  display: block;
  margin: 12px 0;
}

.article-content :deep(p) {
  margin: 8px 0;
}

/* 知识库编辑器容器 */
.knowledge-editor-wrapper {
  min-height: 400px;
}

/* 分类标签拖拽和删除样式 */
.category-tabs-wrapper {
  position: relative;
}

.category-tab-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: move;
  user-select: none;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.3s;
}

.category-tab-label:hover {
  background-color: var(--el-fill-color-light);
}

.edit-category-icon {
  color: var(--el-text-color-secondary);
  cursor: pointer;
  font-size: 16px;
  transition: all 0.3s;
  opacity: 0.6;
}

.edit-category-icon:hover {
  color: var(--el-color-primary);
  opacity: 1;
  transform: scale(1.2);
}

.category-name {
  flex: 1;
}

.delete-category-icon {
  opacity: 0;
  transition: all 0.3s;
  color: var(--el-color-danger);
  cursor: pointer;
  font-size: 16px;
}

.delete-category-icon:hover {
  opacity: 1 !important;
  transform: scale(1.2);
  color: var(--el-color-danger);
}

.category-tab-label:hover .delete-category-icon {
  opacity: 0.7;
}

/* 知识库编辑器深色模式适配 */
.knowledge-editor-wrapper :deep(#knowledge-toolbar .w-e-toolbar) {
  background-color: var(--el-fill-color-lighter) !important;
  border-color: var(--el-border-color-light) !important;
}

.knowledge-editor-wrapper :deep(#knowledge-toolbar .w-e-bar-item button) {
  color: var(--el-text-color-primary) !important;
}

.knowledge-editor-wrapper :deep(#knowledge-toolbar .w-e-bar-item button:hover) {
  background-color: var(--el-fill-color) !important;
  color: var(--el-color-primary) !important;
}

.knowledge-editor-wrapper :deep(#knowledge-toolbar .w-e-bar-item-active button) {
  color: var(--el-color-primary) !important;
}

.knowledge-editor-wrapper :deep(#knowledge-toolbar .w-e-select-list) {
  background-color: var(--el-bg-color-overlay) !important;
  border-color: var(--el-border-color-light) !important;
}

.knowledge-editor-wrapper :deep(#knowledge-toolbar .w-e-select-list ul li) {
  color: var(--el-text-color-primary) !important;
}

.knowledge-editor-wrapper :deep(#knowledge-toolbar .w-e-select-list ul li:hover) {
  background-color: var(--el-fill-color) !important;
}

.knowledge-editor-wrapper :deep(#knowledge-editor-content .w-e-text-container) {
  background-color: var(--el-bg-color) !important;
}

.knowledge-editor-wrapper :deep(#knowledge-editor-content [data-slate-editor]) {
  color: var(--el-text-color-primary) !important;
  background-color: var(--el-bg-color) !important;
}

.knowledge-editor-wrapper :deep(#knowledge-editor-content .w-e-text-placeholder) {
  color: var(--el-text-color-placeholder) !important;
}

.knowledge-editor-wrapper :deep(#knowledge-editor-content p) {
  color: var(--el-text-color-primary) !important;
}

.knowledge-editor-wrapper :deep(#knowledge-editor-content h1),
.knowledge-editor-wrapper :deep(#knowledge-editor-content h2),
.knowledge-editor-wrapper :deep(#knowledge-editor-content h3),
.knowledge-editor-wrapper :deep(#knowledge-editor-content h4),
.knowledge-editor-wrapper :deep(#knowledge-editor-content h5),
.knowledge-editor-wrapper :deep(#knowledge-editor-content h6) {
  color: var(--el-text-color-primary) !important;
}

.knowledge-editor-wrapper :deep(#knowledge-editor-content a) {
  color: var(--el-color-primary) !important;
}

.knowledge-editor-wrapper :deep(#knowledge-editor-content blockquote) {
  border-left-color: var(--el-border-color) !important;
  color: var(--el-text-color-secondary) !important;
}

.knowledge-editor-wrapper :deep(#knowledge-editor-content code) {
  background-color: var(--el-fill-color-light) !important;
  color: var(--el-color-danger) !important;
}

.knowledge-editor-wrapper :deep(#knowledge-editor-content pre) {
  background-color: var(--el-fill-color-darker) !important;
  border-color: var(--el-border-color) !important;
}

.knowledge-editor-wrapper :deep(#knowledge-editor-content pre code) {
  color: var(--el-text-color-primary) !important;
  background-color: transparent !important;
}

.knowledge-editor-wrapper :deep(#knowledge-editor-content table) {
  border-color: var(--el-border-color-light) !important;
}

.knowledge-editor-wrapper :deep(#knowledge-editor-content table td),
.knowledge-editor-wrapper :deep(#knowledge-editor-content table th) {
  border-color: var(--el-border-color-light) !important;
  background-color: var(--el-bg-color) !important;
}

.knowledge-editor-wrapper :deep(#knowledge-editor-content table th) {
  background-color: var(--el-fill-color-light) !important;
}
</style>

