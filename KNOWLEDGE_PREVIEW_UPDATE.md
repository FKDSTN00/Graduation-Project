# 知识库预览优化：新标签页打开

## ✅ 已完成的功能

在管理员知识库预览对话框中添加了"新标签页打开"功能。

### 1. 界面更新
- 在预览窗口的底部（Footer）添加了一个**绿色按钮**（type='success'）。
- 按钮位置：关闭按钮和编辑按钮之间。
- 按钮文本："新标签页打开"。

### 2. 功能实现
- ✅ **openKnowledgeInNewTab** 函数：
  - 获取当前预览的文章ID
  - 构造路由 `/knowledge/{id}`
  - 使用 `window.open(route, '_blank')` 在新标签页中打开

### 3. 代码变更
**文件**：`/frontend/src/views/AdminDashboard.vue`

**HTML**：
```html
<el-button type="success" @click="openKnowledgeInNewTab">新标签页打开</el-button>
```

**JavaScript**：
```javascript
const openKnowledgeInNewTab = () => {
  if (currentKnowledgeArticle.value) {
    const route = `/knowledge/${currentKnowledgeArticle.value.id}`
    window.open(route, '_blank')
  }
}
```

现在管理员预览文章时，不仅可以直接编辑，还可以选择在新标签页打开查看完整的文章详情页效果。
