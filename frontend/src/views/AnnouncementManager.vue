<template>
  <div class="announcement-manager">
    <div class="header">
      <h3>公告管理</h3>
      <el-button type="primary" @click="openCreateDialog">发布公告</el-button>
    </div>
    
    <el-table :data="notices" style="width: 100%" v-loading="loading">
       <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
       <el-table-column prop="level" label="等级" width="100">
         <template #default="{ row }">
            <el-tag :type="row.level === 'important' ? 'danger' : 'primary'">
                {{ row.level === 'important' ? '重要' : '普通' }}
            </el-tag>
         </template>
       </el-table-column>
       <el-table-column prop="created_at" label="发布时间" width="180">
          <template #default="{ row }">
             {{ formatTime(row.created_at) }}
          </template>
       </el-table-column>
       <el-table-column label="操作" width="180" align="right">
          <template #default="{ row }">
             <el-button link type="primary" :icon="Edit" @click="openEditDialog(row)">编辑</el-button>
             <el-button link type="danger" :icon="Delete" @click="handleDelete(row)">删除</el-button>
          </template>
       </el-table-column>
    </el-table>

    <!-- Dialog -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑公告' : '发布公告'" width="500px">
        <el-form :model="form" label-width="80px" :rules="rules" ref="formRef">
            <el-form-item label="标题" prop="title">
                <el-input v-model="form.title" placeholder="请输入标题"></el-input>
            </el-form-item>
            <el-form-item label="等级" prop="level">
                <el-radio-group v-model="form.level">
                    <el-radio label="normal">普通 <el-tag size="small" type="primary">蓝色</el-tag></el-radio>
                    <el-radio label="important">重要 <el-tag size="small" type="danger">红色</el-tag></el-radio>
                </el-radio-group>
            </el-form-item>
            <el-form-item label="内容" prop="content">
                <el-input type="textarea" v-model="form.content" rows="6" placeholder="请输入正文"></el-input>
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="dialogVisible = false">取消</el-button>
            <el-button type="primary" @click="submitForm" :loading="submitting">确定</el-button>
        </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getNotices, createNotice, updateNotice, deleteNotice } from '../api/notice'
import { Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'

const notices = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const submitting = ref(false)
const isEdit = ref(false)
const formRef = ref(null)

const form = ref({
    id: null,
    title: '',
    content: '',
    level: 'normal'
})

const rules = {
    title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
    content: [{ required: true, message: '请输入内容', trigger: 'blur' }]
}

const loadData = async () => {
    loading.value = true
    try {
        const res = await getNotices()
        notices.value = res
    } catch(e) {
        ElMessage.error('加载失败')
    } finally {
        loading.value = false
    }
}

const openCreateDialog = () => {
    isEdit.value = false
    form.value = { title: '', content: '', level: 'normal' }
    dialogVisible.value = true
}

const openEditDialog = (row) => {
    isEdit.value = true
    form.value = { ...row }
    dialogVisible.value = true
}

const submitForm = async () => {
    if (!formRef.value) return
    await formRef.value.validate(async (valid) => {
        if (valid) {
            submitting.value = true
            try {
                if (isEdit.value) {
                    await updateNotice(form.value.id, form.value)
                    ElMessage.success('更新成功')
                } else {
                    await createNotice(form.value)
                    ElMessage.success('发布成功')
                }
                dialogVisible.value = false
                loadData()
            } catch(e) {
                console.error(e)
                ElMessage.error(isEdit.value ? '更新失败' : '发布失败')
            } finally {
                submitting.value = false
            }
        }
    })
}

const handleDelete = (row) => {
    ElMessageBox.confirm('确定删除该公告吗？', '提示', { type: 'warning' })
    .then(async () => {
        try {
            await deleteNotice(row.id)
            ElMessage.success('删除成功')
            loadData()
        } catch(e) {
            ElMessage.error('删除失败')
        }
    })
}

const formatTime = (iso) => dayjs(iso).format('YYYY-MM-DD HH:mm')

onMounted(() => {
    loadData()
})
</script>

<style scoped>
.announcement-manager {
    padding: 20px;
    background: var(--el-bg-color);
    border-radius: 4px;
    height: 100%;
    overflow-y: auto;
}
.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}
</style>
