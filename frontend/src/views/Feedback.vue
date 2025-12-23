<template>
  <div class="feedback-container">
    <div class="header-section">
      <div class="title-group">
        <h2>留言与反馈</h2>
        <p class="subtitle">分享您的想法，反馈问题，或参与社区讨论</p>
      </div>
      <el-button
        v-if="userStore.userInfo?.role !== 'admin'"
        type="primary"
        @click="openCreateDialog"
      >
        <el-icon class="mr-1"><EditPen /></el-icon> 发布留言
      </el-button>
    </div>

    <!-- Filter Bar -->
    <div class="filter-bar">
      <el-radio-group v-model="filterCategory" @change="fetchFeedbacks">
        <el-radio-button label="all">全部</el-radio-button>
        <el-radio-button label="message">留言</el-radio-button>
        <el-radio-button label="bug">Bug反馈</el-radio-button>
        <el-radio-button label="suggestion">建议</el-radio-button>
      </el-radio-group>
      
      <el-input
        v-model="keyword"
        placeholder="搜索关键词"
        style="width: 240px"
        clearable
        @clear="fetchFeedbacks"
        @keyup.enter="fetchFeedbacks"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
    </div>

    <!-- Post List -->
    <div v-loading="loading" class="post-list">
      <div v-if="feedbacks.length === 0" class="empty-state">
        <el-empty description="暂无相关帖子" />
      </div>

      <div v-else class="post-items">
        <div
          v-for="post in feedbacks"
          :key="post.id"
          class="post-item"
          @click="openDetail(post)"
        >
          <div class="post-main">
             <div class="post-header">
               <el-tag size="small" :type="getCategoryType(post.category)">{{ getCategoryLabel(post.category) }}</el-tag>
               <h3 class="post-title">{{ post.title }}</h3>
             </div>
             <p class="post-summary">{{ post.content }}</p>
             <div class="post-meta">
               <div class="user-meta">
                 <el-avatar :size="20" :src="post.avatar">{{ post.username?.charAt(0).toUpperCase() }}</el-avatar>
                 <span>{{ post.username }}</span>
               </div>
               <span class="divider">|</span>
               <span>发布于 {{ formatDate(post.created_at) }}</span>
               <span class="divider">|</span>
               <span><el-icon><View /></el-icon> {{ post.view_count }}</span>
               <template v-if="userStore.userInfo?.role === 'admin' || userStore.userInfo?.id === post.user_id">
                 <span class="divider">|</span>
                 <span class="delete-action" @click.stop="handleDeleteFeedback(post, $event)">
                   <el-icon><Delete /></el-icon> 删除
                 </span>
               </template>
             </div>
          </div>
          <div class="post-stats">
            <div class="reply-badge" @click.stop="handleLikeFeedback(post)" title="点赞">
              <el-icon :class="{ 'is-liked': post.is_liked }"><Star /></el-icon>
              <span>{{ post.like_count }}</span>
            </div>
            <div class="reply-badge" title="评论">
              <el-icon><ChatLineSquare /></el-icon>
              <span>{{ post.reply_count }}</span>
            </div>
            <span class="last-reply" v-if="post.last_reply_at">
              最后回复 {{ formatTimeAgo(post.last_reply_at) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Detail Dialog -->
    <el-dialog
      v-model="detailVisible"
      width="800px"
      top="5vh"
      destroy-on-close
      :title="currentFeedback?.title"
      class="feedback-detail-dialog"
    >
      <div v-if="currentFeedback" class="detail-content">
        <!-- Main Post -->
        <div class="main-post">
           <div class="post-author-row">
             <div class="author-info">
               <el-avatar :size="40" :src="currentFeedback.avatar">{{ currentFeedback.username?.charAt(0).toUpperCase() }}</el-avatar>
               <div>
                 <div class="author-name">{{ currentFeedback.username }}</div>
                 <div class="post-time">{{ formatDate(currentFeedback.created_at) }} · {{ currentFeedback.view_count }} 浏览</div>
               </div>
             </div>
             <el-tag :type="getCategoryType(currentFeedback.category)">{{ getCategoryLabel(currentFeedback.category) }}</el-tag>
           </div>
           
           <div class="post-body">
             {{ currentFeedback.content }}
           </div>
           
           <div class="post-actions-bar">
             <el-button :type="currentFeedback.is_liked ? 'primary' : ''" :plain="!currentFeedback.is_liked" @click="handleLikeFeedback(currentFeedback)">
               <el-icon class="mr-1"><Star /></el-icon> {{ currentFeedback.is_liked ? '已赞' : '点赞' }} {{ currentFeedback.like_count }}
             </el-button>
           </div>
        </div>

        <el-divider content-position="left">评论 ({{ currentFeedback.replies.length }})</el-divider>

        <!-- Reply List -->
        <div class="reply-list">
          <div v-for="reply in currentFeedback.replies" :key="reply.id" class="reply-item">
            <el-avatar :size="32" :src="reply.avatar" class="reply-avatar">
              {{ reply.username?.charAt(0).toUpperCase() }}
            </el-avatar>
            <div class="reply-content-wrapper">
              <div class="reply-header">
                <span class="reply-author" :class="{ 'is-admin': reply.role === 'admin' }">
                  {{ reply.username }}
                  <el-tag v-if="reply.role === 'admin'" size="small" type="danger" effect="plain" class="admin-badge">管理员</el-tag>
                </span>
                <div class="reply-actions-top">
                   <div class="like-action mr-2" @click="handleLikeReply(reply)">
                     <el-icon :class="{ 'is-liked': reply.is_liked }"><Star /></el-icon>
                     <span>{{ reply.like_count || 0 }}</span>
                   </div>
                   <span class="reply-time">{{ formatDate(reply.created_at) }}</span>
                   <el-button
                    v-if="userStore.userInfo?.role === 'admin' || userStore.userInfo?.id === reply.user_id"
                    type="danger"
                    link
                    size="small"
                    class="ml-2"
                    @click="handleDeleteReply(reply)"
                  >删除</el-button>
                </div>
              </div>
              <div class="reply-text">{{ reply.content }}</div>
            </div>
          </div>
          <div v-if="currentFeedback.replies.length === 0" class="no-replies">
            暂无评论，快来抢沙发吧~
          </div>
        </div>
      </div>
      
      <div class="reply-input-area">
         <el-input
           v-model="replyContent"
           type="textarea"
           :rows="3"
           placeholder="友善回复，理性探讨..."
           resize="none"
         />
         <div class="reply-actions">
           <el-button type="primary" :loading="replying" @click="submitReply">发送回复</el-button>
         </div>
      </div>
    </el-dialog>

    <!-- Create Dialog -->
    <el-dialog
      v-model="createVisible"
      title="发布新帖子"
      width="500px"
    >
      <el-form :model="createForm" label-position="top">
        <el-form-item label="标题">
          <el-input v-model="createForm.title" placeholder="简要描述您的问题或观点" />
        </el-form-item>
        <el-form-item label="分类">
          <el-radio-group v-model="createForm.category">
            <el-radio label="message">留言</el-radio>
            <el-radio label="bug">Bug反馈</el-radio>
            <el-radio label="suggestion">建议</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="内容">
          <el-input
             v-model="createForm.content"
             type="textarea"
             :rows="6"
             placeholder="详细描述..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="submitCreate">发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { EditPen, Search, View, ChatLineSquare, Delete, Star } from '@element-plus/icons-vue'
import { useUserStore } from '../store'
import { getFeedbacks, createFeedback, getFeedbackDetail, replyFeedback, deleteFeedback, deleteReply, likeFeedback, likeReply } from '../api/feedback'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const userStore = useUserStore()
const loading = ref(false)
const feedbacks = ref([])

// Filters
const filterCategory = ref('all')
const keyword = ref('')

// Create
const createVisible = ref(false)
const creating = ref(false)
const createForm = reactive({
  title: '',
  category: 'message',
  content: ''
})

// Detail & Reply
const detailVisible = ref(false)
const currentFeedback = ref(null)
const replyContent = ref('')
const replying = ref(false)

const fetchFeedbacks = async () => {
  loading.value = true
  try {
    const params = {
      category: filterCategory.value,
      keyword: keyword.value
    }
    const res = await getFeedbacks(params)
    feedbacks.value = res
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  createForm.title = ''
  createForm.content = ''
  createForm.category = 'message'
  createVisible.value = true
}

const submitCreate = async () => {
  if (!createForm.title || !createForm.content) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  creating.value = true
  try {
    await createFeedback(createForm)
    ElMessage.success('发布成功')
    createVisible.value = false
    fetchFeedbacks()
  } catch (error) {
    ElMessage.error(error.response?.data?.msg || '发布失败')
  } finally {
    creating.value = false
  }
}

const openDetail = async (post) => {
  try {
    const res = await getFeedbackDetail(post.id)
    currentFeedback.value = res
    replyContent.value = ''
    detailVisible.value = true
  } catch (error) {
    ElMessage.error('获取详情失败')
  }
}

const submitReply = async () => {
  if (!replyContent.value.trim()) {
    ElMessage.warning('请输入回复内容')
    return
  }
  
  replying.value = true
  try {
    const res = await replyFeedback(currentFeedback.value.id, { content: replyContent.value })
    ElMessage.success('回复成功')
    // Append reply locally
    currentFeedback.value.replies.push(res.data)
    replyContent.value = ''
  } catch (error) {
     ElMessage.error('回复失败')
  } finally {
    replying.value = false
  }
}

const handleDeleteFeedback = (post, event) => {
  if (event) event.stopPropagation()
  ElMessageBox.confirm('确定删除该帖子吗？', '警告', {
    type: 'warning'
  }).then(async () => {
    try {
      await deleteFeedback(post.id)
      ElMessage.success('删除成功')
      fetchFeedbacks()
      detailVisible.value = false
    } catch (error) {
       ElMessage.error(error.response?.data?.msg || '删除失败')
    }
  }).catch(() => {})
}

const handleDeleteReply = (reply) => {
   ElMessageBox.confirm('确定删除该回复吗？', '警告', {
    type: 'warning'
  }).then(async () => {
    try {
      await deleteReply(reply.id)
      ElMessage.success('删除成功')
      if (currentFeedback.value) {
        currentFeedback.value.replies = currentFeedback.value.replies.filter(r => r.id !== reply.id)
      }
    } catch (error) {
       ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const handleLikeFeedback = async (post) => {
  try {
    const res = await likeFeedback(post.id)
    post.is_liked = res.is_liked
    post.like_count = res.like_count
  } catch (error) {
    // silent fail or msg
  }
}

const handleLikeReply = async (reply) => {
  try {
    const res = await likeReply(reply.id)
    reply.is_liked = res.is_liked
    reply.like_count = res.like_count
  } catch (error) {
  }
}

const getCategoryLabel = (cat) => {
  const map = { message: '留言', bug: 'Bug反馈', suggestion: '建议' }
  return map[cat] || '讨论'
}

const getCategoryType = (cat) => {
  const map = { message: 'info', bug: 'danger', suggestion: 'success' }
  return map[cat] || ''
}

const formatDate = (date) => dayjs(date).format('YYYY-MM-DD HH:mm')
const formatTimeAgo = (date) => dayjs(date).fromNow()

onMounted(() => {
  fetchFeedbacks()
})
</script>

<style scoped>
.feedback-container {
  padding: 24px;
  max-width: 1000px;
  margin: 0 auto;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.title-group h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
}

.subtitle {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.filter-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.post-items {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.post-item {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  transition: all 0.2s;
}

.post-item:hover {
  border-color: var(--el-color-primary-light-5);
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.post-main {
  flex: 1;
  min-width: 0;
  margin-right: 20px;
}

.post-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.post-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.post-summary {
  color: var(--el-text-color-regular);
  font-size: 14px;
  margin: 0 0 12px 0;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.post-meta {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.user-meta {
  display: flex;
  align-items: center;
  gap: 6px;
}

.divider {
  margin: 0 8px;
  color: var(--el-border-color);
}

.post-stats {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: center;
  gap: 8px;
  min-width: 80px;
}

.reply-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--el-color-primary);
  font-weight: 600;
  font-size: 16px;
}

.last-reply {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

/* Detail Styles */
.detail-content {
  max-height: 60vh;
  overflow-y: auto;
  padding-right: 8px;
  margin-bottom: 16px;
}

.post-author-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.author-info {
  display: flex;
  gap: 12px;
}

.author-name {
  font-weight: 600;
  font-size: 16px;
}

.post-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.post-body {
  font-size: 15px;
  line-height: 1.6;
  color: var(--el-text-color-primary);
  white-space: pre-wrap;
  background: var(--el-fill-color-light);
  padding: 16px;
  border-radius: 8px;
}

.reply-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.reply-item {
  display: flex;
  gap: 12px;
}

.reply-content-wrapper {
  flex: 1;
}

.reply-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.reply-author {
  font-weight: 600;
  font-size: 14px;
}

.reply-author.is-admin {
  color: var(--el-color-danger);
}

.admin-badge {
  margin-left: 4px;
  height: 20px;
  padding: 0 4px;
}

.reply-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.reply-text {
  font-size: 14px;
  line-height: 1.5;
  color: var(--el-text-color-regular);
}

.no-replies {
  text-align: center;
  color: var(--el-text-color-secondary);
  padding: 20px;
}

.reply-input-area {
  border-top: 1px solid var(--el-border-color-light);
  padding-top: 16px;
}

.reply-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.delete-action {
  cursor: pointer;
  display: flex;
  align-items: center;
  color: var(--el-text-color-secondary);
  transition: color 0.2s;
  font-size: 12px;
}

.delete-action:hover {
  color: var(--el-color-danger);
}

.reply-actions-top {
  display: flex;
  align-items: center;
}

.ml-2 {
  margin-left: 8px;
}
.mr-2 {
  margin-right: 8px;
}
.is-liked {
  color: var(--el-color-primary);
}
.like-action {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  color: var(--el-text-color-secondary);
  transition: all 0.2s;
}
.like-action:hover {
  color: var(--el-color-primary);
}
.post-actions-bar {
  margin-top: 16px;
  display: flex;
  justify-content: flex-start;
}
</style>
