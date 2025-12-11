<template>
  <div class="dashboard">
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :lg="6" v-for="stat in stats" :key="stat.title">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon" :style="{ background: stat.color }">
              <el-icon :size="32"><component :is="stat.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-title">{{ stat.title }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="charts-row">
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>景区评分排行榜</span>
              <el-icon><TrophyBase /></el-icon>
            </div>
          </template>
          <div ref="ratingChartRef" class="chart"></div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>景区游客量排行</span>
              <el-icon><User /></el-icon>
            </div>
          </template>
          <div ref="visitorChartRef" class="chart"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="charts-row">
      <el-col :xs="24" :lg="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>评分分布</span>
              <el-icon><DataLine /></el-icon>
            </div>
          </template>
          <div ref="ratingDistChartRef" class="chart"></div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="8">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>热门景区</span>
              <el-icon><Star /></el-icon>
            </div>
          </template>
          <div class="top-spots">
            <div
              v-for="(spot, index) in topSpots"
              :key="index"
              class="spot-item"
            >
              <div class="spot-rank" :class="`rank-${index + 1}`">{{ index + 1 }}</div>
              <div class="spot-info">
                <div class="spot-name">{{ spot.name }}</div>
                <el-rate v-model="spot.rating" disabled show-score />
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { getOverviewAPI, getScenicRankingAPI } from '@/api/analysis'
import { Location, User, ChatDotRound, Star, TrophyBase, DataLine } from '@element-plus/icons-vue'

const stats = ref([
  { title: '景区总数', value: 0, icon: 'Location', color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
  { title: '评论总数', value: 0, icon: 'ChatDotRound', color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' },
  { title: '平均评分', value: 0, icon: 'Star', color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' },
  { title: '评论人数', value: 0, icon: 'User', color: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' }
])

const topSpots = ref([])
const ratingChartRef = ref(null)
const visitorChartRef = ref(null)
const ratingDistChartRef = ref(null)

let ratingChart = null
let visitorChart = null
let ratingDistChart = null

const fetchOverview = async () => {
  try {
    const res = await getOverviewAPI()
    const data = res.data
    stats.value[0].value = data.totalSpots || 0
    stats.value[1].value = data.totalReviews || 0
    stats.value[2].value = data.averageRating?.toFixed(1) || 0
    stats.value[3].value = data.totalReviewers || 0
  } catch (error) {
    console.error('获取概览数据失败:', error)
  }
}

const fetchRankingData = async () => {
  try {
    const [ratingRes, visitorRes] = await Promise.all([
      getScenicRankingAPI({ rankType: 'rating', limit: 10 }),
      getScenicRankingAPI({ rankType: 'visitor', limit: 10 })
    ])
    
    if (ratingRes.data && ratingRes.data.length > 0) {
      initRatingChart(ratingRes.data)
      topSpots.value = ratingRes.data.slice(0, 5).map(item => ({
        name: item.scenic_spot || item.spot_name,
        rating: parseFloat(item.avg_rating || item.rating || 0)
      }))
    }
    
    if (visitorRes.data && visitorRes.data.length > 0) {
      initVisitorChart(visitorRes.data)
    }
    
    initRatingDistChart()
  } catch (error) {
    console.error('获取排行数据失败:', error)
  }
}

const initRatingChart = (data) => {
  if (!ratingChartRef.value) return
  
  ratingChart = echarts.init(ratingChartRef.value)
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      max: 5
    },
    yAxis: {
      type: 'category',
      data: data.map(item => item.scenic_spot || item.spot_name).reverse(),
      axisLabel: {
        formatter: (value) => value.length > 6 ? value.substring(0, 6) + '...' : value
      }
    },
    series: [{
      type: 'bar',
      data: data.map(item => parseFloat(item.avg_rating || item.rating || 0)).reverse(),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#667eea' },
          { offset: 1, color: '#764ba2' }
        ])
      },
      label: {
        show: true,
        position: 'right',
        formatter: '{c}'
      }
    }]
  }
  ratingChart.setOption(option)
}

