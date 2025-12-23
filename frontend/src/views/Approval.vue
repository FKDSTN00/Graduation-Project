<template>
  <div class="approval-container">
    <div class="header-section">
      <div class="title-group">
        <h2>审批流程</h2>
        <p class="subtitle">管理和查看所有的审批申请</p>
      </div>
      <el-button
        v-if="userStore.userInfo?.role === 'user'"
        type="primary"
        class="create-btn"
        @click="openCreateDialog"
      >
        <el-icon class="mr-1"><Plus /></el-icon> 发起申请
      </el-button>
    </div>

    <!-- Filters could be added here -->

    <!-- Application List -->
    <div v-loading="loading" class="list-container">
      <el-collapse v-model="activeNames">
        <el-collapse-item title="未处理" name="pending">
          <template #title>
             <span class="collapse-title">未处理 ({{ pendingApprovals.length }})</span>
          </template>
          <div v-if="pendingApprovals.length === 0" class="empty-state">
            <el-empty description="暂无未处理申请" :image-size="80" />
          </div>
          <div v-else class="grid-layout">
            <el-card
              v-for="item in pendingApprovals"
              :key="item.id"
              class="approval-card"
              shadow="hover"
              @click="openDetailDialog(item)"
            >
              <div class="card-header-custom">
                <div class="user-info">
                  <el-avatar :src="item.applicant.avatar || defaultAvatar" :size="40">
                    {{ item.applicant.username?.charAt(0).toUpperCase() }}
                  </el-avatar>
                  <div class="meta">
                    <span class="username">{{ item.applicant.username }}</span>
                    <span class="email">{{ item.applicant.email }}</span>
                  </div>
                </div>
                <el-tag :type="getStatusType(item.status)" effect="dark" class="status-tag">
                  {{ getStatusLabel(item.status) }}
                </el-tag>
              </div>
              
              <div class="card-body">
                <div class="info-row">
                  <span class="label">申请类别:</span>
                  <span class="value">{{ getTypeLabel(item.type) }}</span>
                </div>
                <div class="info-row">
                  <span class="label">提交时间:</span>
                  <span class="value">{{ formatDate(item.created_at) }}</span>
                </div>
              </div>
            </el-card>
          </div>
        </el-collapse-item>

        <el-collapse-item title="已处理" name="processed">
          <template #title>
             <div class="collapse-header-wrapper">
               <span class="collapse-title">已处理 ({{ processedApprovals.length }})</span>
               <el-button 
                 v-if="userStore.userInfo?.role === 'admin' && processedApprovals.length > 0"
                 type="danger" 
                 link 
                 size="small" 
                 @click.stop="handleClearProcessed"
               >
                 清空记录
               </el-button>
             </div>
          </template>
          <div v-if="processedApprovals.length === 0" class="empty-state">
             <el-empty description="暂无已处理申请" :image-size="80" />
          </div>
          <div v-else class="grid-layout">
            <el-card
              v-for="item in processedApprovals"
              :key="item.id"
              class="approval-card"
              shadow="hover"
              @click="openDetailDialog(item)"
            >
              <div class="card-header-custom">
                <div class="user-info">
                  <el-avatar :src="item.applicant.avatar || defaultAvatar" :size="40">
                    {{ item.applicant.username?.charAt(0).toUpperCase() }}
                  </el-avatar>
                  <div class="meta">
                    <span class="username">{{ item.applicant.username }}</span>
                    <span class="email">{{ item.applicant.email }}</span>
                  </div>
                </div>
                <el-tag :type="getStatusType(item.status)" effect="dark" class="status-tag">
                  {{ getStatusLabel(item.status) }}
                </el-tag>
              </div>
              
              <div class="card-body">
                <div class="info-row">
                  <span class="label">申请类别:</span>
                  <span class="value">{{ getTypeLabel(item.type) }}</span>
                </div>
                <div class="info-row">
                  <span class="label">提交时间:</span>
                  <span class="value">{{ formatDate(item.created_at) }}</span>
                </div>
              </div>
            </el-card>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>

    <!-- Create Application Dialog -->
    <el-dialog
      v-model="createDialogVisible"
      title="发起审批申请"
      width="550px"
      destroy-on-close
      class="custom-dialog"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" label-position="top">
        <el-form-item label="申请类别" prop="type">
          <el-select v-model="form.type" placeholder="请选择申请类别" style="width: 100%" @change="handleTypeChange">
            <el-option label="实习生转正" value="intern_conversion" />
            <el-option label="请假" value="leave" />
            <el-option label="调休" value="time_off" />
            <el-option label="出差" value="business_trip" />
            <el-option label="工资预支" value="salary_advance" />
          </el-select>
        </el-form-item>

        <template v-if="form.type">
           <!-- Dynamic Fields -->
           <el-form-item label="申请理由" prop="reason">
             <el-input type="textarea" :rows="3" v-model="form.reason" placeholder="请输入申请理由" />
           </el-form-item>

           <el-form-item v-if="form.type === 'leave'" label="申请时间" prop="timeRange">
             <el-date-picker
               v-model="form.timeRange"
               type="datetimerange"
               range-separator="至"
               start-placeholder="开始时间"
               end-placeholder="结束时间"
               style="width: 100%"
               value-format="YYYY-MM-DD HH:mm:ss"
             />
           </el-form-item>

           <template v-if="form.type === 'time_off'">
             <el-form-item label="原本工作时间" prop="originalWorkTime">
               <el-input v-model="form.originalWorkTime" placeholder="例如：本周六" />
             </el-form-item>
             <el-form-item label="想调到何时" prop="desiredTimeOff">
               <el-input v-model="form.desiredTimeOff" placeholder="例如：下周一" />
             </el-form-item>
           </template>

           <el-form-item v-if="form.type === 'salary_advance'" label="预支工期" prop="duration">
             <el-input v-model="form.duration" placeholder="例如：1个月" />
           </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitApplication">提交申请</el-button>
      </template>
    </el-dialog>

    <!-- Detail Dialog -->
    <el-dialog
      v-model="detailDialogVisible"
      title="申请详情"
      width="600px"
      class="custom-dialog"
    >
      <div v-if="selectedApproval" class="detail-content">
        <div class="detail-header">
           <el-avatar :src="selectedApproval.applicant.avatar || defaultAvatar" :size="60">
             {{ selectedApproval.applicant.username?.charAt(0).toUpperCase() }}
           </el-avatar>
           <div class="detail-user-info">
             <h3>{{ selectedApproval.applicant.username }}</h3>
             <p>{{ selectedApproval.applicant.email }}</p>
           </div>
           <div class="detail-status">
              <el-tag :type="getStatusType(selectedApproval.status)" size="large" effect="dark">
                {{ getStatusLabel(selectedApproval.status) }}
              </el-tag>
           </div>
        </div>

        <el-descriptions :column="1" border class="mt-4">
          <el-descriptions-item label="申请类别">{{ getTypeLabel(selectedApproval.type) }}</el-descriptions-item>
          <el-descriptions-item label="申请理由">{{ selectedApproval.details.reason }}</el-descriptions-item>
          
          <el-descriptions-item v-if="selectedApproval.type === 'leave'" label="时间范围">
             {{ formatTimeRange(selectedApproval.details.timeRange) }}
          </el-descriptions-item>
          
          <template v-if="selectedApproval.type === 'time_off'">
            <el-descriptions-item label="原工作时间">{{ selectedApproval.details.originalWorkTime }}</el-descriptions-item>
            <el-descriptions-item label="期望调休时间">{{ selectedApproval.details.desiredTimeOff }}</el-descriptions-item>
          </template>

          <el-descriptions-item v-if="selectedApproval.type === 'salary_advance'" label="预支工期">
            {{ selectedApproval.details.duration }}
          </el-descriptions-item>
          
          <el-descriptions-item label="申请时间">{{ formatDate(selectedApproval.created_at) }}</el-descriptions-item>
        </el-descriptions>

      </div>
      <template #footer>
        <!-- Admin Actions -->
        <div v-if="userStore.userInfo?.role === 'admin' && selectedApproval?.status === 'pending'" class="dialog-actions">
           <el-button type="danger" @click="handleAction(selectedApproval.id, 'reject')">拒绝</el-button>
           <el-button type="success" @click="handleAction(selectedApproval.id, 'approve')">同意</el-button>
        </div>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { useUserStore } from '../store'
