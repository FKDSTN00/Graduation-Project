<template>
  <div class="schedule-container">
    <el-row :gutter="20" style="height: 100%">
      <!-- 左侧日历 -->
      <el-col :span="16" class="calendar-col">
        <el-card shadow="hover" class="calendar-card">
          <el-calendar v-model="currentDate" ref="calendarRef">
            <template #date-cell="{ data }">
              <div class="date-cell" :class="{ 'is-selected': data.isSelected }">
                <div class="date-text">{{ data.day.split('-').slice(2).join('') }}</div>
                <div class="events-dots">
                  <span v-for="(item, index) in getDayEvents(data.day)" :key="index" class="event-dot" :class="item.type"></span>
                </div>
              </div>
            </template>
          </el-calendar>
        </el-card>
      </el-col>

      <!-- 右侧详情 -->
      <el-col :span="8" class="detail-col">
        <el-card shadow="hover" class="detail-card">
          <template #header>
            <div class="detail-header">
              <span class="current-date-title">{{ formatDate(currentDate) }}</span>
              <div class="header-actions">
                <el-button type="primary" size="small" @click="openCreateDialog('schedule')">创建日程</el-button>
                <el-button type="success" size="small" @click="openCreateDialog('meeting')" v-if="isAdmin">创建会议</el-button>
              </div>
            </div>
          </template>

          <div class="events-list">
            <el-empty v-if="currentDayEvents.length === 0" description="暂无日程安排" />
            <div v-else class="event-items">
              <div v-for="event in currentDayEvents" :key="event.id + event.type" class="event-item" @click="openViewDialog(event)">
                <div class="event-time">
                  {{ formatTime(event.start_time) }} - {{ formatTime(event.end_time) }}
                </div>
                <div class="event-content">
                  <div class="event-title">
                    <el-tag size="small" :type="event.type === 'schedule' ? 'primary' : 'success'" effect="dark" style="margin-right: 5px; flex-shrink: 0;">
                      {{ event.type === 'schedule' ? '日程' : '会议' }}
                    </el-tag>
                    <span class="title-text">{{ event.title }}</span>
                  </div>
                  <div class="event-desc" v-if="event.description">{{ event.description }}</div>
                  <div class="event-meta" v-if="event.remind_minutes > 0">
                    <el-icon><Bell /></el-icon> 提前 {{ formatRemindTime(event.remind_minutes) }} 通知
                  </div>
                </div>
                <div class="event-actions" v-if="event.user_id === currentUserId">
                  <el-button type="primary" link :icon="Edit" @click.stop="openEditDialog(event)"></el-button>
                  <el-button type="danger" link :icon="Delete" @click.stop="handleDelete(event)"></el-button>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 创建/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
      @closed="resetForm"
    >
      <el-form :model="form" label-width="80px" :rules="rules" ref="formRef">
        <el-form-item label="类型" v-if="!isEdit">
          <el-radio-group v-model="form.type" disabled>
            <el-radio label="schedule">日程</el-radio>
            <el-radio label="meeting">会议</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="名称" prop="title">
          <el-input v-model="form.title" placeholder="请输入事件名称" />
        </el-form-item>

        <el-form-item label="时间" prop="timeRange">
          <el-date-picker
            v-model="form.timeRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
            :default-time="defaultTime"
          />
        </el-form-item>

        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" rows="3" placeholder="请输入详情描述" />
        </el-form-item>
        
        <el-form-item label="会议链接" v-if="form.type === 'meeting'">
           <el-input v-model="form.meeting_link" placeholder="例如 Zoom/腾讯会议 链接" />
        </el-form-item>

        <el-form-item label="提前通知">
          <el-select v-model="form.remind_minutes" placeholder="请选择">
            <el-option label="不通知" :value="0" />
            <el-option label="5分钟前" :value="5" />
            <el-option label="15分钟前" :value="15" />
            <el-option label="30分钟前" :value="30" />
            <el-option label="1小时前" :value="60" />
            <el-option label="2小时前" :value="120" />
            <el-option label="1天前" :value="1440" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 查看详情弹窗 -->
    <el-dialog
      v-model="viewDialogVisible"
      title="事件详情"
      width="500px"
    >
      <div v-if="currentViewEvent">
        <h3 style="margin-top:0; word-break: break-all;">{{ currentViewEvent.title }}</h3>
        <el-tag size="small" :type="currentViewEvent.type === 'schedule' ? 'primary' : 'success'" style="margin-bottom: 10px;">
            {{ currentViewEvent.type === 'schedule' ? '日程' : '会议' }}
        </el-tag>
        <p><strong>时间：</strong>{{ formatFullTime(currentViewEvent.start_time) }} - {{ formatFullTime(currentViewEvent.end_time) }}</p>
        <p v-if="currentViewEvent.meeting_link"><strong>会议链接：</strong><a :href="currentViewEvent.meeting_link" target="_blank">{{ currentViewEvent.meeting_link }}</a></p>
        <div style="margin-top: 10px; white-space: pre-wrap; word-break: break-all;">{{ currentViewEvent.description || '无描述' }}</div>
        <div v-if="currentViewEvent.remind_minutes > 0" style="margin-top: 10px; color: #E6A23C; font-size: 12px;">
            <el-icon><Bell /></el-icon> 提前 {{ formatRemindTime(currentViewEvent.remind_minutes) }} 通知
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="viewDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Calendar, Bell, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import { getEvents, createSchedule, updateSchedule, deleteSchedule, createMeeting, updateMeeting, deleteMeeting } from '../api/schedule'

