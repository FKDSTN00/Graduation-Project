<template>
  <div class="ai-chat-container">
    <!-- 移动端侧边栏遮罩 -->
    <div 
      class="sidebar-backdrop" 
      v-if="isMobile && sidebarVisible"
      @click="sidebarVisible = false"
    ></div>

    <!-- 左侧会话列表 -->
    <div class="sidebar" :class="{ 'mobile-open': isMobile && sidebarVisible }">
      <div class="new-chat-btn">
        <el-button type="primary" class="new-btn" @click="createNewSession">
          <el-icon><Plus /></el-icon> 新对话
        </el-button>
      </div>
      
      <div class="session-list" v-loading="loadingSessions">
        <div 
          v-for="session in formattedSessions" 
          :key="session.id" 
          class="session-item"
          :class="{ active: currentSessionId === session.id, pinned: session.is_pinned }"
          @click="selectSession(session.id)"
        >
          <div class="session-icon">
            <el-icon><ChatDotSquare /></el-icon>
          </div>
          <div class="session-info">
            <div class="session-title">{{ session.title }}</div>
            <div class="session-time">{{ session.timeDisplay }}</div>
          </div>
          <div class="session-actions" @click.stop>
            <el-dropdown trigger="click" @command="(cmd) => handleSessionAction(cmd, session)">
              <span class="action-trigger">
                <el-icon><MoreFilled /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="rename">重命名</el-dropdown-item>
                  <el-dropdown-item command="pin">{{ session.is_pinned ? '取消置顶' : '置顶' }}</el-dropdown-item>
                  <el-dropdown-item command="delete" style="color: var(--el-color-danger)">删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
        <el-empty v-if="sessions.length === 0" description="暂无历史对话" :image-size="60"></el-empty>
      </div>
    </div>

    <!-- 右侧聊天区域 -->
    <div class="chat-area">
      <!-- 移动端顶部导航栏 -->
      <div class="mobile-header" v-if="isMobile">
        <el-button text @click="sidebarVisible = true">
           <el-icon><Menu /></el-icon>
        </el-button>
        <span class="mobile-title">DeepSeek-R1</span>
        <el-button text @click="createNewSession">
           <el-icon><Plus /></el-icon>
        </el-button>
      </div>

      <!-- 消息列表 -->
      <div class="messages-container" ref="messagesContainer">
        <div v-if="messages.length === 0 && !currentSessionId" class="welcome-screen">
          <div class="welcome-logo">
            <img :src="deepseekLogo" alt="DeepSeek" style="width: 60px; height: 60px;" />
          </div>
          <h2>今天有什么可以帮到你？</h2>
        </div>
        
        <div v-else class="message-list">
          <div v-for="(msg, index) in messages" :key="index" class="message-wrapper" :class="msg.role">
            <div class="avatar">
               <el-avatar v-if="msg.role === 'user'" :size="36" :src="userAvatar"></el-avatar>
               <div v-else class="ai-avatar">
                 <img :src="deepseekLogo" alt="DeepSeek" />
               </div>
            </div>
            <div class="message-content">
              <!-- 使用 v-html 渲染 markdown 内容 (需要引入 marked) -->
              <div class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
              <div class="message-time" v-if="msg.created_at">{{ formatTime(msg.created_at) }}</div>
              
              <!-- 复制按钮 -->
              <div class="copy-btn" @click="copyToClipboard(msg.content)">
                 <el-icon><CopyDocument /></el-icon>
              </div>
            </div>
          </div>
          <div v-if="isTyping" class="message-wrapper assistant">
             <div class="avatar">
               <div class="ai-avatar">
                 <img :src="deepseekLogo" alt="DeepSeek" />
               </div>
            </div>
            <div class="message-content typing">
               <span class="dot"></span><span class="dot"></span><span class="dot"></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <div class="input-wrapper" :class="{ 'expanded': inputText.length > 50 }">
          <el-input
            v-model="inputText"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 6 }"
            placeholder="输入您的问题 (Shift + Enter 换行)..."
            resize="none"
            class="chat-input"
            @keydown.enter="handleKeydown"
          />
          <el-button 
            type="primary" 
            circle 
            class="send-btn" 
            :disabled="!inputText.trim() || isTyping"
            @click="sendMessage"
          >
            <el-icon><Position /></el-icon>
          </el-button>
        </div>
        <div class="input-tips">
          AI 生成的内容可能不准确，请核对重要信息。
        </div>
      </div>
    </div>

    <!-- 重命名对话框 -->
    <el-dialog v-model="renameVisible" title="重命名对话" width="400px">
      <el-input v-model="newTitle" placeholder="请输入新标题" @keyup.enter="submitRename" />
      <template #footer>
        <el-button @click="renameVisible = false">取消</el-button>
        <el-button type="primary" @click="submitRename">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { 
  Plus, ChatDotSquare, MoreFilled, Position, Cpu, CopyDocument, Menu, ArrowLeft
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css' // 代码高亮样式
// 配置 marked
import request from '../api/request'
import deepseekLogo from '../assets/deepseek.png'

marked.setOptions({
  highlight: function (code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext';
    return hljs.highlight(code, { language }).value;
  },
  langPrefix: 'hljs language-',
  breaks: true // 支持 Github 风格换行
})

// 状态
const sessions = ref([])
const loadingSessions = ref(false)
const currentSessionId = ref(null)
const messages = ref([])
const inputText = ref('')
const isTyping = ref(false)
const renameVisible = ref(false)
const newTitle = ref('')
const editingSession = ref(null)
const userAvatar = ref('')
const isMobile = ref(false)
const sidebarVisible = ref(false)
// 自动导入，无需额外声明

// 监听窗口大小
const checkMobile = () => {
  isMobile.value = window.innerWidth <= 768
  if (!isMobile.value) {
    sidebarVisible.value = true // PC 端默认显示
  } else {
    sidebarVisible.value = false // 移动端默认隐藏
  }
}

import { useRouter, useRoute } from 'vue-router'

const route = useRoute()

onMounted(async () => {
  const userInfoStr = localStorage.getItem('userInfo')
  if (userInfoStr) {
    const userInfo = JSON.parse(userInfoStr)
    userAvatar.value = userInfo.avatar
  }
  
  checkMobile()
  window.addEventListener('resize', checkMobile)
  
  await loadSessions()
  
  // 检查 URL 参数是否有 session_id 或 summary action
  if (route.query.action === 'summary') {
    handleSummaryAction()
  } else if (route.query.session_id) {
    const sid = parseInt(route.query.session_id)
    if (sid) {
       selectSession(sid)
    }
  }
})

// 处理文档总结跳转
const handleSummaryAction = async () => {
  const docStr = sessionStorage.getItem('ai_summary_doc')
  if (!docStr) return
  
  sessionStorage.removeItem('ai_summary_doc') // 清除数据
  
  try {
    const doc = JSON.parse(docStr)
    const summaryPrompt = `请阅读并总结以下文档的内容：\n\n${doc.title}\n\n${doc.content}`
    
    // 1. 创建新会话
    const sessionRes = await request.post('/ai/sessions')
    const sessionId = sessionRes.id
    
    // 2. 重命名会话
    await request.put(`/ai/sessions/${sessionId}`, {
      title: `AI总结：${doc.title}`
    })
    
    // 3. 刷新列表并选中
    await loadSessions()
    await selectSession(sessionId)
    
    // 4. 自动发送 prompt (调用 sendMessage 逻辑，但不要重复绑定事件)
    // 直接复用 sendMessage 的核心逻辑，但参数不一样
    triggerAutoMessage(sessionId, summaryPrompt)
    
  } catch (err) {
    ElMessage.error('无法启动 AI 总结: ' + err.message)
  }
}

// 自动发送消息（不依赖输入框）
const triggerAutoMessage = async (sessionId, text) => {
  if (isTyping.value) return
  
  isTyping.value = true
  
  // 先显示用户消息
  messages.value.push({
    role: 'user',
    content: text,
    created_at: new Date().toISOString()
  })
  scrollToBottom()
  
  try {
    // 调用后端
    const res = await request.post('/ai/chat', {
      session_id: sessionId,
      prompt: text
    }, {
      timeout: 120000 // 120s 超时
    })
    
    // 成功收到回复
    isTyping.value = false
    typewriterEffect(res.content, 'assistant')
    
  } catch (err) {
    console.error(err)
    isTyping.value = false
    messages.value.push({
       role: 'system',
       content: 'AI 响应超时或出错，请重试。'
    })
    
    // 即使出错，也要刷新列表以显示（可能已保存的用户消息）
    loadSessions()
  }
}

// 计算属性
const formattedSessions = computed(() => {
  const now = dayjs()
  return sessions.value.map(s => {
    let timeDisplay = ''
    const date = dayjs(s.updated_at)
    if (date.isSame(now, 'day')) {
      timeDisplay = date.format('HH:mm')
    } else if (date.isSame(now.subtract(1, 'day'), 'day')) {
      timeDisplay = '昨天'
    } else {
      timeDisplay = date.format('MM-DD')
    }
    return { ...s, timeDisplay }
  })
})

// 加载会话列表
const loadSessions = async () => {
  loadingSessions.value = true
  try {
    const res = await request.get('/ai/sessions')
    sessions.value = res
  } catch (err) {
    console.error(err)
    ElMessage.error('加载会话列表失败')
  } finally {
    loadingSessions.value = false
  }
}

// 选择会话
const selectSession = async (id) => {
  if (currentSessionId.value === id) return
  currentSessionId.value = id
  messages.value = [] // 先清空，显示加载效果
  
  try {
    const res = await request.get(`/ai/sessions/${id}/messages`)
    messages.value = res
    scrollToBottom()
    // 移动端选择后自动关闭侧边栏
    if (isMobile.value) {
      sidebarVisible.value = false
    }
  } catch (err) {
    console.error(err)
    ElMessage.error('加载消息失败')
  }
}

// 创建新会话
const createNewSession = async () => {
  // 如果当前已经是空的非新建会话，则直接清空
  currentSessionId.value = null
  messages.value = []
  inputText.value = ''
  // 实际上只有发第一条消息时才真正创建 session
  if (isMobile.value) {
    sidebarVisible.value = false
  }
}

// 发送消息
const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || isTyping.value) return

  // 乐观更新 UI
  messages.value.push({
    role: 'user',
    content: text,
    created_at: new Date().toISOString()
  })
  
  inputText.value = ''
  isTyping.value = true
  scrollToBottom()

  try {
    const res = await request.post('/ai/chat', {
      session_id: currentSessionId.value,
      prompt: text
    }, {
      timeout: 120000 // 单独为 AI 对话设置更长的超时时间 (120秒)
    })
    
    const { session_id, role, content, title } = res
    
    // 如果是新会话，更新 ID 并刷新列表
    if (!currentSessionId.value) {
      currentSessionId.value = session_id
      loadSessions() // 重新加载以显示新标题
    } else {
       // 检查标题是否变化（自动总结）
       const session = sessions.value.find(s => s.id === session_id)
       if (session && session.title !== title) {
          session.title = title
       }
       // 也可以把这个 session 移到最前
       if (session) {
          session.updated_at = new Date().toISOString()
          sessions.value.sort((a, b) => b.is_pinned - a.is_pinned || new Date(b.updated_at) - new Date(a.updated_at))
       }
    }

    // 更新状态：不再输入中
    isTyping.value = false
    
    // 开始打字机效果输出
    typewriterEffect(content, role)
    
  } catch (err) {
    console.error(err)
    ElMessage.error('发送失败: ' + (err.response?.data?.error || err.message))
    isTyping.value = false
    messages.value.push({
       role: 'system',
       content: '发送失败，请稍后重试。'
    })
  }
}