import { createApproval, getApprovals, updateApprovalStatus, clearProcessedApprovals } from '../api/approval'
import request from '../api/request'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
dayjs.extend(utc)

const userStore = useUserStore()
const loading = ref(false)
const activeNames = ref(['pending'])
const approvals = ref([])

const pendingApprovals = computed(() => {
  return approvals.value.filter(item => item.status === 'pending')
})

const processedApprovals = computed(() => {
  return approvals.value.filter(item => item.status !== 'pending')
})

const createDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const selectedApproval = ref(null)
const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'
const submitting = ref(false)
const formRef = ref(null)

const form = reactive({
  type: '',
  reason: '',
  timeRange: [],
  originalWorkTime: '',
  desiredTimeOff: '',
  duration: ''
})

const rules = {
  type: [{ required: true, message: '请选择申请类别', trigger: 'change' }],
  reason: [{ required: true, message: '请输入申请理由', trigger: 'blur' }],
  timeRange: [{ required: true, message: '请选择时间范围', trigger: 'change' }],
  originalWorkTime: [{ required: true, message: '请输入原本工作时间', trigger: 'blur' }],
  desiredTimeOff: [{ required: true, message: '请输入想调到什么时候', trigger: 'blur' }],
  duration: [{ required: true, message: '请输入预支工期', trigger: 'blur' }]
}

const handleTypeChange = () => {
  form.reason = ''
  form.timeRange = []
  form.originalWorkTime = ''
  form.desiredTimeOff = ''
  form.duration = ''
}

const openCreateDialog = () => {
  form.type = ''
  handleTypeChange()
  createDialogVisible.value = true
}

