import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Layout from '../views/Layout.vue'
import Home from '../views/Home.vue'
import DocumentList from '../views/DocumentList.vue'
import DocumentEditor from '../views/DocumentEditor.vue'
import Schedule from '../views/Schedule.vue'
import Approval from '../views/Approval.vue'
import Tasks from '../views/Tasks.vue'
import Votes from '../views/Votes.vue'
import Knowledge from '../views/Knowledge.vue'
import KnowledgeArticle from '../views/KnowledgeArticle.vue'
// import Files from '../views/Files.vue'
import Feedback from '../views/Feedback.vue'
import PersonalCenter from '../views/PersonalCenter.vue'
import AdminDashboard from '../views/AdminDashboard.vue'

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
