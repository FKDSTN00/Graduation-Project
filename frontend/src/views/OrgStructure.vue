<template>
  <div class="org-container">
    <el-card class="tree-card">
      <template #header>
        <div class="card-header">
          <span>组织架构</span>
          <el-button type="primary" size="small" @click="openAddDept(null)">新增一级部门</el-button>
        </div>
      </template>
      <el-tree
        :data="deptTree"
        node-key="id"
        default-expand-all
        :expand-on-click-node="false"
        draggable
        :allow-drop="allowDrop"
        :allow-drag="allowDrag"
        @node-drop="handleDrop"
        @node-click="handleNodeClick"
      >
        <template #default="{ node, data }">
            <span class="custom-tree-node">
            <span>{{ node.label }}</span>
            <span class="node-actions">
               <el-tag size="small" v-if="data.managerName" type="success">负责人: {{ data.managerName }}</el-tag>
               <el-dropdown trigger="click" @command="handleCommand($event, data)">
                  <el-button link type="primary" size="small">
                    操作<el-icon class="el-icon--right"><arrow-down /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="manager">设置负责人</el-dropdown-item>
                      <el-dropdown-item command="edit">编辑</el-dropdown-item>
                      <el-dropdown-item command="add">新增子部门</el-dropdown-item>
                      <el-dropdown-item command="delete" divided style="color: red;">删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
               </el-dropdown>
            </span>
          </span>
        </template>
      </el-tree>
    </el-card>

    <div class="right-panel">

      <el-card v-if="selectedDept" class="dept-detail-card" body-style="overflow:auto">
        <template #header>
          <div class="card-header">
            <span>{{ selectedDept.label }} - 结构图谱</span>
            <el-radio-group v-model="viewMode" size="small">
                <el-radio-button label="chart">图谱</el-radio-button>
                <el-radio-button label="list">列表</el-radio-button>
            </el-radio-group>
          </div>
        </template>
        
        <div v-if="viewMode === 'chart'" class="org-chart-container">
            <!-- 层级图谱 -->
            <div class="tree-chart-node root">
                <!-- 1. 当前部门负责人 -->
                <div class="user-card manager" v-if="chartData.manager">
                   <el-avatar :size="40" :src="chartData.manager.avatar ? (chartData.manager.avatar.startsWith('http') ? chartData.manager.avatar : 'http://localhost' + chartData.manager.avatar) : userDefault" />
                   <div class="info">
                       <span class="name">{{ chartData.manager.username }}</span>
                       <span class="role text-ellipsis">部门主管</span>
                       <el-tag size="small" type="danger">负责人</el-tag>
                   </div>
                </div>
                <!-- 无负责人也要占位 -->
                <div class="user-card empty-manager" v-else>
                     <span style="color:#999">暂无负责人</span>
                </div>
                
                <div class="divider"></div>

                <div class="children-container">
                   <!-- 2. 子部门分支 (如果有) -->
                   <div class="sub-depts-container" v-if="chartData.subDepts && chartData.subDepts.length">
                       <div class="sub-dept-branch" v-for="sub in chartData.subDepts" :key="sub.id">
                           <!-- 子部门主管 -->
                           <div class="branch-connector"></div>
                           <div class="user-card sub-manager">
                                <div class="dept-label-tag">{{ sub.name }}</div>
                                <div v-if="sub.manager">
                                    <el-avatar :size="36" :src="sub.manager.avatar ? (sub.manager.avatar.startsWith('http') ? sub.manager.avatar : 'http://localhost' + sub.manager.avatar) : userDefault" />
                                    <div class="info">
                                        <span class="name">{{ sub.manager.username }}</span>
                                        <span class="role">主管</span>
                                    </div>
                                </div>
                                <div class="empty-sub-manager" v-else>
                                    <span style="font-size:12px;color:#ccc">无主管</span>
                                </div>
                           </div>
                           
                           <!-- 子部门成员 -->
                           <div class="sub-members-grid" v-if="sub.members && sub.members.length">
                               <div class="vertical-line"></div>
                               <div class="members-row">
                                   <div class="user-card member small" v-for="user in sub.members" :key="user.id">
                                        <el-avatar :size="30" :src="user.avatar ? (user.avatar.startsWith('http') ? user.avatar : 'http://localhost' + user.avatar) : userDefault" />
                                        <div class="info">
                                            <span class="name">{{ user.username }}</span>
                                        </div>
                                   </div>
                               </div>
                           </div>
                       </div>
                   </div>

                   <!-- 3. 当前部门直属成员 (仅当没有子部门时显示，即叶子节点部门，或者用户要求一级部门不显示直属成员) -->
                   <div class="direct-members-container" v-if="(!chartData.subDepts || chartData.subDepts.length === 0) && chartData.members && chartData.members.length">
                        <!-- 如果没有子部门，直接显示在下方 -->
                        <div class="members-grid">
                             <div class="user-card member" v-for="user in chartData.members" :key="user.id">
                                <el-avatar :size="36" :src="user.avatar ? (user.avatar.startsWith('http') ? user.avatar : 'http://localhost' + user.avatar) : userDefault" />
                                <div class="info">
                                    <span class="name">{{ user.username }}</span>
                                    <span class="role text-ellipsis">{{ user.role || '员工' }}</span>
                                </div>
                             </div>
                        </div>
                   </div>
                </div>
            </div>
            <el-alert title="说明: 图谱展示所选部门负责人 -> 子部门(及其成员) / 直属成员。" type="info" :closable="false" style="margin-top:20px"/>
        </div>

        <el-table v-else :data="deptEmployees" style="width: 100%" v-loading="loadingEmployees">
           <el-table-column prop="username" label="姓名">
               <template #default="scope">
                   <div style="display:flex;align-items:center;gap:8px">
                       <el-avatar :size="30" :src="scope.row.avatar ? (scope.row.avatar.startsWith('http') ? scope.row.avatar : 'http://localhost' + scope.row.avatar) : userDefault" />
                       {{ scope.row.username }}
                   </div>
               </template>
           </el-table-column>
           <el-table-column prop="role" label="职位" />
           <el-table-column label="所属部门">
               <template #default="scope">{{ scope.row.department }}</template>
           </el-table-column>
        </el-table>
      </el-card>
      <el-empty v-else description="请点击左侧部门查看详情" />
    </div>

    <el-dialog v-model="dialogVisible" title="新增部门" width="400px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="部门名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="上级部门">
          <el-input v-model="parentName" disabled />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitDept">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog v-model="managerDialogVisible" title="设置部门负责人" width="400px">
      <el-form :model="managerForm" label-width="80px">
        <el-form-item label="部门">
          <el-input v-model="currentDeptName" disabled />
        </el-form-item>
        <el-form-item label="负责人">
          <el-select v-model="managerForm.managerId" placeholder="选择负责人" filterable style="width: 100%">
             <el-option label="无" :value="null" />
             <el-option v-for="u in userList" :key="u.id" :label="u.username" :value="u.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
           <el-button @click="managerDialogVisible = false">取消</el-button>
           <el-button type="primary" @click="submitManager">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog v-model="editDialogVisible" title="编辑部门" width="400px">
      <el-form :model="editForm" label-width="80px">
          <el-form-item label="名称">
              <el-input v-model="editForm.name"></el-input>
          </el-form-item>

      </el-form>
      <template #footer>
          <span class="dialog-footer">
             <el-button @click="editDialogVisible = false">取消</el-button>
             <el-button type="primary" @click="submitEditDept">确定</el-button>
          </span>
      </template>
    </el-dialog>
  </div>

