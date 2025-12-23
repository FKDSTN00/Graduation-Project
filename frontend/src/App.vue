<template>
  <router-view />
</template>

<script setup>
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background-color: var(--el-bg-color);
  color: var(--el-text-color-primary);
  transition: background-color 0.3s, color 0.3s;
}

#app {
  width: 100%;
  height: 100vh;
}

/* 全局移动端优化 */
@media (max-width: 768px) {
  body {
    font-size: 14px;
  }
  
  /* 按钮适配 */
  .el-button {
    padding: 8px 12px !important;
  }
  
  /* 卡片适配 */
  .el-card {
    margin-bottom: 12px !important;
  }
  
  /* 对话框适配 */
  .el-dialog {
    width: 95% !important;
    margin: 5vh auto !important;
  }
  
  /* 表格横向滚动 */
  .el-table {
    overflow-x: auto;
  }
  
  /* 表单适配 */
  .el-form-item {
    margin-bottom: 16px !important;
  }
  
  /* 输入框适配 */
  .el-input__inner,
  .el-textarea__inner {
    font-size: 16px !important; /* 防止iOS自动放大 */
  }
  
  /* 抽屉适配 */
  .el-drawer {
    width: 90% !important;
  }
}

@media (max-width: 480px) {
  /* 超小屏幕额外优化 */
  .el-button--small {
    padding: 6px 10px !important;
  }
  
  .el-card__body {
    padding: 12px !important;
  }
}

</style>