const initVisitorChart = (data) => {
  if (!visitorChartRef.value) return
  
  visitorChart = echarts.init(visitorChartRef.value)
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value'
    },
    yAxis: {
      type: 'category',
      data: data.map(item => item.scenic_spot || item.spot_name).reverse(),
      axisLabel: {
        formatter: (value) => value.length > 6 ? value.substring(0, 6) + '...' : value
      }
    },
    series: [{
      type: 'bar',
      data: data.map(item => parseInt(item.visitor_count || item.total_visitors || 0)).reverse(),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#f093fb' },
          { offset: 1, color: '#f5576c' }
        ])
      },
      label: {
        show: true,
        position: 'right'
      }
    }]
  }
  visitorChart.setOption(option)
}

const initRatingDistChart = () => {
  if (!ratingDistChartRef.value) return
  
  ratingDistChart = echarts.init(ratingDistChartRef.value)
  const option = {
    tooltip: {
      trigger: 'item'
    },
    legend: {
      top: '5%',
      left: 'center'
    },
    series: [{
      name: '评分分布',
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: true,
        formatter: '{b}: {c}条 ({d}%)'
      },
      data: [
        { value: 85, name: '5分', itemStyle: { color: '#43e97b' } },
        { value: 12, name: '4分', itemStyle: { color: '#4facfe' } },
        { value: 2, name: '3分', itemStyle: { color: '#f093fb' } },
        { value: 1, name: '2分', itemStyle: { color: '#f5576c' } },
        { value: 0, name: '1分', itemStyle: { color: '#909399' } }
      ]
    }]
  }
  ratingDistChart.setOption(option)
}

const handleResize = () => {
  ratingChart?.resize()
  visitorChart?.resize()
  ratingDistChart?.resize()
}

onMounted(async () => {
  await fetchOverview()
  await fetchRankingData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  ratingChart?.dispose()
  visitorChart?.dispose()
  ratingDistChart?.dispose()
})
</script>

<style scoped lang="scss">
.dashboard {
  .stats-row {
    margin-bottom: 20px;
  }
  
  .stat-card {
    cursor: pointer;
    transition: transform 0.3s;
    
    &:hover {
      transform: translateY(-5px);
    }
    
    .stat-content {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .stat-icon {
        width: 64px;
        height: 64px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
      }
      
      .stat-info {
        flex: 1;
        
        .stat-value {
          font-size: 28px;
          font-weight: 600;
          color: #303133;
          margin-bottom: 4px;
        }
        
        .stat-title {
          font-size: 14px;
          color: #909399;
        }
      }
    }
  }
  
  .charts-row {
    margin-bottom: 20px;
  }
  
  .chart-card {
    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-weight: 600;
    }
    
    .chart {
      height: 400px;
    }
    
    .top-spots {
      .spot-item {
        display: flex;
        align-items: center;
        padding: 16px;
        border-bottom: 1px solid #f0f0f0;
        transition: background 0.3s;
        
        &:last-child {
          border-bottom: none;
        }
        
        &:hover {
          background: #f5f7fa;
        }
        
        .spot-rank {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
          margin-right: 12px;
          
          &.rank-1 {
            background: linear-gradient(135deg, #ffd700, #ffed4e);
            color: #fff;
          }
          
          &.rank-2 {
            background: linear-gradient(135deg, #c0c0c0, #e8e8e8);
            color: #fff;
          }
          
          &.rank-3 {
            background: linear-gradient(135deg, #cd7f32, #f0a663);
            color: #fff;
          }
          
          &:not(.rank-1):not(.rank-2):not(.rank-3) {
            background: #f0f0f0;
            color: #606266;
          }
        }
        
        .spot-info {
          flex: 1;
          
          .spot-name {
            font-weight: 500;
            margin-bottom: 4px;
          }
        }
      }
    }
  }
}
</style>