// 打字机效果函数
const typewriterEffect = (fullText, role) => {
  // 先加入一个空消息
  const msgIndex = messages.value.length
  messages.value.push({
    role: role,
    content: '', // 初始为空
    created_at: new Date().toISOString()
  })
  
  let currentIndex = 0
  const speed = 20 // 打字速度 ms
  
  const timer = setInterval(() => {
    if (currentIndex < fullText.length) {
      // 每次追加一个字符
      // 注意：直接修改数组元素属性在 Vue3 ref 是响应式的
      // 为了稳定性使用 messages.value[msgIndex]
      const char = fullText.charAt(currentIndex)
      messages.value[msgIndex].content += char
      currentIndex++
      
      // 每输出几个字滚动一次，避免太频繁
      if (currentIndex % 2 === 0) scrollToBottom() 
    } else {
      clearInterval(timer)
      scrollToBottom()
    }
  }, speed)
}

const handleKeydown = (e) => {
  if (!e.shiftKey) {
    e.preventDefault() // 阻止默认的回车换行
    sendMessage()
  }
  // 如果按了 Shift，不做处理，允许默认的换行行为
}

// 复制功能
const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('复制成功')
  } catch (err) {
    ElMessage.error('复制失败')
    console.error(err)
  }
}

// 会话操作菜单
const handleSessionAction = async (cmd, session) => {
  if (cmd === 'rename') {
    editingSession.value = session
    newTitle.value = session.title
    renameVisible.value = true
  } else if (cmd === 'delete') {
    ElMessageBox.confirm('确定要删除这个对话吗？', '提示', {
      type: 'warning'
    }).then(async () => {
      try {
        await request.delete(`/ai/sessions/${session.id}`)
        ElMessage.success('删除成功')
        if (currentSessionId.value === session.id) {
          createNewSession()
        }
        loadSessions()
      } catch (err) {
        ElMessage.error('删除失败')
      }
    })
  } else if (cmd === 'pin') {
     try {
       await request.put(`/ai/sessions/${session.id}`, {
         is_pinned: !session.is_pinned
       })
       loadSessions()
     } catch(err) {
       ElMessage.error('操作失败')
     }
  }
}