// 状态
const currentDate = ref(new Date())
const events = ref([])
const isAdmin = computed(() => {
  const userStr = localStorage.getItem('userInfo')
  if (userStr) {
    const user = JSON.parse(userStr)
    return user.role === 'admin'
  }
  return false
})
const currentUserId = computed(() => {
  const userStr = localStorage.getItem('userInfo')
  if (userStr) {
    const user = JSON.parse(userStr)
    return user.id
  }
  return null
})

// 表单状态
const dialogVisible = ref(false)
const submitting = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const form = ref({
  id: null,
  type: 'schedule',
  title: '',
  description: '',
  timeRange: [],
  remind_minutes: 0,
  remind_minutes: 0,
  meeting_link: ''
})

const viewDialogVisible = ref(false)
const currentViewEvent = ref({})

const openViewDialog = (event) => {
    currentViewEvent.value = event
    viewDialogVisible.value = true
}

const formatFullTime = (iso) => dayjs(iso).format('YYYY-MM-DD HH:mm')

const defaultTime = [
  new Date(2000, 1, 1, 9, 0, 0),
  new Date(2000, 1, 1, 10, 0, 0),
]

const rules = {
  title: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  timeRange: [{ required: true, message: '请选择时间范围', trigger: 'change' }]
}

const dialogTitle = computed(() => {
  const action = isEdit.value ? '编辑' : '创建'
  const typeName = form.value.type === 'schedule' ? '日程' : '会议'
  return `${action}${typeName}`
})

// 加载数据
// 这里为了简单，每次加载当前日期前后的数据，或者加载所有数据
// 优化：加载当前展示月份的数据
const loadEvents = async () => {
    // 获取当前日历视图的范围稍微麻烦一点，因为el-calendar没有直接暴露出范围
    // 我们简单加载当前月份前后3个月的数据
    const d = dayjs(currentDate.value)
    const start_date = d.subtract(1, 'month').startOf('month').format('YYYY-MM-DD')
    const end_date = d.add(1, 'month').endOf('month').format('YYYY-MM-DD')
    
    try {
        const res = await getEvents({ start_date, end_date })
        events.value = res
    } catch(err) {
        console.error(err)
        ElMessage.error('加载日程失败')
    }
}

watch(() => currentDate.value, () => {
    loadEvents()
}, { immediate: true }) // 实际上el-calendar切换年月时currentDate会变，但可能需要去抖动

// 获取特定日期的事件
const getDayEvents = (dayStr) => {
    return events.value.filter(e => {
        const start = dayjs(e.start_time).format('YYYY-MM-DD')
        return start === dayStr
    })
}

// 当前选中日期的事件
const currentDayEvents = computed(() => {
    const dayStr = dayjs(currentDate.value).format('YYYY-MM-DD')
    return getDayEvents(dayStr)
})

// 格式化函数
const formatDate = (date) => dayjs(date).format('YYYY年MM月DD日')
const formatTime = (isoStr) => dayjs(isoStr).format('HH:mm')
const formatRemindTime = (mins) => {
    if (mins < 60) return `${mins}分钟`
    if (mins < 1440) return `${Math.floor(mins/60)}小时`
    return `${Math.floor(mins/1440)}天`
}

