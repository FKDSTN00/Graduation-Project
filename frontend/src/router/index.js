import { createRouter, createWebHistory } from 'vue-router'
// 同步导入关键页面，确保首屏快速加载
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Layout from '../views/Layout.vue'

// 懒加载其他页面，按需加载，减少首次加载体积
const Home = () => import('../views/Home.vue')
const DocumentList = () => import('../views/DocumentList.vue')
const DocumentEditor = () => import('../views/DocumentEditor.vue')
const Schedule = () => import('../views/Schedule.vue')
const Approval = () => import('../views/Approval.vue')
const Tasks = () => import('../views/Tasks.vue')
const Votes = () => import('../views/Votes.vue')
const Knowledge = () => import('../views/Knowledge.vue')
const KnowledgeArticle = () => import('../views/KnowledgeArticle.vue')
const Feedback = () => import('../views/Feedback.vue')
const PersonalCenter = () => import('../views/PersonalCenter.vue')
const AdminDashboard = () => import('../views/AdminDashboard.vue')

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/login',
            name: 'login',
            component: Login,
            meta: { title: '登录' }
        },
        {
            path: '/register',
            name: 'register',
            component: Register,
            meta: { title: '注册' }
        },
        {
            path: '/',
            component: Layout,
            children: [
                {
                    path: '',
                    redirect: '/home'
                },
                {
                    path: 'home',
                    name: 'home',
                    component: Home,
                    meta: { title: '首页' }
                },
                {
                    path: 'documents',
                    name: 'documents',
                    component: DocumentList,
                    meta: { title: '文档管理' }
                },
                {
                    path: 'documents/create',
                    name: 'document-create',
                    component: DocumentEditor,
                    meta: { title: '新建文档' }
                },
                {
                    path: 'documents/edit/:id',
                    name: 'document-edit',
                    component: DocumentEditor,
                    meta: { title: '编辑文档' }
                },
                {
                    path: 'tasks',
                    name: 'tasks',
                    component: Tasks,
                    meta: { title: '任务管理' }
                },
                {
                    path: 'knowledge',
                    name: 'knowledge',
                    component: Knowledge,
                    meta: { title: '知识库' }
                },
                {
                    path: 'knowledge/:id',
                    name: 'knowledge-article',
                    component: KnowledgeArticle,
                    meta: { title: '文章详情' }
                },
                {
                    path: 'files',
                    name: 'files',
                    component: () => import('../views/Files.vue'),
                    meta: { title: '文件中心' }
                },
                {
                    path: 'schedule',
                    name: 'schedule',
                    component: Schedule,
                    meta: { title: '日程会议' }
                },
                {
                    path: 'approval',
                    name: 'approval',
                    component: Approval,
                    meta: { title: '审批流程' }
                },
                {
                    path: 'votes',
                    name: 'votes',
                    component: Votes,
                    meta: { title: '投票与问卷' }
                },
                {
                    path: 'ai-chat',
                    name: 'ai-chat',
                    component: () => import('../views/AIChat.vue'),
                    meta: { title: 'Deepseek-R1' }
                },
                {
                    path: 'feedback',
                    name: 'feedback',
                    component: Feedback,
                    meta: { title: '留言与反馈' }
                },
                {
                    path: 'announcement/:id',
                    name: 'announcement-detail',
                    component: () => import('../views/AnnouncementDetail.vue'),
                    meta: { title: '公告详情' }
                },
                {
                    path: 'admin/:tab?',
                    name: 'admin',
                    component: AdminDashboard,
                    meta: { title: '管理员后台', requiresAdmin: true }
                },
                {
                    path: 'personal-center',
                    name: 'personal-center',
                    component: PersonalCenter,
                    meta: { title: '个人中心' }
                }
            ]
        }
    ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('token')
    const userInfo = localStorage.getItem('userInfo') ? JSON.parse(localStorage.getItem('userInfo')) : null
    // 如果没有 token 且访问的不是登录页或注册页，则跳转到登录页
    if (!token && to.path !== '/login' && to.path !== '/register') {
        next('/login')
        return
    }
    // 管理员权限校验
    const isAdmin = userInfo?.role === 'admin'
    if (to.meta?.requiresAdmin && !isAdmin) {
        next('/login')
        return
    }
    // 管理员访问非后台页面时跳转到后台，但允许访问知识库、公告详情和个人中心
    if (isAdmin && !to.path.startsWith('/admin') && !to.path.startsWith('/knowledge') && !to.path.startsWith('/announcement') && !to.path.startsWith('/personal-center') && to.path !== '/login' && to.path !== '/register') {
        next('/admin/announcement')
        return
    }
    next()
})

export default router
