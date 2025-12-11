<template>
  <div class="data-crawler">
    <!-- 系统状态卡片 -->
    <el-row :gutter="20" class="status-row">
      <el-col :xs="24" :sm="12" :md="6" v-for="stat in systemStats" :key="stat.label">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon" :style="{ background: stat.color }">
              <el-icon :size="24"><component :is="stat.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 操作区域 -->
    <el-row :gutter="20">
      <el-col :xs="24" :lg="16">
        <!-- 任务列表 -->
        <el-card class="task-list-card">
          <template #header>
            <div class="card-header">
              <span>爬取任务列表</span>
              <div class="header-actions">
                <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
                  创建任务
                </el-button>
                <el-button type="success" :icon="Download" @click="handleAdminCrawl">
                  一键爬取福州
                </el-button>
                <el-button :icon="Refresh" @click="fetchTaskList" circle />
              </div>
            </div>
          </template>
          
          <el-table :data="taskList" stripe v-loading="tableLoading">
            <el-table-column prop="task_id" label="ID" width="60" />
            <el-table-column prop="task_name" label="任务名称" min-width="200" show-overflow-tooltip />
            <el-table-column prop="scenic_spot_name" label="景区" width="120" />
            <el-table-column prop="data_source" label="数据源" width="100">
              <template #default="{ row }">
                <el-tag>{{ row.data_source }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="actual_count" label="已爬取" width="100">
              <template #default="{ row }">
                {{ row.actual_count || 0 }} / {{ row.target_count }}
              </template>
            </el-table-column>
            <el-table-column prop="create_time" label="创建时间" width="160" />
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button
                  v-if="row.status === 'running'"
                  type="warning"
                  size="small"
                  :icon="VideoPause"
                  @click="handleStopTask(row.id)"
                >
                  停止
                </el-button>
                <el-button
                  type="primary"
                  size="small"
                  :icon="View"
                  @click="handleViewTask(row)"
                >
                  详情
                </el-button>
                <el-button
                  v-if="row.status !== 'running'"
                  type="danger"
                  size="small"
                  :icon="Delete"
                  @click="handleDeleteTask(row.id)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="fetchTaskList"
            @current-change="fetchTaskList"
            class="pagination"
          />
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="8">
        <!-- 快速操作 -->
        <el-card class="quick-actions-card">
          <template #header>
            <div class="card-header">
              <span>快速操作</span>
              <el-icon><Setting /></el-icon>
            </div>
          </template>
          
          <div class="quick-actions">
            <el-button type="primary" :icon="Plus" @click="showCreateDialog = true" class="action-btn">
              创建爬取任务
            </el-button>
            <el-button type="success" :icon="Download" @click="handleAdminCrawl" class="action-btn">
              一键爬取福州所有景区
            </el-button>
            <el-button :icon="Refresh" @click="fetchTaskList" class="action-btn">
              刷新任务列表
            </el-button>
            <el-button :icon="Monitor" @click="fetchSystemStatus" class="action-btn">
              刷新系统状态
            </el-button>
          </div>
          
          <el-divider />
          
          <div class="info-section">
            <h4>数据源信息</h4>
            <div v-for="source in dataSources" :key="source.source_code" class="info-item">
              <el-tag :type="source.is_enabled ? 'success' : 'info'">
                {{ source.source_name }}
              </el-tag>
              <span class="info-note">{{ source.note }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 创建任务对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建爬取任务"
      width="600px"
      @close="resetCreateForm"
    >
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="120px">
        <el-form-item label="任务名称" prop="task_name">
          <el-input v-model="createForm.task_name" placeholder="请输入任务名称" />
        </el-form-item>
        
        <el-form-item label="景区名称" prop="scenic_spot_name">
          <el-input v-model="createForm.scenic_spot_name" placeholder="例如：三坊七巷" />
        </el-form-item>
        
        <el-form-item label="数据源" prop="data_source">
          <el-select v-model="createForm.data_source" placeholder="选择数据源" style="width: 100%">
            <el-option
              v-for="source in dataSources"
              :key="source.source_code"
              :label="source.source_name"
              :value="source.source_code"
              :disabled="!source.is_enabled"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="数据类型" prop="data_type">
          <el-select v-model="createForm.data_type" placeholder="选择数据类型" style="width: 100%">
            <el-option label="评论数据" value="review" />
            <el-option label="景区信息" value="info" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="目标数量" prop="target_count">
          <el-input-number
            v-model="createForm.target_count"
            :min="1"
            :max="10000"
            :step="100"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateTask" :loading="createLoading">
          创建并启动
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 任务详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="任务详情"
      width="700px"
    >
      <el-descriptions :column="2" border v-if="currentTask">
        <el-descriptions-item label="任务ID">{{ currentTask.id }}</el-descriptions-item>
        <el-descriptions-item label="任务名称">{{ currentTask.task_name }}</el-descriptions-item>
        <el-descriptions-item label="景区名称">{{ currentTask.scenic_spot_name }}</el-descriptions-item>
        <el-descriptions-item label="数据源">{{ currentTask.data_source }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentTask.status)">
            {{ getStatusText(currentTask.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="进度">
          {{ currentTask.crawled_count || 0 }} / {{ currentTask.target_count }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间" :span="2">
          {{ currentTask.create_time }}
        </el-descriptions-item>
        <el-descriptions-item label="开始时间" :span="2">
          {{ currentTask.start_time || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="结束时间" :span="2">
          {{ currentTask.end_time || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="输出文件" :span="2">
          {{ currentTask.output_file || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="错误信息" :span="2">
          {{ currentTask.error_msg || '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import {
  Plus, Refresh, Delete, View, VideoPause, Download, Monitor, Setting
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  startCrawlTaskAPI,
  getTaskListAPI,
  stopTaskAPI,
  deleteTaskAPI,
  getDataSourceListAPI,
  adminCrawlFuzhouAPI,
  getSystemStatusAPI
} from '@/api/crawler'

const systemStats = ref([
  { label: '运行中任务', value: 0, icon: 'VideoPlay', color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
  { label: '等待中任务', value: 0, icon: 'Clock', color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' },
  { label: '今日完成', value: 0, icon: 'CircleCheck', color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' },
  { label: '系统状态', value: 'running', icon: 'Monitor', color: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' }
])

const taskList = ref([])
const dataSources = ref([])
const tableLoading = ref(false)
const createLoading = ref(false)
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const currentTask = ref(null)

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const createForm = reactive({
  task_name: '',
  scenic_spot_name: '',
  data_source: 'ctrip',
  data_type: 'review',
  target_count: 500
})

const createFormRef = ref(null)

const createRules = {
  task_name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  scenic_spot_name: [{ required: true, message: '请输入景区名称', trigger: 'blur' }],
  data_source: [{ required: true, message: '请选择数据源', trigger: 'change' }],
  data_type: [{ required: true, message: '请选择数据类型', trigger: 'change' }],
  target_count: [{ required: true, message: '请输入目标数量', trigger: 'blur' }]
}

let refreshTimer = null

const fetchTaskList = async () => {
  tableLoading.value = true
  try {
    const res = await getTaskListAPI({
      page: pagination.page,
      page_size: pagination.pageSize
    })
    if (res.data) {
      taskList.value = res.data.tasks
      pagination.total = res.data.total
    }
  } catch (error) {
    console.error('获取任务列表失败:', error)
  } finally {
    tableLoading.value = false
  }
}

const fetchDataSources = async () => {
  try {
    const res = await getDataSourceListAPI()
    if (res.data) {
      dataSources.value = res.data
    }
  } catch (error) {
    console.error('获取数据源失败:', error)
  }
}

const fetchSystemStatus = async () => {
  try {
    const res = await getSystemStatusAPI()
    if (res.data) {
      systemStats.value[0].value = res.data.running_tasks || 0
      systemStats.value[1].value = res.data.pending_tasks || 0
      systemStats.value[2].value = res.data.today_completed_tasks || 0
      systemStats.value[3].value = res.data.service_status || 'unknown'
    }
  } catch (error) {
    console.error('获取系统状态失败:', error)
  }
}

const handleCreateTask = async () => {
  await createFormRef.value.validate(async (valid) => {
    if (valid) {
      createLoading.value = true
      try {
        const res = await startCrawlTaskAPI(createForm)
        if (res.code === 200) {
          ElMessage.success('任务创建成功！')
          showCreateDialog.value = false
          fetchTaskList()
          fetchSystemStatus()
        }
      } catch (error) {
        ElMessage.error(error.response?.data?.msg || '创建任务失败')
      } finally {
        createLoading.value = false
      }
    }
  })
}

const handleAdminCrawl = async () => {
  ElMessageBox.confirm(
    '确定要启动福州所有景区数据采集任务吗？此操作会爬取大量数据并存入Hadoop。',
    '确认操作',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      const res = await adminCrawlFuzhouAPI({ target_count: 500 })
      if (res.code === 200) {
        ElMessage.success('福州全景区采集任务已启动！')
        fetchTaskList()
        fetchSystemStatus()
      }
    } catch (error) {
      ElMessage.error(error.response?.data?.msg || '启动任务失败')
    }
  }).catch(() => {})
}

const handleStopTask = async (taskId) => {
  ElMessageBox.confirm('确定要停止该任务吗？', '确认操作', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await stopTaskAPI({ task_id: taskId })
      if (res.code === 200) {
        ElMessage.success('任务已停止')
        fetchTaskList()
        fetchSystemStatus()
      }
    } catch (error) {
      ElMessage.error(error.response?.data?.msg || '停止任务失败')
    }
  }).catch(() => {})
}

const handleDeleteTask = async (taskId) => {
  ElMessageBox.confirm('确定要删除该任务吗？', '确认操作', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await deleteTaskAPI(taskId)
      if (res.code === 200) {
        ElMessage.success('任务已删除')
        fetchTaskList()
      }
    } catch (error) {
      ElMessage.error(error.response?.data?.msg || '删除任务失败')
    }
  }).catch(() => {})
}

const handleViewTask = (task) => {
  currentTask.value = task
  showDetailDialog.value = true
}

const resetCreateForm = () => {
  createFormRef.value?.resetFields()
}

const getStatusType = (status) => {
  const typeMap = {
    pending: 'info',
    running: 'warning',
    success: 'success',
    failed: 'danger',
    stopped: 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    pending: '等待中',
    running: '运行中',
    success: '成功',
    failed: '失败',
    stopped: '已停止'
  }
  return textMap[status] || status
}

onMounted(() => {
  fetchTaskList()
  fetchDataSources()
  fetchSystemStatus()
  
  // 定时刷新任务列表
  refreshTimer = setInterval(() => {
    fetchTaskList()
    fetchSystemStatus()
  }, 5000)
})

onBeforeUnmount(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped lang="scss">
.data-crawler {
  .status-row {
    margin-bottom: 20px;
    
    .stat-card {
      cursor: pointer;
      transition: transform 0.3s;
      
      &:hover {
        transform: translateY(-5px);
      }
      
      .stat-content {
        display: flex;
        align-items: center;
        gap: 12px;
        
        .stat-icon {
          width: 48px;
          height: 48px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #fff;
        }
        
        .stat-info {
          flex: 1;
          
          .stat-value {
            font-size: 20px;
            font-weight: 600;
            color: #303133;
            margin-bottom: 4px;
          }
          
          .stat-label {
            font-size: 12px;
            color: #909399;
          }
        }
      }
    }
  }
  
  .task-list-card {
    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-weight: 600;
      
      .header-actions {
        display: flex;
        gap: 8px;
      }
    }
    
    .pagination {
      margin-top: 20px;
      justify-content: flex-end;
    }
  }
  
  .quick-actions-card {
    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-weight: 600;
    }
    
    .quick-actions {
      display: flex;
      flex-direction: column;
      gap: 12px;
      
      .action-btn {
        width: 100%;
        justify-content: flex-start;
      }
    }
    
    .info-section {
      h4 {
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 12px;
        color: #303133;
      }
      
      .info-item {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
        
        .info-note {
          font-size: 12px;
          color: #909399;
        }
      }
    }
  }
}
</style>
