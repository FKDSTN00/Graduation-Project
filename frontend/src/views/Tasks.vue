<template>
  <div class="tasks-page">
    <div class="page-header">
      <h2>任务管理</h2>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon> 新建任务
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-card class="stats-card" shadow="hover">
      <div class="stats-content">
        <div class="stats-info">
          <div class="stats-item">
            <span class="label">总任务</span>
            <span class="value">{{ stats.total }}</span>
          </div>
          <el-divider direction="vertical" />
          <div class="stats-item">
            <span class="label">已完成</span>
            <span class="value success">{{ stats.completed }}</span>
          </div>
          <el-divider direction="vertical" />
          <div class="stats-item">
            <span class="label">进行中</span>
            <span class="value primary">{{ stats.inProgress }}</span>
          </div>
          <el-divider direction="vertical" />
          <div class="stats-item">
            <span class="label">待处理</span>
            <span class="value warning">{{ stats.pending }}</span>
          </div>
        </div>
        <div class="progress-section">
          <span class="label">完成进度</span>
          <el-progress 
            :percentage="stats.percentage" 
            :status="stats.percentage === 100 ? 'success' : ''"
            :stroke-width="15"
            style="width: 300px"
          />
        </div>
      </div>
    </el-card>

    <!-- 任务列表 -->
    <el-card class="list-card">
      <el-tabs v-model="filterStatus">
        <el-tab-pane label="全部" name="all" />
        <el-tab-pane label="待处理" name="pending" />
        <el-tab-pane label="进行中" name="in-progress" />
        <el-tab-pane label="已完成" name="completed" />
      </el-tabs>

      <el-table :data="filteredTasks" style="width: 100%" v-loading="loading">
        <el-table-column width="60">
          <template #default="scope">
            <el-checkbox 
              :model-value="scope.row.status === 'completed'" 
              @change="toggleStatus(scope.row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="title" label="任务标题" min-width="150">
          <template #default="scope">
            <span :class="{ 'completed-text': scope.row.status === 'completed' }">{{ scope.row.title }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="notes" label="备注" min-width="150" show-overflow-tooltip align="center" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusLabel(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="100" align="center">
          <template #default="scope">
            <el-tag :type="getPriorityType(scope.row.priority)" effect="plain">
              {{ scope.row.priority }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="deadline" label="截止时间" width="180" align="center">
          <template #default="scope">
             <span :class="{ 'overdue': isOverdue(scope.row) }">
               <el-icon><Calendar /></el-icon> {{ scope.row.deadline }}
             </span>
          </template>
        </el-table-column>
        <el-table-column label="关联文档" width="100" align="center">
           <template #default="scope">
             <el-popover
                v-if="scope.row.relatedDocs && scope.row.relatedDocs.length > 0"
                placement="left"
                title="关联文档"
                :width="250"
                trigger="hover"
             >
               <template #reference>
                 <el-button link type="primary">查看({{ scope.row.relatedDocs.length }})</el-button>
               </template>
               <ul class="related-docs-list">
                 <li v-for="doc in scope.row.relatedDocs" :key="doc.id">
                   <el-link type="primary" :underline="false" @click="$router.push(`/documents/edit/${doc.id}`)">
                     {{ doc.title }}
                   </el-link>
                 </li>
               </ul>
             </el-popover>
             <span v-else>-</span>
           </template>
        </el-table-column>
        <el-table-column label="操作" width="150" align="center">
          <template #default="scope">
            <el-button 
              type="primary" 
              link 
              icon="Edit" 
              @click="handleEdit(scope.row)"
            >编辑</el-button>
            <el-button 
              type="danger" 
              link 
              icon="Delete" 
              @click="handleDelete(scope.row)"
            >删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-empty v-if="filteredTasks.length === 0" description="暂无任务" />
    </el-card>

    <!-- 新建/编辑任务弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑任务' : '新建任务'"
      width="600px"
      destroy-on-close
    >
      <el-form :model="form" ref="formRef" :rules="rules" label-width="80px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入任务标题" />
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="form.priority" placeholder="请选择优先级" style="width: 100%">
            <el-option label="High (高)" value="High" />
            <el-option label="Medium (中)" value="Medium" />
            <el-option label="Low (低)" value="Low" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止时间" prop="deadline">
          <el-date-picker
            v-model="form.deadline"
            type="datetime"
            placeholder="选择截止时间"
            value-format="YYYY-MM-DD HH:mm"
            style="width: 100%"
            :disabled-date="disabledDate"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" placeholder="请输入备注说明（可选）" />
        </el-form-item>
        <el-form-item label="关联文档">
          <div class="doc-selector">
            <el-select 
              v-model="selectedFolderId" 
              placeholder="选择文件夹" 
              style="width: 100%; margin-bottom: 12px"
              @change="handleFolderChange"
            >
              <el-option label="全部文档" :value="null" />
              <el-option 
                v-for="folder in folders" 
                :key="folder.id" 
                :label="folder.name" 
                :value="folder.id" 
              />
            </el-select>
            <el-select 
              v-model="form.relatedDocs" 
              placeholder="选择关联文档 (可多选)" 
              style="width: 100%" 
              multiple 
              value-key="id"
              collapse-tags
              collapse-tags-tooltip
            >
              <el-option
                v-for="doc in folderDocs"
                :key="doc.id"
                :label="doc.title"
                :value="doc"
              />
            </el-select>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitTask">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useTaskStore } from '../store'
import { Plus, Calendar, Delete, Edit } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import request from '../api/request'

const taskStore = useTaskStore()
const { stats } = storeToRefs(taskStore)
const filterStatus = ref('all')
const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref(null)
const isEditing = ref(false)
const editingTaskId = ref(null)

const form = ref({
  title: '',
  priority: 'Medium',
  deadline: '',
  notes: '',
  relatedDocs: []
})

const rules = {
  title: [{ required: true, message: '请输入任务标题', trigger: 'blur' }],
  priority: [{ required: true, message: '请选择优先级', trigger: 'change' }],
  deadline: [{ required: true, message: '请选择截止时间', trigger: 'change' }]
}

// 关联文档相关
const folders = ref([])
const selectedFolderId = ref(null)
const folderDocs = ref([])

const loadFolders = async () => {
  try {
    const res = await request.get('/docs/folders')
    folders.value = res.sort((a,b) => a.order - b.order)
    loadDocs()
  } catch (error) {
    console.error('加载文件夹失败', error)
  }
}

onMounted(async () => {
  taskStore.fetchTasks()
  // 加载文件夹，用于选择文档
  loadFolders()
})

const loadDocs = async () => {
  try {
    const params = {}
    if (selectedFolderId.value) {
      params.folder_id = selectedFolderId.value
    }
    const res = await request.get('/docs/', { params })
    folderDocs.value = res
  } catch (error) {
    console.error('加载文档失败', error)
  }
}

const handleFolderChange = () => {
  loadDocs()
}

const filteredTasks = computed(() => {
  let tasks = taskStore.tasks
  if (filterStatus.value !== 'all') {
    tasks = tasks.filter(t => t.status === filterStatus.value)
  }
  // Sort by deadline asc (earliest first)
  return [...tasks].sort((a, b) => {
    if (!a.deadline) return 1
    if (!b.deadline) return -1
    return dayjs(a.deadline).valueOf() - dayjs(b.deadline).valueOf()
  })
})

const getPriorityType = (p) => {
  const map = { High: 'danger', Medium: 'warning', Low: 'info' }
  return map[p] || 'info'
}

const getStatusType = (s) => {
  const map = { pending: 'warning', 'in-progress': '', completed: 'success' }
  return map[s] || 'info'
}

const getStatusLabel = (s) => {
  const map = { pending: '待处理', 'in-progress': '进行中', completed: '已完成' }
  return map[s] || s
}

const isOverdue = (task) => {
  if (task.status === 'completed') return false
  return dayjs().isAfter(dayjs(task.deadline))
}

// 禁用过去日期 (Allow today, disable yesterday and before)
const disabledDate = (time) => {
  return time.getTime() < new Date().setHours(0, 0, 0, 0)
}

const openCreateDialog = () => {
  isEditing.value = false
  editingTaskId.value = null
  form.value = {
    title: '',
    priority: 'Medium',
    deadline: dayjs().format('YYYY-MM-DD HH:mm'),
    notes: '',
    relatedDocs: []
  }
  selectedFolderId.value = null
  if (folders.value.length === 0) {
      loadFolders()
  } else {
      loadDocs() 
  }
  dialogVisible.value = true
}

const handleEdit = (task) => {
  isEditing.value = true
  editingTaskId.value = task.id
  form.value = {
    title: task.title,
    priority: task.priority,
    deadline: task.deadline,
    notes: task.notes || '',
    relatedDocs: task.relatedDocs || []
  }
  selectedFolderId.value = null
  if (folders.value.length === 0) {
      loadFolders()
  } else {
      loadDocs() 
  }
  dialogVisible.value = true
}

const submitTask = async () => {
  if (!formRef.value) return
  await formRef.value.validate((valid) => {
    if (valid) {
      if (dayjs(form.value.deadline).isBefore(dayjs())) {
          ElMessage.warning('截止时间不能早于当前时间')
          return 
      }
      if (isEditing.value) {
        taskStore.updateTask(editingTaskId.value, { ...form.value })
        ElMessage.success('更新成功')
      } else {
        taskStore.addTask({ ...form.value })
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
    }
  })
}

const toggleStatus = (task) => {
  taskStore.toggleTaskStatus(task.id)
}

const handleDelete = (task) => {
  ElMessageBox.confirm('确定要删除该任务吗？', '提示', {
    type: 'warning'
  }).then(() => {
    taskStore.deleteTask(task.id)
    ElMessage.success('已删除')
  }).catch(() => {})
}
</script>

<style scoped>
.tasks-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.tasks-page h2 {
  margin: 0;
  font-size: 24px;
}

.stats-card {
  margin-bottom: 20px;
}

.stats-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
}

.stats-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stats-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stats-item .label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.stats-item .value {
  font-size: 24px;
  font-weight: bold;
}

.stats-item .value.success { color: var(--el-color-success); }
.stats-item .value.primary { color: var(--el-color-primary); }
.stats-item .value.warning { color: var(--el-color-warning); }

.progress-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.completed-text {
  text-decoration: line-through;
  color: var(--el-text-color-secondary);
}

.overdue {
  color: var(--el-color-danger);
  font-weight: bold;
}

.related-docs-list {
  padding: 0 10px;
  margin: 0;
  list-style: none;
}
.related-docs-list li {
  margin-bottom: 4px;
}
</style>
