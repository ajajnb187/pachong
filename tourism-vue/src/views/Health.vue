<template>
  <div class="health-container">
    <div class="control-header">
      <div class="header-left">
        <div class="title-box">
          <el-icon class="icon-pulse"><Monitor /></el-icon>
          <span class="main-title">系统健康监控</span>
        </div>
      </div>
      <el-button type="primary" @click="fetchHealthData" :loading="loading">
        <el-icon><Refresh /></el-icon> 刷新状态
      </el-button>
    </div>

    <el-row :gutter="24">
      <el-col :xs="24" :md="12">
        <div class="tech-panel">
          <div class="panel-header">
            <div class="header-title">
              <el-icon class="icon"><Platform /></el-icon>
              <span class="title">应用服务状态</span>
            </div>
          </div>
          <div class="panel-body" v-loading="loading">
            <div v-if="appHealth" class="health-info">
              <div class="status-badge" :class="appHealth.status">
                <el-icon><CircleCheck v-if="appHealth.status === 'UP'" /><CircleClose v-else /></el-icon>
                {{ appHealth.status }}
              </div>
              <div class="info-grid">
                <div class="info-item">
                  <span class="label">服务名称</span>
                  <span class="value">{{ appHealth.service }}</span>
                </div>
                <div class="info-item">
                  <span class="label">版本号</span>
                  <span class="value">{{ appHealth.version }}</span>
                </div>
              </div>
            </div>
          </div>
          <i class="corner t-l"></i><i class="corner t-r"></i>
          <i class="corner b-l"></i><i class="corner b-r"></i>
        </div>
      </el-col>

      <el-col :xs="24" :md="12">
        <div class="tech-panel">
          <div class="panel-header">
            <div class="header-title">
              <el-icon class="icon"><DataAnalysis /></el-icon>
              <span class="title">Hive连接状态</span>
            </div>
          </div>
          <div class="panel-body" v-loading="loading">
            <div v-if="hiveHealth" class="health-info">
              <div class="status-badge" :class="hiveHealth.status === 'SUCCESS' ? 'UP' : 'DOWN'">
                <el-icon>
                  <CircleCheck v-if="hiveHealth.status === 'SUCCESS'" />
                  <CircleClose v-else />
                </el-icon>
                {{ hiveHealth.status }}
              </div>
              <div class="info-grid">
                <div class="info-item">
                  <span class="label">连接状态</span>
                  <span class="value">{{ hiveHealth.hiveConnected ? '已连接' : '未连接' }}</span>
                </div>
                <div class="info-item">
                  <span class="label">评论数据量</span>
                  <span class="value">{{ formatNumber(hiveHealth.totalReviews) }}</span>
                </div>
                <div class="info-item full">
                  <span class="label">消息</span>
                  <span class="value">{{ hiveHealth.message }}</span>
                </div>
              </div>
            </div>
          </div>
          <i class="corner t-l"></i><i class="corner t-r"></i>
          <i class="corner b-l"></i><i class="corner b-r"></i>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Monitor, Refresh, Platform, DataAnalysis, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import axios from 'axios'

const loading = ref(false)
const appHealth = ref(null)
const hiveHealth = ref(null)

const fetchHealthData = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('token')
    
    const [appRes, hiveRes] = await Promise.all([
      axios.get('/api/health', { headers: { Authorization: `Bearer ${token}` } }),
      axios.get('/api/health/hive', { headers: { Authorization: `Bearer ${token}` } })
    ])

    if (appRes.data.code === 200) {
      appHealth.value = appRes.data.data
    }
    
    if (hiveRes.data.code === 200) {
      hiveHealth.value = hiveRes.data.data
    }
  } catch (error) {
    console.error('获取健康状态失败:', error)
    ElMessage.error('获取系统健康状态失败')
  } finally {
    loading.value = false
  }
}

const formatNumber = (num) => {
  return num ? num.toLocaleString() : '0'
}

onMounted(() => {
  fetchHealthData()
})
</script>

<style scoped lang="scss">
$primary: #00f2fe;
$bg-panel: rgba(13, 27, 62, 0.65);
$border-color: rgba(0, 242, 254, 0.25);
$text-main: #fff;
$text-sub: #8fb6e6;

.health-container {
  min-height: 100vh;
  padding: 20px;
  background: radial-gradient(circle at 50% 10%, rgba(0, 242, 254, 0.05) 0%, transparent 60%),
              linear-gradient(180deg, #050a1f 0%, #02040d 100%);
  color: $text-main;
}

.control-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;

  .header-left {
    .title-box {
      display: flex;
      align-items: center;
      gap: 10px;
      .icon-pulse { color: $primary; font-size: 24px; }
      .main-title { font-size: 24px; font-weight: bold; color: #fff; }
    }
  }
}

.tech-panel {
  background: $bg-panel;
  border: 1px solid $border-color;
  position: relative;
  margin-bottom: 20px;
  min-height: 250px;

  .corner {
    position: absolute;
    width: 10px; height: 10px;
    border: 2px solid $primary;
    &.t-l { top: -1px; left: -1px; border-width: 2px 0 0 2px; }
    &.t-r { top: -1px; right: -1px; border-width: 2px 2px 0 0; }
    &.b-l { bottom: -1px; left: -1px; border-width: 0 0 2px 2px; }
    &.b-r { bottom: -1px; right: -1px; border-width: 0 2px 2px 0; }
  }

  .panel-header {
    height: 50px;
    padding: 0 20px;
    display: flex;
    align-items: center;
    background: rgba(255, 255, 255, 0.02);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);

    .header-title {
      display: flex; align-items: center; gap: 8px;
      .icon { color: $primary; font-size: 18px; }
      .title { color: #fff; font-size: 16px; font-weight: 600; }
    }
  }

  .panel-body {
    padding: 30px;
  }
}

.health-info {
  .status-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border-radius: 20px;
    font-weight: bold;
    margin-bottom: 20px;

    &.UP {
      background: rgba(67, 233, 123, 0.15);
      color: #43e97b;
      border: 1px solid rgba(67, 233, 123, 0.3);
    }

    &.DOWN {
      background: rgba(245, 108, 108, 0.15);
      color: #f56c6c;
      border: 1px solid rgba(245, 108, 108, 0.3);
    }
  }

  .info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;

    .info-item {
      display: flex;
      flex-direction: column;
      gap: 5px;

      &.full {
        grid-column: 1 / -1;
      }

      .label {
        font-size: 12px;
        color: $text-sub;
      }

      .value {
        font-size: 16px;
        color: #fff;
        font-weight: 500;
      }
    }
  }
}
</style>