const submitRename = async () => {
  if (!newTitle.value.trim()) return
  try {
    await request.put(`/ai/sessions/${editingSession.value.id}`, {
      title: newTitle.value
    })
    editingSession.value.title = newTitle.value
    renameVisible.value = false
    ElMessage.success('重命名成功')
  } catch (err) {
    ElMessage.error('重命名失败')
  }
}

// 工具函数
const scrollToBottom = () => {
  nextTick(() => {
    if (this?.$refs?.messagesContainer) { // this check might be needed in setup script? No, in script setup use ref directly
       // In script setup, use the ref variable
    }
    // const container = document.querySelector('.messages-container') // fallback selector or ref
    // vue ref usage:
    const container = document.querySelector('.messages-container') // 此时 ref 还没绑定好或者为了简便直接 dom，最好用 ref
    if (container) {
       container.scrollTop = container.scrollHeight
    }
  })
}

// 为了在模板中使用 ref，需要手动确保正确绑定
// 上面的 scrollToBottom 使用 querySelector 是为了稳健，正确的 ref 使用方式如下：
// 已在模板声明 ref="messagesContainer"
// 使用 watch 监听 messages 变化自动滚动
watch(messages, () => {
  nextTick(() => {
    // 简单粗暴选择器，确保一定能滚到底部
    const container = document.querySelector('.messages-container')
    if (container) container.scrollTop = container.scrollHeight
  })
}, { deep: true })

