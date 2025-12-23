<template>
  <div class="votes-container">
    <div class="header-section">
      <div class="title-group">
        <h2>投票与问卷</h2>
        <p class="subtitle">参与投票或通过问卷反馈意见</p>
      </div>
      <el-button
        v-if="userStore.userInfo?.role === 'admin'"
        type="primary"
        @click="openCreateDialog"
      >
        <el-icon class="mr-1"><Plus /></el-icon> 发起投票
      </el-button>
    </div>

    <div v-loading="loading" class="vote-list">
      <div v-if="votes.length === 0" class="empty-state">
        <el-empty description="暂无进行中的投票" />
      </div>

      <div v-else class="grid-layout">
        <el-card
          v-for="vote in votes"
          :key="vote.id"
          class="vote-card"
          shadow="hover"
        >
          <template #header>
            <div class="card-header">
              <span class="vote-title">{{ vote.title }}</span>
              <div class="header-actions">
                <el-tag :type="vote.is_active ? 'success' : 'info'" effect="dark" size="small">
                  {{ vote.is_active ? '进行中' : '已结束' }}
                </el-tag>
                <el-button
                  v-if="vote.user_voted_key || !vote.is_active || userStore.userInfo?.role === 'admin'"
                  type="primary"
                  size="small"
                  @click="showChart(vote)"
                >
                  <el-icon><PieChart /></el-icon> 可视化
                </el-button>
                <el-button
                  v-if="userStore.userInfo?.role === 'admin'"
                  type="danger"
                  size="small"
                  icon="Delete"
                  circle
                  @click="handleDelete(vote.id)"
                />
              </div>
            </div>
            <div class="card-meta">
              <span>{{ vote.total_count }} 人参与</span>
              <span v-if="vote.end_time">截止: {{ formatDate(vote.end_time) }}</span>
            </div>
          </template>

          <div class="vote-options">
            <div
              v-for="opt in vote.options"
              :key="opt.key"
              class="option-item"
              :class="{ 'voted': vote.user_voted_key === opt.key }"
              @click="handleVote(vote, opt.key)"
            >
              <div class="option-header">
                 <span class="option-label">{{ opt.label }}</span>
                 <span v-if="vote.user_voted_key || !vote.is_active" class="option-percent">
                   {{ opt.percent }}% ({{ opt.count }}票)
                 </span>
              </div>
              
              <div class="progress-bar-bg">
                 <div
                   class="progress-bar-fill"
                   :style="{ width: (vote.user_voted_key || !vote.is_active || userStore.userInfo?.role === 'admin') ? opt.percent + '%' : '0%' }"
                   :class="{ 'is-selected': vote.user_voted_key === opt.key }"
                 ></div>
              </div>
              
              <div v-if="vote.user_voted_key === opt.key" class="voted-mark">
                <el-icon><Check /></el-icon> 已投
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- Chart Dialog -->
    <el-dialog
      v-model="chartDialogVisible"
      :title="currentChart?.title + ' - 投票结果'"
      width="600px"
      destroy-on-close
    >
      <div ref="chartContainer" style="width: 100%; height: 400px;"></div>
      <template #footer>
        <el-radio-group v-model="chartType" @change="renderChart">
          <el-radio-button label="pie">饼状图</el-radio-button>
          <el-radio-button label="bar">柱状图</el-radio-button>
        </el-radio-group>
      </template>
    </el-dialog>

    <!-- Create Vote Dialog -->
    <el-dialog
      v-model="createDialogVisible"
      title="发起新投票"
      width="500px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="投票标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入投票主题" />
        </el-form-item>
        
        <el-form-item label="截止时间" prop="end_time">
          <el-date-picker
            v-model="form.end_time"
            type="datetime"
            placeholder="选择截止时间 (可选)"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="投票选项">
           <div v-for="(opt, index) in form.options" :key="index" class="option-input-row">
             <el-input v-model="opt.label" :placeholder="`选项 ${index + 1}`" />
             <el-button
               v-if="form.options.length > 2"
               type="danger"
               icon="Minus"
               circle
               plain
               @click="removeOption(index)"
             />
           </div>
           <el-button type="primary" link icon="Plus" @click="addOption" class="mt-2">添加选项</el-button>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitCreate">发起投票</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Plus, Check, Delete, Minus, PieChart } from '@element-plus/icons-vue'
import { useUserStore } from '../store'
import { getVotes, createVote, submitVote, deleteVote } from '../api/notice'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import * as echarts from 'echarts'

const userStore = useUserStore()
const loading = ref(false)
const votes = ref([])
const createDialogVisible = ref(false)
const submitting = ref(false)
const formRef = ref(null)

// Chart
const chartDialogVisible = ref(false)
const currentChart = ref(null)
const chartType = ref('pie')
const chartContainer = ref(null)
let chartInstance = null

const form = reactive({
  title: '',
  end_time: null,
  options: [
    { label: '' },
    { label: '' }
  ]
})

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }]
}