</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '../api/request'
import { ElMessage } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { fetchUsers } from '../api/admin'


import userDefault from '@/assets/user.png'

const deptTree = ref([])
const dialogVisible = ref(false)
const form = ref({ name: '', parentId: null })
const parentName = ref('')

const userList = ref([])
const managerDialogVisible = ref(false)
const managerForm = ref({ managerId: null })
const currentDeptId = ref(null)
const currentDeptName = ref('')

const loadTree = async () => {
  try {
    const res = await request.get('/org/departments/tree')
    deptTree.value = res
  } catch (e) {
    console.error(e)
  }
}

const loadUsers = async () => {
    try {
        userList.value = await request.get('/users/')
    } catch(e) {}
}

const openAddDept = (parent) => {
  form.value = { name: '', parentId: parent ? parent.id : null }
  parentName.value = parent ? parent.label : '无 (一级部门)'
  dialogVisible.value = true
}

const openSetManager = async (data) => {
    currentDeptId.value = data.id
    currentDeptName.value = data.label
    managerForm.value = { managerId: data.managerId }
    managerDialogVisible.value = true
    // Only load users for this department
    try {
        const res = await fetchUsers({ departmentId: data.id })
        userList.value = res
    } catch(e) {
        userList.value = []
    }
}

const submitManager = async () => {
    // if (!managerForm.value.managerId) return ElMessage.warning('请选择负责人') 允许设置为空
    try {
        await request.put(`/org/departments/${currentDeptId.value}`, { managerId: managerForm.value.managerId })

        ElMessage.success('设置成功')
        managerDialogVisible.value = false
        loadTree()
    } catch(e) {
        ElMessage.error('设置失败')
    }
}


