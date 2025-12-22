<template>
  <div class="knowledge-page">
    <div class="page-header">
      <h2>知识库</h2>
    </div>

    <!-- 分类标签 -->
    <el-tabs v-model="activeCategory" @tab-change="handleCategoryChange">
      <el-tab-pane :label="`全部 (${totalArticleCount})`" name="all" />
      <el-tab-pane 
        v-for="cat in categories" 
        :key="cat.id" 
        :label="`${cat.name} (${cat.article_count})`" 
        :name="String(cat.id)" 
      />
    </el-tabs>

    <!-- 文章列表 -->
    <div v-loading="loading" class="article-list">
      <el-card 
        v-for="article in articles" 
        :key="article.id" 
        class="article-card"
        shadow="hover"
        @click="viewArticle(article)"
      >
        <div class="article-header">
          <h3>{{ article.title }}</h3>
          <el-tag size="small" type="info">{{ article.category_name }}</el-tag>
        </div>
        <div class="article-meta">
          <span><el-icon><User /></el-icon> {{ article.author }}</span>
          <span><el-icon><Clock /></el-icon> {{ article.updated_at }}</span>
        </div>
      </el-card>

      <el-empty v-if="articles.length === 0 && !loading" description="暂无文章" />
    </div>

    <!-- 文章预览对话框 -->
    <el-dialog 
      v-model="previewVisible" 
      :title="currentArticle?.title" 
      width="70%" 
      top="5vh"
      destroy-on-close
    >
      <div v-if="currentArticle" class="article-preview">
        <div class="article-info">
          <el-tag size="small">{{ currentArticle.category_name }}</el-tag>
          <span class="author">作者：{{ currentArticle.author }}</span>
          <span class="time">更新时间：{{ currentArticle.updated_at }}</span>
        </div>
        <el-divider />
        <div class="article-content" v-html="currentArticle.content"></div>
      </div>
      <template #footer>
        <el-button @click="previewVisible = false">关闭</el-button>
        <el-button type="primary" @click="openInNewTab">新标签页打开</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Clock } from '@element-plus/icons-vue'
import { getCategories, getArticles } from '../api/knowledge'

const router = useRouter()
const activeCategory = ref('all')
const categories = ref([])
const articles = ref([])
const loading = ref(false)
const previewVisible = ref(false)
const currentArticle = ref(null)

const totalArticleCount = computed(() => {
  return categories.value.reduce((sum, cat) => sum + cat.article_count, 0)
})

const loadCategories = async () => {
  try {
    const res = await getCategories()
    categories.value = res
  } catch (error) {
    console.error('加载分类失败', error)
  }
}

const loadArticles = async () => {
  loading.value = true
  try {
    const categoryId = activeCategory.value === 'all' ? null : parseInt(activeCategory.value)
    const res = await getArticles(categoryId)
    articles.value = res
  } catch (error) {
    console.error('加载文章失败', error)
    ElMessage.error('加载文章失败')
  } finally {
    loading.value = false
  }
}

const handleCategoryChange = () => {
  loadArticles()
}

const viewArticle = (article) => {
  currentArticle.value = article
  previewVisible.value = true
}

const openInNewTab = () => {
  if (currentArticle.value) {
    const { href } = router.resolve({
      name: 'knowledge-article',
      params: { id: currentArticle.value.id }
    })
    window.open(href, '_blank')
  }
}

onMounted(() => {
  loadCategories()
  loadArticles()
})
</script>

<style scoped>
.knowledge-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
}

.article-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
  margin-top: 20px;
}

.article-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.article-card:hover {
  transform: translateY(-4px);
}

.article-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.article-header h3 {
  margin: 0;
  font-size: 18px;
  flex: 1;
  margin-right: 12px;
}

.article-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.article-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
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
</style>