const submitApplication = async () => {
  if (!form.type) return
  
  // Validate form
  await formRef.value.validate(async (valid, fields) => {
    if (valid) {
      submitting.value = true
      try {
        const payload = {
          type: form.type,
          details: {
            reason: form.reason,
            timeRange: form.timeRange,
            originalWorkTime: form.originalWorkTime,
            desiredTimeOff: form.desiredTimeOff,
            duration: form.duration
          }
        }
        await createApproval(payload)
        ElMessage.success('申请已提交')
        createDialogVisible.value = false
        fetchApprovals()
      } catch (error) {
        console.error(error)
        ElMessage.error(error.response?.data?.msg || '提交失败')
      } finally {
        submitting.value = false
      }
    } else {
        console.warn('Form validation failed', fields)
        ElMessage.warning('请检查输入项是否完整')
    }
  })
}

const fetchApprovals = async () => {
  loading.value = true
  try {
    const res = await getApprovals()
    // res should be the array directly if api wrapper handles "data" property, 
    // usually wrapper returns `response.data` or `response`.
    // Assuming standard wrapper that intercepts and returns data part or the full object.
    // Based on user store `res.code === 200`, it seems wrapper returns full object.
    // But `getTasks` example: `this.tasks = res`. 
    // Wait, backend returns `jsonify([...])`. So `res` is the array.
    approvals.value = res.data || res // Handle potential wrapper differences
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const openDetailDialog = (item) => {
  selectedApproval.value = item
  detailDialogVisible.value = true
}

const handleAction = async (id, action) => {
  if (selectedApproval.value?.type === 'password_reset' && action === 'approve') {
    ElMessageBox.prompt('请输入为用户重置的新密码', '重置密码', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /^.{6,}$/,
      inputErrorMessage: '密码长度至少6位',
      inputType: 'text' // Plain text to see what they are typing, or password if preferred. User usually wants to clearly see the generated pw.
    }).then(async ({ value }) => {
      try {
        await request.put(`/approval/${id}/status`, { action, new_password: value })
        ElMessage.success('已重置密码并发送邮件')
        detailDialogVisible.value = false
        fetchApprovals()
      } catch (error) {
        console.error(error)
        ElMessage.error(error.response?.data?.msg || '操作失败')
      }
    }).catch(() => {})
    return
  }

  try {
    await updateApprovalStatus(id, action)
    ElMessage.success(action === 'approve' ? '已同意该申请' : '已拒绝该申请')
    detailDialogVisible.value = false
    fetchApprovals()
  } catch (error) {
    console.error(error)
  }
}

const handleClearProcessed = () => {
  ElMessageBox.confirm(
    '确定要清空所有已处理（已通过/已拒绝）的申请记录吗？此操作不可恢复。',
    '清空确认',
    {
      confirmButtonText: '确定清空',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(async () => {
      try {
        await clearProcessedApprovals()
        ElMessage.success('已清空所有已处理记录')
        fetchApprovals()
      } catch (error) {
        console.error(error)
        ElMessage.error('清空失败')
      }
    })
    .catch(() => {})
}

// Helpers
const getStatusLabel = (status) => {
  const map = { pending: '待审批', approved: '已通过', rejected: '已拒绝' }
  return map[status] || status
}

const getStatusType = (status) => {
  const map = { pending: 'warning', approved: 'success', rejected: 'danger' }
  return map[status] || 'info'
}

const getTypeLabel = (type) => {
  const map = {
    intern_conversion: '实习生转正',
    leave: '请假',
    time_off: '调休',
    business_trip: '出差',
    salary_advance: '工资预支',
    password_reset: '重置密码'
  }
  return map[type] || type
}

const formatDate = (dateStr) => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

const formatTimeRange = (range) => {
  if (Array.isArray(range) && range.length === 2) {
    return `${range[0]} 至 ${range[1]}`
  }
  return '未指定'
}

onMounted(() => {
  fetchApprovals()
})
</script>

<style scoped>
.approval-container {
  padding: 24px;
  height: 100%;
  background-color: var(--el-bg-color);
  overflow-y: auto;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.title-group h2 {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: var(--el-text-color-primary);
}

.subtitle {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.list-container {
  min-height: 200px;
}

.grid-layout {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.approval-card {
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
}

.approval-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

.card-header-custom {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.meta {
  display: flex;
  flex-direction: column;
}

.username {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.email {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.card-body {
  border-top: 1px solid var(--el-border-color-lighter);
  padding-top: 12px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.label {
  color: var(--el-text-color-secondary);
}

.value {
  color: var(--el-text-color-primary);
  font-weight: 500;
}

/* Detail Styles */
.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.detail-user-info {
  flex: 1;
}

.detail-user-info h3 {
  margin: 0;
  font-size: 18px;
}

.detail-user-info p {
  margin: 4px 0 0;
  color: var(--el-text-color-secondary);
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* Custom spacing for dialog */
.mt-4 {
  margin-top: 24px !important;
}

.mr-1 {
  margin-right: 4px;
}

.collapse-title {
  font-weight: 600;
  font-size: 16px;
  color: var(--el-text-color-primary);
}

.empty-state {
  padding: 40px 0;
  display: flex;
  justify-content: center;
}

.collapse-header-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding-right: 12px;
}
</style>