const renderMarkdown = (text) => {
  return marked(text || '')
}

const formatTime = (time) => {
  return dayjs(time).format('MM-DD HH:mm')
}
</script>

<style scoped>
.ai-chat-container {
  display: flex;
  height: calc(100vh - 84px); /* 减去头部高度，确保填满剩余空间 */
  background-color: var(--el-bg-color);
  overflow: hidden;
}

/* 左侧栏 */
.sidebar {
  width: 260px;
  border-right: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
  background-color: var(--el-bg-color-page);
  flex-shrink: 0;
}

.new-chat-btn {
  padding: 16px;
}

.new-btn {
  width: 100%;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: background-color 0.2s;
  position: relative;
}

.session-item:hover {
  background-color: var(--el-fill-color);
}

.session-item.active {
  background-color: var(--el-color-primary-light-9);
}

.session-item.pinned {
  border-left: 3px solid var(--el-color-primary);
  background-color: var(--el-fill-color-light);
}

.session-icon {
  margin-right: 10px;
  color: var(--el-text-color-secondary);
  display: flex;
  align-items: center;
}

.session-info {
  flex: 1;
  overflow: hidden;
}

.session-title {
  font-size: 14px;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.session-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.session-actions {
  opacity: 0;
  transition: opacity 0.2s;
  margin-left: 8px;
}

.session-item:hover .session-actions {
  opacity: 1;
}

.action-trigger {
  padding: 4px;
  cursor: pointer;
  color: var(--el-text-color-secondary);
}

.action-trigger:hover {
  color: var(--el-color-primary);
}

/* 右侧聊天区 */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  background-color: var(--el-bg-color);
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.welcome-screen {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-secondary);
  opacity: 0.8;
}

