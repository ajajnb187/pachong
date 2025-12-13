<template>
  <div class="crawler-container">
    <!-- 顶部状态监控区 (HUD风格) -->
    <div class="dashboard-header">
      <div
          class="status-panel"
          v-for="(stat, index) in systemStats"
          :key="stat.label"
          :class="`delay-${index}`"
      >
        <div class="panel-decoration top-left"></div>
        <div class="panel-decoration bottom-right"></div>

        <div class="icon-box" :class="`type-${index}`">
          <el-icon :size="24"><component :is="stat.icon" /></el-icon>
        </div>
        <div class="info-box">
          <div class="value-text">{{ stat.value }}</div>
          <div class="label-text">{{ stat.label }}</div>
        </div>
        <!-- 动态扫描线 -->
        <div class="scan-line"></div>
      </div>
    </div>

    <!-- 主控区域 -->
    <el-row :gutter="24" class="main-workspace">
      <!-- 左侧：任务列表 -->
      <el-col :xs="24" :lg="16">
        <div class="tech-panel full-height">
          <div class="panel-header">
            <div class="header-title">
              <el-icon class="title-icon"><List /></el-icon>
              <span>数据采集任务队列</span>
            </div>
            <div class="header-controls">
              <el-button class="tech-btn icon-only" @click="fetchTaskList">
                <el-icon :class="{ 'spin-anim': tableLoading }"><Refresh /></el-icon>
              </el-button>
            </div>
          </div>

          <div class="panel-body">
            <el-table
                :data="taskList"
                v-loading="tableLoading"
                class="custom-table"
                element-loading-background="rgba(0, 0, 0, 0.5)"
            >
              <el-table-column prop="task_id" label="ID" width="70" />
              <el-table-column prop="task_name" label="任务标识" min-width="180">
                <template #default="{ row }">
                  <span class="highlight-text">{{ row.task_name }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="scenic_spot_name" label="目标景区" width="130" />
              <el-table-column prop="data_source" label="来源" width="100">
                <template #default="{ row }">
                  <span class="source-tag">{{ row.data_source }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="运行状态" width="110">
                <template #default="{ row }">
                  <div class="status-indicator" :class="row.status">
                    <span class="dot"></span>
                    {{ getStatusText(row.status) }}
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="actual_count" label="进度监控" width="140">
                <template #default="{ row }">
                  <div class="progress-info">
                    <span>{{ row.actual_count || 0 }}</span>
                    <span class="separator">/</span>
                    <span class="total">{{ row.target_count }}</span>
                  </div>
                  <el-progress
                      :percentage="Math.min(100, Math.round(((row.actual_count || 0) / row.target_count) * 100))"
                      :show-text="false"
                      :stroke-width="3"
                      :color="row.status === 'running' ? '#00f2fe' : '#4facfe'"
                  />
                </template>
              </el-table-column>
              <el-table-column label="指令控制" width="180" fixed="right" align="right">
                <template #default="{ row }">
                  <div class="action-group">
                    <el-tooltip content="停止" v-if="row.status === 'running'">
                      <span class="action-icon warning" @click="handleStopTask(row.id)"><VideoPause /></span>
                    </el-tooltip>
                    <el-tooltip content="查看详情">
                      <span class="action-icon info" @click="handleViewTask(row)"><View /></span>
                    </el-tooltip>
                    <el-tooltip content="删除记录" v-if="row.status !== 'running'">
                      <span class="action-icon danger" @click="handleDeleteTask(row.id)"><Delete /></span>
                    </el-tooltip>
                  </div>
                </template>
              </el-table-column>
            </el-table>

            <div class="pagination-wrapper">
              <el-pagination
                  v-model:current-page="pagination.page"
                  v-model:page-size="pagination.pageSize"
                  :total="pagination.total"
                  :page-sizes="[10, 20, 50]"
                  layout="prev, pager, next, total"
                  @size-change="fetchTaskList"
                  @current-change="fetchTaskList"
                  background
              />
            </div>
          </div>
        </div>
      </el-col>

      <!-- 右侧：控制台与信息 -->
      <el-col :xs="24" :lg="8">
        <div class="tech-panel control-panel">
          <div class="panel-header">
            <div class="header-title">
              <el-icon class="title-icon"><Setting /></el-icon>
              <span>系统指令集</span>
            </div>
          </div>
          <div class="panel-body">
            <div class="crawl-control-center">
              <div class="control-title">数据爬取控制台</div>
              <div class="control-form">
                <el-form :model="crawlForm" label-position="top" class="tech-form">
                  <el-form-item label="爬取数量 / Crawl Count">
                    <el-radio-group v-model="crawlForm.mode" class="crawl-radio-group">
                      <el-radio-button label="custom">指定数量</el-radio-button>
                      <el-radio-button label="all">全部爬取</el-radio-button>
                    </el-radio-group>
                  </el-form-item>
                  <el-form-item label="数量设置" v-if="crawlForm.mode === 'custom'">
                    <el-input-number
                        v-model="crawlForm.targetCount"
                        :min="10"
                        :max="10000"
                        :step="100"
                        style="width: 100%"
                        class="tech-number-input"
                    />
                  </el-form-item>
                </el-form>
                <el-button 
                    class="tech-btn success crawl-btn" 
                    @click="handleStartCrawl"
                    :loading="crawlLoading"
                    size="large"
                >
                  <el-icon><Download /></el-icon> 开始数据爬取
                </el-button>
              </div>
            </div>

            <div class="divider-glow"></div>

            <div class="data-source-monitor">
              <div class="sub-title">数据源连接状态</div>
              <div class="source-list">
                <div v-for="source in dataSources" :key="source.source_code" class="source-item">
                  <div class="source-info">
                    <span class="name">{{ source.source_name }}</span>
                    <span class="note">{{ source.note }}</span>
                  </div>
                  <div class="connection-status">
                    <div class="status-dot" :class="{ active: source.is_enabled }"></div>
                    <span>{{ source.is_enabled ? 'ONLINE' : 'OFFLINE' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 对话框样式重写 (通过class透传样式) -->
    <el-dialog
        v-model="showDetailDialog"
        title="任务运行日志"
        width="600px"
        class="tech-dialog"
    >
      <div class="detail-grid" v-if="currentTask">
        <div class="detail-item full">
          <label>任务ID</label>
          <span class="code-font">{{ currentTask.id }}</span>
        </div>
        <div class="detail-item">
          <label>任务名称</label>
          <span>{{ currentTask.task_name }}</span>
        </div>
        <div class="detail-item">
          <label>景区名称</label>
          <span>{{ currentTask.scenic_spot_name }}</span>
        </div>
        <div class="detail-item">
          <label>数据源</label>
          <span>{{ currentTask.data_source }}</span>
        </div>
        <div class="detail-item">
          <label>当前状态</label>
          <span :class="['status-text', currentTask.status]">{{ getStatusText(currentTask.status) }}</span>
        </div>
        <div class="detail-item full">
          <label>采集进度</label>
          <div class="detail-progress">
            <span>{{ currentTask.crawled_count || 0 }} / {{ currentTask.target_count }}</span>
            <div class="bar-bg"><div class="bar-fill" :style="{width: ((currentTask.crawled_count || 0) / currentTask.target_count * 100) + '%'}"></div></div>
          </div>
        </div>
        <div class="detail-item">
          <label>创建时间</label>
          <span>{{ currentTask.create_time }}</span>
        </div>
        <div class="detail-item">
          <label>开始时间</label>
          <span>{{ currentTask.start_time || '-' }}</span>
        </div>
        <div class="detail-item full">
          <label>HDFS存储路径</label>
          <span class="path-text">{{ currentTask.output_file || '等待生成...' }}</span>
        </div>
        <div class="detail-item full error" v-if="currentTask.error_msg">
          <label>系统异常日志</label>
          <span>{{ currentTask.error_msg }}</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
// 脚本逻辑保持不变，完全复用
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import {
  Plus, Refresh, Delete, View, VideoPause, Download, Monitor, Setting, List
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
  { label: '运行中任务', value: 0, icon: 'VideoPlay', color: '' },
  { label: '等待中任务', value: 0, icon: 'Clock', color: '' },
  { label: '今日完成', value: 0, icon: 'CircleCheck', color: '' },
  { label: '系统状态', value: 'running', icon: 'Monitor', color: '' }
])

const taskList = ref([])
const dataSources = ref([])
const tableLoading = ref(false)
const showDetailDialog = ref(false)
const currentTask = ref(null)

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const crawlForm = reactive({
  mode: 'custom',
  targetCount: 500
})

const crawlLoading = ref(false)

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

const handleStartCrawl = async () => {
  const targetCount = crawlForm.mode === 'all' ? 10000 : crawlForm.targetCount
  
  ElMessageBox.confirm(
      `确定要开始爬取${crawlForm.mode === 'all' ? '全部' : targetCount + '条'}数据吗？数据将自动存入Hadoop。`,
      '确认爬取',
      {
        confirmButtonText: '开始爬取',
        cancelButtonText: '取消',
        type: 'warning',
        customClass: 'tech-message-box'
      }
  ).then(async () => {
    crawlLoading.value = true
    try {
      const res = await adminCrawlFuzhouAPI({ target_count: targetCount })
      if (res.code === 200) {
        ElMessage.success('数据爬取任务已启动！')
        fetchTaskList()
        fetchSystemStatus()
      }
    } catch (error) {
      ElMessage.error(error.response?.data?.msg || '启动任务失败')
    } finally {
      crawlLoading.value = false
    }
  }).catch(() => {})
}

const handleStopTask = async (taskId) => {
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
}

const handleDeleteTask = async (taskId) => {
  ElMessageBox.confirm('确定要删除该任务吗？', '删除确认', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
    customClass: 'tech-message-box'
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

// 辅助函数保持逻辑
const getStatusText = (status) => {
  const textMap = {
    pending: '等待中',
    running: '采集运行中',
    success: '已完成',
    failed: '异常终止',
    stopped: '手动停止'
  }
  return textMap[status] || status
}

onMounted(() => {
  fetchTaskList()
  fetchDataSources()
  fetchSystemStatus()
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

<style lang="scss">
/* 全局覆盖 Element Plus 的 Dialog 和 Message Box 样式 - 必需放在scoped外面 */
.tech-overlay {
  background-color: rgba(0, 0, 0, 0.7) !important;
  backdrop-filter: blur(4px);
}

.tech-dialog, .tech-message-box {
  background: rgba(11, 21, 49, 0.95) !important;
  border: 1px solid #00f2fe !important;
  box-shadow: 0 0 30px rgba(0, 242, 254, 0.15) !important;

  .el-dialog__title, .el-message-box__title {
    color: #fff !important;
    font-weight: 600;
  }

  .el-dialog__body, .el-message-box__content {
    color: #a6b9d6 !important;
  }

  .el-dialog__headerbtn .el-dialog__close {
    color: #00f2fe !important;
    &:hover { transform: rotate(90deg); transition: 0.3s; }
  }
}

/* 下拉菜单样式覆盖 */
.tech-popper {
  background: rgba(11, 21, 49, 0.95) !important;
  border: 1px solid rgba(0, 242, 254, 0.3) !important;

  .el-select-dropdown__item {
    color: #a6b9d6 !important;
    &.selected { color: #00f2fe !important; font-weight: bold; }
    &:hover { background: rgba(0, 242, 254, 0.1) !important; }
  }
}
</style>

<style scoped lang="scss">
/* --- 变量定义 --- */
$primary: #00f2fe;
$secondary: #4facfe;
$bg-dark: #02040d;
$panel-bg: rgba(13, 27, 62, 0.7);
$border-color: rgba(0, 242, 254, 0.2);
$text-main: #fff;
$text-sub: #8fb6e6;

.crawler-container {
  min-height: 100vh;
  padding: 20px;
  background: radial-gradient(circle at 10% 20%, rgba(0, 242, 254, 0.05) 0%, transparent 40%),
  linear-gradient(180deg, #050a1f 0%, #02040d 100%);
  color: $text-main;
  font-family: 'Inter', 'Helvetica Neue', sans-serif;
}

/* --- 顶部 HUD 仪表盘 --- */
.dashboard-header {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.status-panel {
  position: relative;
  height: 100px;
  background: $panel-bg;
  border: 1px solid $border-color;
  display: flex;
  align-items: center;
  padding: 0 24px;
  overflow: hidden;
  transition: all 0.3s;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 0 20px rgba(0, 242, 254, 0.15);
    border-color: rgba(0, 242, 254, 0.6);
  }

  /* 扫描线动画 */
  .scan-line {
    position: absolute;
    top: 0;
    left: -100%;
    width: 20%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
    transform: skewX(-20deg);
    animation: scan 3s infinite linear;
  }

  /* 装饰角标 */
  .panel-decoration {
    position: absolute;
    width: 8px;
    height: 8px;
    border: 2px solid $primary;
    &.top-left { top: 0; left: 0; border-width: 2px 0 0 2px; }
    &.bottom-right { bottom: 0; right: 0; border-width: 0 2px 2px 0; }
  }

  .icon-box {
    width: 54px;
    height: 54px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 16px;
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(5px);

    /* 图标颜色区分 */
    &.type-0 { color: #00f2fe; box-shadow: 0 0 10px rgba(0, 242, 254, 0.2); }
    &.type-1 { color: #f093fb; box-shadow: 0 0 10px rgba(240, 147, 251, 0.2); }
    &.type-2 { color: #43e97b; box-shadow: 0 0 10px rgba(67, 233, 123, 0.2); }
    &.type-3 { color: #4facfe; box-shadow: 0 0 10px rgba(79, 172, 254, 0.2); }
  }

  .info-box {
    .value-text {
      font-family: 'DIN Alternate', sans-serif;
      font-size: 28px;
      font-weight: 700;
      text-shadow: 0 0 8px rgba(255,255,255,0.3);
    }
    .label-text {
      font-size: 13px;
      color: $text-sub;
      margin-top: 2px;
    }
  }
}

/* --- 通用面板样式 --- */
.tech-panel {
  background: $panel-bg;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  position: relative;
  margin-bottom: 20px;

  &.full-height {
    min-height: 600px;
  }

  .panel-header {
    height: 60px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    background: rgba(0, 0, 0, 0.2);

    .header-title {
      font-size: 16px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 10px;
      color: $primary;

      .title-icon { font-size: 18px; }
    }

    .header-controls {
      display: flex;
      gap: 10px;
    }
  }

  .panel-body {
    padding: 20px;
    flex: 1;
    overflow: hidden;
  }
}

/* --- 按钮系统 --- */
.tech-btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: $text-sub;
  padding: 8px 16px;
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 6px;

  &:hover {
    color: #fff;
    border-color: #fff;
  }

  &.primary {
    background: rgba(0, 242, 254, 0.15);
    border-color: $primary;
    color: $primary;
    &:hover { background: $primary; color: #000; box-shadow: 0 0 15px rgba(0, 242, 254, 0.4); }
  }

  &.success {
    background: rgba(67, 233, 123, 0.15);
    border-color: #43e97b;
    color: #43e97b;
    &:hover { background: #43e97b; color: #000; }
  }

  &.icon-only {
    padding: 8px;
    border-radius: 50%;
  }

  &.ghost {
    &:hover { background: rgba(255,255,255,0.1); }
  }
}

/* --- 自定义表格样式 --- */
.custom-table {
  /* 透明化背景 */
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(255, 255, 255, 0.05);
  --el-table-border-color: rgba(255, 255, 255, 0.08);
  --el-text-color-regular: #a6b9d6;
  --el-table-header-text-color: #fff;
  --el-table-row-hover-bg-color: rgba(0, 242, 254, 0.05);

  background: transparent !important;

  :deep(th.el-table__cell) {
    font-weight: 600;
    border-bottom: 1px solid rgba(0, 242, 254, 0.2) !important;
  }

  :deep(td.el-table__cell) {
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }

  .highlight-text { color: #fff; font-weight: 500; }

  .source-tag {
    background: rgba(79, 172, 254, 0.15);
    color: #4facfe;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    border: 1px solid rgba(79, 172, 254, 0.3);
  }

  .status-indicator {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;

    .dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #999;
      box-shadow: 0 0 5px currentColor;
    }

    &.running { color: $primary; .dot { background: $primary; animation: blink 1s infinite; } }
    &.success { color: #43e97b; .dot { background: #43e97b; } }
    &.failed { color: #ff4d4f; .dot { background: #ff4d4f; } }
    &.pending { color: #e6a23c; .dot { background: #e6a23c; } }
  }

  .progress-info {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    margin-bottom: 4px;
    .separator { color: rgba(255,255,255,0.3); }
    .total { color: rgba(255,255,255,0.5); }
  }

  .action-group {
    display: flex;
    justify-content: flex-end;
    gap: 12px;

    .action-icon {
      cursor: pointer;
      font-size: 16px;
      transition: all 0.3s;
      &.warning { color: #e6a23c; &:hover { text-shadow: 0 0 10px #e6a23c; } }
      &.info { color: $primary; &:hover { text-shadow: 0 0 10px $primary; } }
      &.danger { color: #ff4d4f; &:hover { text-shadow: 0 0 10px #ff4d4f; } }
    }
  }
}

/* --- 右侧控制台样式 --- */
.control-panel {
  .crawl-control-center {
    margin-bottom: 25px;
    
    .control-title {
      font-size: 15px;
      color: $primary;
      margin-bottom: 20px;
      padding-bottom: 10px;
      border-bottom: 1px solid rgba(0, 242, 254, 0.2);
      text-align: center;
      letter-spacing: 2px;
    }
    
    .control-form {
      .tech-form {
        margin-bottom: 20px;
        
        :deep(.el-form-item__label) {
          color: $text-sub;
          font-size: 13px;
          font-weight: 500;
        }
        
        .crawl-radio-group {
          width: 100%;
          display: flex;
          
          :deep(.el-radio-button) {
            flex: 1;
            
            .el-radio-button__inner {
              width: 100%;
              background: rgba(0, 0, 0, 0.3);
              border-color: rgba(255, 255, 255, 0.1);
              color: $text-sub;
              transition: all 0.3s;
              
              &:hover {
                background: rgba(0, 242, 254, 0.05);
                border-color: rgba(0, 242, 254, 0.3);
                color: $primary;
              }
            }
            
            &.is-active .el-radio-button__inner {
              background: rgba(0, 242, 254, 0.15);
              border-color: $primary;
              color: $primary;
              box-shadow: 0 0 10px rgba(0, 242, 254, 0.2);
            }
          }
        }
        
        :deep(.el-input-number) {
          .el-input__wrapper {
            background: rgba(0, 0, 0, 0.3);
            box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1);
            
            &.is-focus {
              box-shadow: 0 0 0 1px $primary;
            }
          }
          
          .el-input__inner {
            color: #fff;
            text-align: center;
            font-size: 16px;
            font-weight: bold;
          }
        }
      }
      
      .crawl-btn {
        width: 100%;
        height: 50px;
        font-size: 16px;
        font-weight: 600;
        letter-spacing: 1px;
      }
    }
  }

  .divider-glow {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
    margin: 20px 0;
  }

  .data-source-monitor {
    .sub-title {
      font-size: 14px;
      color: #fff;
      margin-bottom: 15px;
      padding-left: 10px;
      border-left: 3px solid $secondary;
    }

    .source-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px;
      margin-bottom: 8px;
      background: rgba(0, 0, 0, 0.2);
      border-radius: 4px;

      .source-info {
        display: flex;
        flex-direction: column;
        .name { color: #fff; font-size: 13px; }
        .note { color: rgba(255,255,255,0.4); font-size: 12px; }
      }

      .connection-status {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        color: rgba(255,255,255,0.6);

        .status-dot {
          width: 6px;
          height: 6px;
          background: #666;
          border-radius: 50%;
          &.active { background: #43e97b; box-shadow: 0 0 6px #43e97b; }
        }
      }
    }
  }
}

/* --- 表单与对话框内部 --- */
.tech-form {
  :deep(.el-form-item__label) { color: $text-sub; }

  :deep(.el-input__wrapper), :deep(.el-textarea__inner) {
    background: rgba(0, 0, 0, 0.3);
    box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1);
    &.is-focus { box-shadow: 0 0 0 1px $primary; }
  }

  :deep(.el-input__inner) { color: #fff; }
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;

  .detail-item {
    display: flex;
    flex-direction: column;
    gap: 5px;

    &.full { grid-column: span 2; }
    &.error span { color: #ff4d4f; }

    label { font-size: 12px; color: $text-sub; }
    span { color: #fff; font-size: 14px; }
    .code-font { font-family: monospace; color: $primary; }
    .path-text { color: #e6a23c; font-family: monospace; }

    .detail-progress {
      background: rgba(255,255,255,0.1);
      height: 24px;
      border-radius: 2px;
      position: relative;
      display: flex;
      align-items: center;
      padding: 0 8px;

      span { position: relative; z-index: 2; font-size: 12px; text-shadow: 0 0 2px #000; }
      .bar-bg { position: absolute; top:0; left:0; width:100%; height:100%; }
      .bar-fill { height: 100%; background: linear-gradient(90deg, rgba(0,242,254,0.2), rgba(0,242,254,0.6)); }
    }
  }
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;

  :deep(.el-pagination.is-background .el-pager li:not(.is-disabled).is-active) {
    background-color: $primary;
  }
  :deep(.el-pagination.is-background .el-pager li) {
    background-color: rgba(255,255,255,0.05);
    color: #fff;
  }
}

/* 动画 */
@keyframes scan { 0% { left: -100%; } 100% { left: 200%; } }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
.spin-anim { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* 响应式调整 */
@media (max-width: 768px) {
  .dashboard-header { grid-template-columns: 1fr; }
  .control-panel { margin-top: 20px; }
}
</style>