const fetchVotes = async () => {
  loading.value = true
  try {
    const res = await getVotes()
    votes.value = res // Assuming wrapper returns data directly
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  form.title = ''
  form.end_time = null
  form.options = [{ label: '' }, { label: '' }]
  createDialogVisible.value = true
}

const addOption = () => {
  form.options.push({ label: '' })
}

const removeOption = (index) => {
  form.options.splice(index, 1)
}

const submitCreate = async () => {
  if (!form.title) {
    ElMessage.warning('请输入标题')
    return
  }
  const validOptions = form.options.filter(o => o.label.trim())
  if (validOptions.length < 2) {
     ElMessage.warning('至少需要两个有效选项')
     return
  }
  
  submitting.value = true
  try {
    const payload = {
      title: form.title,
      end_time: form.end_time ? dayjs(form.end_time).format() : null,
      options: validOptions.map((o, idx) => ({
        key: 'opt_' + idx + '_' + Date.now(),
        label: o.label
      }))
    }
    await createVote(payload)
    ElMessage.success('发起成功')
    createDialogVisible.value = false
    fetchVotes()
  } catch (error) {
    console.error(error)
    ElMessage.error('发起失败')
  } finally {
    submitting.value = false
  }
}

const handleVote = async (vote, optionKey) => {
  if (!vote.is_active) {
    ElMessage.warning('投票已结束')
    return
  }
  if (userStore.userInfo?.role === 'admin') {
    ElMessage.warning('管理员不能参与投票')
    return
  }
  if (vote.user_voted_key) {
    ElMessage.warning('您已参与过该投票')
    return
  }
  
  try {
    await submitVote(vote.id, optionKey)
    ElMessage.success('投票成功')
    fetchVotes()
  } catch (error) {
    console.error(error)
    ElMessage.error(error.response?.data?.error || '投票失败')
  }
}

const handleDelete = (id) => {
  ElMessageBox.confirm('确定删除该投票吗？', '警告', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteVote(id)
      ElMessage.success('已删除')
      fetchVotes()
    } catch (error) {
       ElMessage.error('删除失败')
    }
  })
}

const formatDate = (date) => {
  return dayjs(date).format('MM-DD HH:mm')
}

const showChart = (vote) => {
  currentChart.value = vote
  chartDialogVisible.value = true
  setTimeout(() => {
    renderChart()
  }, 100)
}

const renderChart = () => {
  if (!chartContainer.value) return
  
  if (chartInstance) {
    chartInstance.dispose()
  }
  
  chartInstance = echarts.init(chartContainer.value)
  
  const data = currentChart.value.options.map(opt => ({
    name: opt.label,
    value: opt.count
  }))
  
  let option = {}
  
  if (chartType.value === 'pie') {
    option = {
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c}票 ({d}%)'
      },
      legend: {
        orient: 'horizontal',
        bottom: '0%'
      },
      series: [
        {
          name: '投票结果',
          type: 'pie',
          radius: '60%',
          data: data,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          },
          label: {
            formatter: '{b}: {d}%'
          }
        }
      ]
    }
  } else {
    option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      xAxis: {
        type: 'category',
        data: data.map(d => d.name)
      },
      yAxis: {
        type: 'value',
        name: '票数'
      },
      series: [
        {
          name: '票数',
          type: 'bar',
          data: data.map(d => d.value),
          itemStyle: {
            color: '#409EFF'
          },
          label: {
            show: true,
            position: 'top'
          }
        }
      ]
    }
  }
  
  chartInstance.setOption(option)
}

onMounted(() => {
  fetchVotes()
})
</script>

<style scoped>
.votes-container {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
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

.grid-layout {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 24px;
}

.vote-card {
  border-radius: 12px;
  border: 1px solid var(--el-border-color-light);
  transition: all 0.3s;
}

.vote-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.vote-title {
  font-weight: 600;
  font-size: 16px;
  line-height: 1.4;
  color: var(--el-text-color-primary);
  flex: 1;
  margin-right: 12px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-meta {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  display: flex;
  justify-content: space-between;
}

.vote-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.option-item {
  position: relative;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color-page);
  cursor: pointer;
  transition: all 0.2s;
  overflow: hidden;
}

.option-item:hover {
  border-color: var(--el-color-primary-light-5);
}

.option-item.voted {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.option-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  position: relative;
  z-index: 2;
}

.option-label {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.option-percent {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.progress-bar-bg {
  height: 6px;
  background: var(--el-border-color-lighter);
  border-radius: 3px;
  overflow: hidden;
  position: relative;
  z-index: 2;
}

.progress-bar-fill {
  height: 100%;
  background: var(--el-color-primary);
  border-radius: 3px;
  transition: width 0.6s ease;
}

.progress-bar-fill.is-selected {
  background: var(--el-color-success);
}

.voted-mark {
  position: absolute;
  top: 8px;
  right: 8px;
  color: var(--el-color-success);
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  display: none; /* Hidden by default, showing status via styles above */
}

/* User inputs in dialog */
.option-input-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.mt-2 {
  margin-top: 8px;
}

.mr-1 {
  margin-right: 4px;
}
</style>