.welcome-logo {
  margin-bottom: 20px;
  /* padding: 20px; */
  /* background: var(--el-fill-color-light); */
  /* border-radius: 50%; */
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: 20px;
}

.message-wrapper {
  display: flex;
  gap: 16px;
  max-width: 80%;
}

.message-wrapper.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-wrapper.assistant {
  align-self: flex-start;
}

.avatar {
  flex-shrink: 0;
}

.ai-avatar {
  width: 36px;
  height: 36px;
  background: transparent; /* 透明背景 */
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden; 
  /* border: 1px solid var(--el-border-color-lighter); */
}

.ai-avatar img {
  width: 100% !important; 
  height: 100% !important;
  object-fit: contain; /* 保持比例 */
  padding: 4px; /* 留点白边 */
}

.message-content {
  background-color: var(--el-fill-color-light);
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 14px;
  color: var(--el-text-color-primary);
  min-width: 50px;
  position: relative;
  border: 1px solid var(--el-border-color-lighter);
}

/* 用户与 AI 消息颜色统一，只靠对齐区分 */
.message-wrapper.user .message-content {
  /* background-color: var(--el-color-primary);
  color: white; */
  background-color: var(--el-bg-color-overlay); 
  border-radius: 12px 12px 0 12px;
}

.message-wrapper.assistant .message-content {
  border-radius: 0 12px 12px 12px;
  background-color: var(--el-bg-color-overlay); /* 更亮的背景 */
}

/* Markdown 样式适配 */
.markdown-body {
  font-size: 14px;
  line-height: 1.6;
}

.markdown-body :deep(p) {
  margin-bottom: 0.8em;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(h1), 
.markdown-body :deep(h2), 
.markdown-body :deep(h3), 
.markdown-body :deep(h4) {
  font-weight: 600;
  margin-top: 1.2em;
  margin-bottom: 0.6em;
  line-height: 1.3;
}

.markdown-body :deep(ul), 
.markdown-body :deep(ol) {
  padding-left: 1.5em;
  margin-bottom: 0.8em;
}

.markdown-body :deep(li) {
  margin-bottom: 0.2em;
}

.markdown-body :deep(blockquote) {
  margin: 0.8em 0;
  padding: 0 1em;
  color: var(--el-text-color-secondary);
  border-left: 4px solid var(--el-border-color);
}

.markdown-body :deep(a) {
  color: var(--el-color-primary);
  text-decoration: none;
}
.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

/* 代码块样式优化 */
.markdown-body :deep(pre) {
  background-color: #f6f8fa;
  border-radius: 8px;
  padding: 12px;
  margin: 0.8em 0;
  overflow-x: auto;
  border: 1px solid var(--el-border-color-lighter);
}

/* 修复 highlight.js 样式冲突：移除 code.hljs 自身的背景和 padding，统一由 pre 接管 */
.markdown-body :deep(code.hljs) {
  background-color: transparent !important;
  padding: 0 !important;
  display: inline-block; /* 防止 display: block 导致多余换行 */
  width: 100%;
}

/* 覆盖 highlight.js 对 code 标签的默认样式 */
.markdown-body :deep(code) {
  font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace;
}

/* 行内代码样式 (非 pre 包裹的 code) */
.markdown-body :deep(:not(pre) > code) {
  background-color: rgba(175, 184, 193, 0.2);
  padding: 0.2em 0.4em;
  border-radius: 4px;
  font-size: 90%;
  color: #eb5757; /* 稍微显眼的颜色区分行内代码 */
}

/* 用户消息特殊适配恢复颜色 */
.markdown-body :deep(.hljs) {
    color: inherit; /* 让 highlight.js 决定颜色，或者默认 */
}

/* 暗黑模式下行内代码 */
html.dark .markdown-body :deep(:not(pre) > code) {
    background-color: rgba(110, 118, 129, 0.4);
    color: #ff7b72;
}

/* 暗黑模式下 Pre 背景 */
html.dark .markdown-body :deep(pre) {
  background-color: #161b22;
  border-color: #30363d;
}

.message-wrapper.user .markdown-body {
    color: var(--el-text-color-primary); 
}
/* 
.message-wrapper.user .markdown-body :deep(a) {
    color: #e6f7ff;
} */

.message-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
  text-align: right;
  opacity: 0.7;
}

