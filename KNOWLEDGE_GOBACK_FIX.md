# 知识库文章详情页返回跳转优化

## ✅ 优化内容

**问题**：
管理员在新标签页打开文章详情后，点击"返回知识库"按钮，默认跳转到了用户端知识库（`/knowledge`），而不是管理员后台知识库（`/admin/knowledge`）。

**解决方案**：
在 `KnowledgeArticle.vue` 的 `goBack` 方法中添加用户角色判断逻辑。

**代码实现**：
```javascript
const goBack = () => {
  const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
  // 如果是管理员，跳转到后台知识库页面
  if (userInfo.role === 'admin') {
    router.push('/admin/knowledge')
  } else {
    // 否则跳转到普通用户知识库页面
    router.push('/knowledge')
  }
}
```

## 📝 效果

- **管理员**：预览文章 -> 新标签页 -> 点击返回 -> 跳转回 **后台管理界面** 的知识库标签
- **普通用户**：查看文章 -> 点击返回 -> 跳转回 **知识库首页**

这样就保证了不同角色用户的操作流线性，避免了管理员误入用户界面的情况。