const editDialogVisible = ref(false)
const editForm = ref({ id: null, name: '' })

const openEditDept = (data) => {
    editForm.value = { id: data.id, name: data.label }
    editDialogVisible.value = true
}


// Drag and Drop Logic
const allowDrag = (draggingNode) => {
    return true
}

const allowDrop = (draggingNode, dropNode, type) => {
    // 仅允许同级排序 (prev/next)，不允许成为子节点 (inner)
    // 且必须是同一父节点下的节点之间
    if (type === 'inner') return false
    return draggingNode.parent.id === dropNode.parent.id
}

const handleDrop = async (draggingNode, dropNode, dropType, ev) => {
    // 此时 Element Plus 已经完成了 UI 层面和 data 数据的移动
    // 我们只需要获取新的排序列表发给后端
    
    // 获取当前层级的所有节点 (即 changingNode 的 parent 的 children)
    const parentNode = dropNode.parent
    const siblings = parentNode.childNodes
    
    // 构造 payload
    const payload = siblings.map((node, index) => ({
        id: node.data.id,
        // parentNode.data 是 undefined 或者是 对象（如果是根节点）
        // 如果是根节点，parent id 为 null
        // 关键：dropNode.data.parentId 也可能是旧的，我们需要取 parentNode 的 id
        // 如果 parentNode.level === 0，说明是根节点，parent_id = null
        parent_id: parentNode.level === 0 ? null : parentNode.data.id, 
        order: index
    }))
    
    try {
        await request.post('/org/departments/reorder', { nodes: payload })
        ElMessage.success('调整成功')
    } catch(e) {
        ElMessage.error('调整失败')
        loadTree() // 失败回滚
    }
}

// Right Panel Logic
const selectedDept = ref(null)
const deptEmployees = ref([])
const loadingEmployees = ref(false)
const viewMode = ref('chart')
const chartData = ref({})

const buildChartData = (dept, employees) => {
    // Find manager
    const manager = employees.find(u => u.id === dept.managerId)
    const members = employees.filter(u => u.id !== dept.managerId)
    
    return {
        manager: manager ? { ...manager, role_name: '部门主管' } : null,
        members: members
    }
}


const handleNodeClick = async (data) => {
    selectedDept.value = data
    loadingEmployees.value = true
    try {
        // Fetch users in this department
        const res = await fetchUsers({ departmentId: data.id })
        deptEmployees.value = res
        // Build chart data
        // Need to know who is manager. data.managerId is available
        // Build chart data
        // For rendering sub-depts structure, we need to fetch users/managers for sub-departments
        const subDeptsData = []
        if (data.children && data.children.length > 0) {
             for (const child of data.children) {
                  try {
                      const childUsers = await fetchUsers({ departmentId: child.id })
                      const childManager = childUsers.find(u => u.id === child.managerId)
                      const childMembers = childUsers.filter(u => u.id !== child.managerId)
                      subDeptsData.push({
                          id: child.id,
                          name: child.label,
                          manager: childManager,
                          members: childMembers
                      })
                  } catch(e) {}
             }
        }
        
        chartData.value = {
             manager: res.find(u => u.id === data.managerId),
             members: res.filter(u => u.id !== data.managerId),
             subDepts: subDeptsData
        }

    } catch(e) {
        console.error(e)
    } finally {
        loadingEmployees.value = false
    }
}

