<template>
  <div class="announcement-detail-page">
    <el-card class="detail-card" v-loading="loading">
       <template v-if="notice">
          <div class="header">
             <h2 class="title">{{ notice.title }}</h2>
             <div class="meta">
                <el-tag :type="notice.level === 'important' ? 'danger' : 'primary'">{{ notice.level === 'important' ? '重要' : '普通' }}</el-tag>
                <span class="author">发布人: {{ notice.author }}</span>
                <span class="date">时间: {{ formatTime(notice.created_at) }}</span>
             </div>
          </div>
          <el-divider />
          <div class="content">
             {{ notice.content }}
          </div>
       </template>
       <el-empty v-else description="未找到公告" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getNotice } from '../api/notice'
import dayjs from 'dayjs'

const route = useRoute()
const notice = ref(null)
const loading = ref(false)

onMounted(async () => {
   const id = route.params.id
   if (id) {
      loading.value = true
      try {
         const res = await getNotice(id)
         notice.value = res
      } catch(e) {
         console.error(e)
      } finally {
         loading.value = false
      }
   }
})

const formatTime = (iso) => dayjs(iso).format('YYYY-MM-DD HH:mm')
</script>

<style scoped>
.announcement-detail-page {
   padding: 20px;
   max-width: 900px;
   margin: 0 auto;
}
.header {
   text-align: center;
   margin-bottom: 20px;
}
.title {
    margin-bottom: 15px;
    font-size: 24px;
    color: var(--el-text-color-primary);
}
.meta {
   margin-top: 10px;
   display: flex;
   justify-content: center;
   gap: 20px;
   color: var(--el-text-color-secondary);
   font-size: 14px;
   align-items: center;
}
.content {
    white-space: pre-wrap; 
    line-height: 1.8; 
    font-size: 16px;
    color: var(--el-text-color-regular);
    padding: 10px 0;
}
</style>