/* 复制按钮 */
.copy-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  opacity: 0;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  background-color: rgba(0, 0, 0, 0.05);
  transition: opacity 0.2s, background-color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 消息内容悬停时显示复制按钮 */
.message-content:hover .copy-btn {
  opacity: 1;
}

.copy-btn:hover {
  background-color: rgba(0, 0, 0, 0.1);
}

/* 输入区域 */
.input-area {
  padding: 20px;
  border-top: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
  align-items: center;
  background-color: var(--el-bg-color);
}

.input-wrapper {
  width: 100%;
  max-width: 768px; /* 默认宽度限制 */
  position: relative;
  transition: max-width 0.3s ease;
  display: flex;
  align-items: flex-end;
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  padding: 8px;
}

.input-wrapper.expanded {
  max-width: 960px; /* 扩展后的最大宽度 */
}

.chat-input :deep(.el-textarea__inner) {
  border: none;
  box-shadow: none;
  padding-right: 40px; /* 给发送按钮留位置 */
  background: transparent;
}

.send-btn {
  margin-left: 8px;
  flex-shrink: 0;
}

.input-tips {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  margin-top: 8px;
  text-align: center;
}

/* 打字动画 */
.typing .dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  margin-right: 3px;
  background: var(--el-text-color-secondary);
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out both;
}

.typing .dot:nth-child(1) { animation-delay: -0.32s; }
.typing .dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* 暗黑模式适配 */
html.dark .message-wrapper.assistant .message-content,
html.dark .message-wrapper.user .message-content {
    background-color: #2b2b2b;
}
html.dark .markdown-body :deep(pre) {
  background-color: #1e1e1e;
}

html.dark .copy-btn {
    background-color: rgba(255, 255, 255, 0.1);
}
html.dark .copy-btn:hover {
    background-color: rgba(255, 255, 255, 0.2);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .ai-chat-container {
    height: calc(100vh - 50px); /* 适配移动端头部高度 */
    position: relative;
  }
  
  .sidebar {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 280px;
    z-index: 2000;
    transform: translateX(-100%);
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 2px 0 8px rgba(0,0,0,0.15);
  }
  
  .sidebar.mobile-open {
    transform: translateX(0);
  }
  
  .sidebar-backdrop {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0,0,0,0.5);
    z-index: 1999;
  }
  
  .chat-area {
    width: 100%;
  }
  
  .mobile-header {
    height: 50px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 10px;
    background-color: var(--el-bg-color);
    border-bottom: 1px solid var(--el-border-color-light);
    flex-shrink: 0;
  }
  
  .mobile-title {
    font-size: 16px;
    font-weight: 500;
  }
  
  .message-wrapper {
    max-width: 90%; /* 移动端气泡宽一点 */
  }
  
  .input-area {
    padding: 10px;
  }
  
  .chat-input :deep(.el-textarea__inner) {
    font-size: 16px; /* 防止 iOS 缩放 */
  }
}
</style>
