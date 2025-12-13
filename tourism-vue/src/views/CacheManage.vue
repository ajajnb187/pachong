<template>
  <div class="cache-container">
    <div class="control-header">
      <div class="header-left">
        <div class="title-box">
          <el-icon class="icon-pulse"><Coin /></el-icon>
          <span class="main-title">缓存管理中心</span>
        </div>
      </div>
    </div>

    <el-row :gutter="24">
      <el-col :xs="24" :md="8">
        <div class="tech-panel action-panel">
          <div class="panel-header">
            <div class="header-title">
              <el-icon class="icon"><Delete /></el-icon>
              <span class="title">清除所有缓存</span>
            </div>
          </div>
          <div class="panel-body">
            <div class="action-content">
              <div class="description">
                清除Redis中所有缓存数据，包括景区列表、分析结果、评论等。
              </div>
              <el-button type="danger" @click="clearAllCache" :loading="loading.all" size="large" class="action-btn">
                <el-icon><Delete /></el-icon> 清除全部缓存
              </el-button>
            </div>
          </div>
          <i class="corner t-l"></i><i class="corner t-r"></i>
          <i class="corner b-l"></i><i class="corner b-r"></i>
        </div>
      </el-col>

      <el-col :xs="24" :md="8">
        <div class="tech-panel action-panel">
          <div class="panel-header">
            <div class="header-title">
              <el-icon class="icon"><Location /></el-icon>
              <span class="title">清除景区缓存</span>
            </div>
          </div>
          <div class="panel-body">
            <div class="action-content">
              <div class="description">
                清除景区管理相关的缓存数据，包括景区列表和详情信息。
              </div>
              <el-button type="warning" @click="clearScenicCache" :loading="loading.scenic" size="large" class="action-btn">
                <el-icon><Location /></el-icon> 清除景区缓存
              </el-button>
            </div>
          </div>
          <i class="corner t-l"></i><i class="corner t-r"></i>
          <i class="corner b-l"></i><i class="corner b-r"></i>
        </div>
      </el-col>

      <el-col :xs="24" :md="8">
        <div class="tech-panel action-panel">
          <div class="panel-header">
            <div class="header-title">
              <el-icon class="icon"><DataAnalysis /></el-icon>
              <span class="title">清除分析缓存</span>
            </div>
          </div>
          <div class="panel-body">
            <div class="action-content">
              <div class="description">
                清除数据分析相关的缓存，包括季节分析、客源地分布等。
              </div>
              <el-button type="primary" @click="clearAnalysisCache" :loading="loading.analysis" size="large" class="action-btn">
                <el-icon><DataAnalysis /></el-icon> 清除分析缓存
              </el-button>
            </div>
          </div>
          <i class="corner t-l"></i><i class="corner t-r"></i>
          <i class="corner b-l"></i><i class="corner b-r"></i>
        </div>
      </el-col>
    </el-row>

    <div class="tech-panel info-panel">
      <div class="panel-header">
        <div class="header-title">
          <el-icon class="icon"><Warning /></el-icon>
          <span class="title">操作说明</span>
        </div>
      </div>
      <div class="panel-body">
        <div class="info-content">
          <el-alert title="缓存管理注意事项" type="info" :closable="false">
            <template #default>
              <ul class="notice-list">
                <li>清除缓存后，下次请求将从Hive数据库重新查询，可能会稍慢</li>
                <li>建议在数据更新后手动清除相关缓存，以确保前端显示最新数据</li>
                <li>"清除所有缓存"会影响所有模块，请谨慎操作</li>
                <li>清除操作不可逆，请确认后再执行</li>
              </ul>
            </template>
          </el-alert>
        </div>
      </div>
      <i class="corner t-l"></i><i class="corner t-r"></i>
      <i class="corner b-l"></i><i class="corner b-r"></i>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Coin, Delete, Location, DataAnalysis, Warning } from '@element-plus/icons-vue'
import axios from 'axios'

const loading = reactive({
  all: false,
  scenic: false,
  analysis: false
})

const clearAllCache = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清除所有缓存吗？此操作将影响所有模块的缓存数据。',
      '警告',
      {
        confirmButtonText: '确定清除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    loading.all = true
    const token = localStorage.getItem('token')
    const res = await axios.delete('/api/cache/clear-all', {
      headers: { Authorization: `Bearer ${token}` }
    })

    if (res.data.code === 200) {
      ElMessage.success('所有缓存已成功清除')
    } else {
      ElMessage.error(res.data.msg || '清除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清除缓存失败:', error)
      ElMessage.error('清除缓存失败')
    }
  } finally {
    loading.all = false
  }
}

const clearScenicCache = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清除景区数据缓存吗？',
      '确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    loading.scenic = true
    const token = localStorage.getItem('token')
    const res = await axios.delete('/api/cache/clear-scenic', {
      headers: { Authorization: `Bearer ${token}` }
    })

    if (res.data.code === 200) {
      ElMessage.success('景区数据缓存已清除')
    } else {
      ElMessage.error(res.data.msg || '清除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清除景区缓存失败:', error)
      ElMessage.error('清除景区缓存失败')
    }
  } finally {
    loading.scenic = false
  }
}

const clearAnalysisCache = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清除分析数据缓存吗？',
      '确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    loading.analysis = true
    const token = localStorage.getItem('token')
    const res = await axios.delete('/api/cache/clear-analysis', {
      headers: { Authorization: `Bearer ${token}` }
    })

    if (res.data.code === 200) {
      ElMessage.success('分析数据缓存已清除')
    } else {
      ElMessage.error(res.data.msg || '清除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清除分析缓存失败:', error)
      ElMessage.error('清除分析缓存失败')
    }
  } finally {
    loading.analysis = false
  }
}
</script>

<style scoped lang="scss">
$primary: #00f2fe;
$bg-panel: rgba(13, 27, 62, 0.65);
$border-color: rgba(0, 242, 254, 0.25);
$text-main: #fff;
$text-sub: #8fb6e6;

.cache-container {
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

.action-panel {
  min-height: 220px;

  .action-content {
    display: flex;
    flex-direction: column;
    gap: 20px;

    .description {
      font-size: 14px;
      color: $text-sub;
      line-height: 1.6;
    }

    .action-btn {
      width: 100%;
      height: 50px;
      font-size: 16px;
      font-weight: bold;
    }
  }
}

.info-panel {
  .info-content {
    :deep(.el-alert) {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(0, 242, 254, 0.2);

      .el-alert__title {
        color: #fff;
        font-weight: bold;
      }

      .el-alert__description {
        color: $text-sub;
      }
    }

    .notice-list {
      margin: 10px 0 0 20px;
      padding: 0;
      color: $text-sub;

      li {
        margin-bottom: 8px;
        line-height: 1.6;
      }
    }
  }
}
</style>
