<template>
  <div class="knowledge-article-page">
    <div class="article-header">
      <el-button @click="goBack">返回知识库</el-button>
    </div>

    <div v-loading="loading" class="article-container">
      <div v-if="article" class="article-detail">
        <h1 class="article-title">{{ article.title }}</h1>
        
        <div class="article-meta">
          <el-tag size="small">{{ article.category_name }}</el-tag>
          <span class="meta-item">
            <el-icon><User /></el-icon>
            作者：{{ article.author }}
          </span>
          <span class="meta-item">
            <el-icon><Clock /></el-icon>
            更新时间：{{ article.updated_at }}
          </span>
        </div>

        <el-divider />

        <div class="article-content" v-html="article.content"></div>
      </div>

      <el-empty v-else-if="!loading" description="文章不存在" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Clock } from '@element-plus/icons-vue'
import { getArticle } from '../api/knowledge'

const route = useRoute()
const router = useRouter()

const article = ref(null)
const loading = ref(false)

const loadArticle = async () => {
  loading.value = true
  try {
    const res = await getArticle(route.params.id)
    article.value = res
  } catch (error) {
    console.error('加载文章失败', error)
    ElMessage.error('文章加载失败')
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
  if (userInfo.role === 'admin') {
    router.push('/admin/knowledge')
  } else {
    router.push('/knowledge')
  }
}

onMounted(() => {
  loadArticle()
})
</script>

<style scoped>
.knowledge-article-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.article-header {
  margin-bottom: 20px;
}

.article-container {
  background: var(--el-bg-color);
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.article-detail {
  max-width: 900px;
  margin: 0 auto;
}

.article-title {
  font-size: 32px;
  font-weight: 600;
  margin: 0 0 20px 0;
  color: var(--el-text-color-primary);
}

.article-meta {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.article-content {
  margin-top: 30px;
  line-height: 1.8;
  font-size: 16px;
  color: var(--el-text-color-primary);
}

.article-content :deep(img) {
  max-width: 100% !important;
  height: auto !important;
  display: block;
  margin: 20px 0;
  border-radius: 4px;
}

.article-content :deep(p) {
  margin: 12px 0;
}

.article-content :deep(h1),
.article-content :deep(h2),
.article-content :deep(h3),
.article-content :deep(h4),
.article-content :deep(h5),
.article-content :deep(h6) {
  margin: 24px 0 12px 0;
  color: var(--el-text-color-primary);
}

.article-content :deep(a) {
  color: var(--el-color-primary);
  text-decoration: none;
}

.article-content :deep(a:hover) {
  text-decoration: underline;
}

.article-content :deep(blockquote) {
  border-left: 4px solid var(--el-border-color);
  padding-left: 16px;
  margin: 16px 0;
  color: var(--el-text-color-secondary);
}

.article-content :deep(code) {
  background-color: var(--el-fill-color-light);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  color: var(--el-color-danger);
}

.article-content :deep(pre) {
  background-color: var(--el-fill-color-darker);
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 16px 0;
}

.article-content :deep(pre code) {
  background-color: transparent;
  padding: 0;
  color: var(--el-text-color-primary);
}

.article-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
}

.article-content :deep(table td),
.article-content :deep(table th) {
  border: 1px solid var(--el-border-color-light);
  padding: 8px 12px;
}

.article-content :deep(table th) {
  background-color: var(--el-fill-color-light);
  font-weight: 600;
}

.article-content :deep(ul),
.article-content :deep(ol) {
  padding-left: 24px;
  margin: 12px 0;
}

.article-content :deep(li) {
  margin: 6px 0;
}
</style>