// 操作逻辑
const openCreateDialog = (type) => {
    isEdit.value = false
    form.value = {
        id: null,
        type: type,
        title: '',
        description: '',
        timeRange: [
            dayjs(currentDate.value).hour(9).minute(0).second(0).format('YYYY-MM-DD HH:mm:ss'),
            dayjs(currentDate.value).hour(10).minute(0).second(0).format('YYYY-MM-DD HH:mm:ss')
        ],
        remind_minutes: 0,
        meeting_link: ''
    }
    dialogVisible.value = true
}

const openEditDialog = (event) => {
    isEdit.value = true
    form.value = {
        id: event.id,
        type: event.type,
        title: event.title,
        description: event.description,
        timeRange: [event.start_time, event.end_time], // ISO string works with element plus? no, needs format usually
        remind_minutes: event.remind_minutes,
        meeting_link: event.meeting_link
    }
    // element-plus date picker needs specific format matching value-format
    form.value.timeRange = [
         dayjs(event.start_time).format('YYYY-MM-DD HH:mm:ss'),
         dayjs(event.end_time).format('YYYY-MM-DD HH:mm:ss')
    ]
    
    dialogVisible.value = true
}

const handleDelete = async (event) => {
    try {
        await ElMessageBox.confirm('确定要删除这个事件吗？', '提示', { type: 'warning' })
        if (event.type === 'schedule') {
            await deleteSchedule(event.id)
        } else {
            await deleteMeeting(event.id)
        }
        ElMessage.success('删除成功')
        loadEvents()
    } catch(err) {
        if (err !== 'cancel') ElMessage.error('删除失败')
    }
}

const submitForm = async () => {
    if (!formRef.value) return
    await formRef.value.validate(async (valid) => {
        if (valid) {
            submitting.value = true
            try {
                const payload = {
                    title: form.value.title,
                    description: form.value.description,
                    start_time: form.value.timeRange[0],
                    end_time: form.value.timeRange[1],
                    remind_minutes: form.value.remind_minutes,
                    meeting_link: form.value.meeting_link
                }
                
                if (isEdit.value) {
                    if (form.value.type === 'schedule') {
                        await updateSchedule(form.value.id, payload)
                    } else {
                        await updateMeeting(form.value.id, payload)
                    }
                    ElMessage.success('更新成功')
                } else {
                    if (form.value.type === 'schedule') {
                        await createSchedule(payload)
                    } else {
                        await createMeeting(payload)
                    }
                    ElMessage.success('创建成功')
                }
                dialogVisible.value = false
                loadEvents()
            } catch(err) {
                console.error(err)
                ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
            } finally {
                submitting.value = false
            }
        }
    })
}

const resetForm = () => {
    if (formRef.value) formRef.value.resetFields()
}

</script>

<style scoped>
.schedule-container {
  height: 100%;
  padding: 10px;
  background-color: var(--el-bg-color-page);
}

.calendar-col {
  height: 100%;
}

.calendar-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.calendar-card :deep(.el-card__body) {
    flex: 1;
    overflow: auto;
    padding: 0;
}

/* 调整日历单元格高度以适应内容 */
:deep(.el-calendar-table .el-calendar-day) {
    height: 80px; 
    padding: 5px;
}

.date-text {
    font-weight: bold;
    margin-bottom: 4px;
}

.events-dots {
    display: flex;
    flex-wrap: wrap;
    gap: 3px;
}

.event-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
}
.event-dot.schedule { background-color: var(--el-color-primary); }
.event-dot.meeting { background-color: var(--el-color-success); }


.detail-col {
  height: 100%;
}

.detail-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.detail-card :deep(.el-card__body) {
    flex: 1;
    overflow: auto;
}

.detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.current-date-title {
    font-size: 18px;
    font-weight: bold;
}

.event-items {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.event-item {
    border-left: 4px solid var(--el-border-color);
    padding-left: 12px;
    padding-right: 80px; /* 为操作按钮留出空间 */
    position: relative;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--el-border-color-lighter);
    cursor: pointer;
    overflow: hidden;
}
.event-item:hover {
    background-color: var(--el-fill-color-light);
}

.event-time {
    font-size: 13px;
    color: var(--el-text-color-secondary);
    margin-bottom: 4px;
}

.event-title {
    font-size: 16px;
    font-weight: 500;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
}

.event-desc {
    font-size: 14px;
    color: var(--el-text-color-regular);
    margin-bottom: 4px;
    white-space: nowrap;
    overflow: hidden; 
    text-overflow: ellipsis;
}

.event-meta {
    font-size: 12px;
    color: var(--el-color-warning);
    display: flex;
    align-items: center;
    gap: 4px;
}

.event-actions {
    position: absolute;
    right: 0;
    top: 0;
}

.title-text {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
</style>