const handleCommand = (command, data) => {
    if (command === 'manager') openSetManager(data)
    if (command === 'edit') openEditDept(data)
    if (command === 'add') openAddDept(data)
    if (command === 'delete') handleDeleteDept(data)
}


const submitEditDept = async () => {
    try {
        await request.put(`/org/departments/${editForm.value.id}`, { name: editForm.value.name, order: editForm.value.order })
        ElMessage.success('更新成功')
        editDialogVisible.value = false
        loadTree()
    } catch(e) {
        ElMessage.error('更新失败')
    }
}

const handleDeleteDept = (data) => {
    // Confirm
    if (confirm(`确定删除部门 ${data.label} 吗？`)) {
        request.delete(`/org/departments/${data.id}`).then(() => {
            ElMessage.success('删除成功')
            loadTree()
        }).catch(e => {
            ElMessage.error(e.response?.data?.msg || '删除失败')
        })
    }
}

const submitDept = async () => {
  if (!form.value.name) return ElMessage.warning('请输入名称')
  try {
    await request.post('/org/departments', form.value)
    ElMessage.success('创建成功')
    dialogVisible.value = false
    loadTree()
  } catch (e) {
    ElMessage.error(e.response?.data?.msg || '失败')
  }
}

onMounted(() => {
  loadTree()
})

</script>

<style scoped>
.org-container {
  display: flex;
  gap: 20px;
  height: calc(100vh - 120px);
}
.tree-card {
  flex: 1;
  overflow-y: auto;
}
.right-panel {
  flex: 2;
  background: var(--el-bg-color);
  border-radius: 4px;
  overflow-y: auto;
}
.dept-detail-card {
    height: 100%;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.custom-tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  padding-right: 8px;
}
.node-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.org-chart-container {
    display: flex;
    flex-direction: column;
.org-chart-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 10px 20px;
    overflow-x: auto; /* Enable scroll on container */
    min-width: 100%; /* Ensure container takes full width */
}

.tree-chart-node {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: max-content; /* Allow node to expand beyond 100% to trigger scroll */
    min-width: 100%;
}

.user-card {
    border: 1px solid #e4e7ed;
    border-radius: 8px;
    padding: 10px;
    display: flex;
    flex-direction: column;
    align-items: center;
    background: transparent;
    width: 100px;
    box-shadow: none;
    transition: all 0.3s;
}

.user-card:hover {
    /* transform: translateY(-2px); Disable to prevent jitter */
    /* box-shadow: 0 4px 8px rgba(0,0,0,0.1); */
    cursor: default;
}

.user-card.manager {
    /* border-top: 3px solid #409EFF; Removed blue stripe */
    background: transparent;
    border: 1px solid #e4e7ed; /* Keep basic border or remove if requested, keeping for consistency but removing top stripe */
    border-left: none;
    border-right: none;
    border-bottom: none;
    /* Actually user just said remove blue stripe. If we remove border-top, it has no border left (since others are none). */
    /* Let's remove specific manager styling that adds borders */
    border: none; 
}
    box-shadow: none;
}
.user-card.manager:hover {
    /* Transform disabled */
    transform: none;
    box-shadow: none;
    background: transparent;
    cursor: default;
}

.children-container {
    display: flex;
    justify-content: center;
    padding-top: 20px;
    position: relative;
    width: 100%;
}

.sub-depts-container {
    display: flex;
    flex-wrap: nowrap;
    /* Removed gap to allow border lines to touch */
    /* gap: 40px; */ 
    padding-top: 15px; /* Reduced space for bridge */
}

/* 一级主管下方的竖线 */
/* 一级主管下方的竖线 */
.tree-chart-node.root > .user-card.manager::after {
    content: '';
    position: absolute;
    bottom: -15px; /* Reduced length */
    left: 50%;
    width: 1px;
    height: 15px; /* Reduced height */
    background-color: #dcdfe6;
}

/* 分隔线作为横向连接线的容器（可选，这里用伪元素实现树状连接线更标准） */
/* 我们使用标准的 CSS Tree 伪元素法 */

.sub-dept-branch {
    position: relative;
    padding: 20px 20px 0 20px; /* Use padding instead of gap for spacing */
    display: flex;
    flex-direction: column;
    align-items: center;
}

