<template>
  <div class="placeholder-page">
    <el-empty description="投票与问卷功能开发中">
      <template #image>
        <el-icon :size="100" color="var(--el-text-color-secondary)">
          <Ticket />
        </el-icon>
      </template>
      <el-button type="primary">敬请期待</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { Ticket } from '@element-plus/icons-vue'
</script>

<style scoped>
.placeholder-page {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  min-height: 500px;
}
</style>