/* 所有分支顶部的竖线 (从横线向下连到子部门主管) */
.sub-dept-branch::before {
    content: '';
    position: absolute;
    top: 0;
    left: 50%;
    border-left: 1px solid #dcdfe6;
    height: 20px;
    width: 0;
}

/* 所有分支顶部的横线 */
.sub-dept-branch::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 20px;
    border-top: 1px solid #dcdfe6;
}
.sub-dept-branch:first-child::after {
    left: 50%;
    width: 50%;
}
.sub-dept-branch:last-child::after {
    width: 50%;
}
/* 如果只有一个子部门，不需要横线，只需竖线 */
.sub-dept-branch:only-child::after {
    display: none;
}
.sub-dept-branch:only-child {
    padding-top: 20px;
}

/* 连接二级主管和成员的线 */
/* 连接二级主管和成员的线 */
.user-card.sub-manager {
    border: 1px solid #dcdfe6;
    background: transparent; /* 去背景 */
    width: auto; /* Auto width to fit five chars */
    min-width: 90px;
    padding: 5px 15px;
    white-space: nowrap;
    position: relative;
    z-index: 1;
    margin-bottom: 20px; /* 留出连接线的空间 */
}

/* 二级主管下方的竖线 */
.user-card.sub-manager::after {
    content: '';
    position: absolute;
    bottom: -20px;
    left: 50%;
    width: 1px;
    height: 20px;
    background-color: #dcdfe6;
    /* 仅当有成员时显示 */
    display: none; 
}
/* 如果有成员容器，则显示主管下方的线 */
.sub-dept-branch:has(.sub-members-grid) .user-card.sub-manager::after {
    display: block;
}
/* 兼容性写法 (如果不支持 :has) */
/* 可以简单地让 sub-members-grid 顶部有个线 */

.sub-members-grid {
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
}
/* 子部门主管和成员之间的连线 */
.sub-members-grid::before {
    content: '';
    position: absolute;
    top: -20px; /* 向上延伸到主管底部 */
    left: 50%;
    width: 1px;
    height: 20px;
    background-color: #dcdfe6;
}

/* 成员列表顶部横线 (连接所有成员) */
.members-row {
    display: flex;
    gap: 10px;
    padding-top: 20px; /* 增加顶部间距，为横线留空间 */
    position: relative;
}

.members-row::before {
    content: '';
    position: absolute;
    top: 0;
    left: 30px; /* 从第一个成员中心开始 (60px/2) */
    right: 30px; /* 到最后一个成员中心结束 */
    border-top: 1px solid #dcdfe6;
}

/* 每个成员向上的连线 */
.user-card.member.small {
    position: relative;
}
.user-card.member.small::before {
    content: '';
    position: absolute;
    top: -20px; /* 连接到 members-row 的横线 */
    left: 50%;
    width: 1px;
    height: 20px;
    background-color: #dcdfe6;
}

/* 假如只有一个成员，特殊处理横线 */
.members-row:has(> .user-card.member.small:only-child)::before {
    display: none;
}
.members-row:has(> .user-card.member.small:only-child) .user-card.member.small::before {
    height: 20px;
    top: -20px;
}


.user-card.member {
    background: transparent;
    border: none;
    box-shadow: none;
}
.user-card.member:hover {
    box-shadow: none;
    transform: none;
    background: rgba(0,0,0,0.02);
}

.user-card .info {
    margin-top: 8px;
    text-align: center;
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.user-card .name {
    font-weight: bold;
    font-size: 14px;
    color: #303133;
}

.user-card .role {
    font-size: 12px;
    color: #909399;
}

.divider {
    height: 30px;
    width: 1px;
    background: #dcdfe6;
    margin: 10px 0;
}

.members-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    justify-content: center;
    position: relative;
}

/* Connectors for members */
.members-grid::before {
    content: '';
    position: absolute;
    top: -10px;
    left: 20px;
    right: 20px;
    height: 1px;
    background: #dcdfe6;
}

.members-grid::after {
    content: '';
    position: absolute;
    top: -10px;
    left: 50%;
    height: 10px;
    width: 1px;
    background: #dcdfe6;
}
</style>



/*.custom-css*/

/* hot fixes 2 */


/*.sub-depts-container*/













