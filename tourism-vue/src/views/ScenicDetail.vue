<template>
  <div class="scenic-detail">
    <el-page-header @back="handleBack" class="page-header">
      <template #content>
        <span class="scenic-name">{{ scenicName }}</span>
      </template>
    </el-page-header>
    
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6" v-for="stat in stats" :key="stat.label">
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
    
    <el-row :gutter="20">
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>评分趋势</span>
              <el-icon><TrendCharts /></el-icon>
            </div>
          </template>
          <div ref="ratingTrendChartRef" class="chart"></div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>游客量趋势</span>
              <el-icon><DataLine /></el-icon>
            </div>
          </template>
          <div ref="visitorTrendChartRef" class="chart"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="second-row">
      <el-col :xs="24">
        <el-card class="review-card">
          <template #header>
            <div class="card-header">
              <span>评论详情</span>
              <el-icon><ChatDotRound /></el-icon>
            </div>
          </template>
          
          <el-table :data="reviews" stripe>
            <el-table-column prop="visitor_name" label="游客" width="120" />
            <el-table-column prop="rating" label="评分" width="120">
              <template #default="{ row }">
                <el-rate v-model="row.rating" disabled show-score />
              </template>
            </el-table-column>
            <el-table-column prop="travel_date" label="游玩日期" width="120" />
            <el-table-column prop="review_content" label="评论内容" show-overflow-tooltip />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { 
  getVisitorCountAPI,
  getReviewStatsAPI
} from '@/api/analysis'
import { Star, User, ChatDotRound, Calendar, TrendCharts, DataLine } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const scenicName = computed(() => route.query.spot || '')
const stats = ref([
  { label: '总游客量', value: 0, icon: 'User', color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
  { label: '总评论数', value: 0, icon: 'ChatDotRound', color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' },
  { label: '平均评分', value: 0, icon: 'Star', color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' },
  { label: '评论人数', value: 0, icon: 'Calendar', color: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' }
])

const reviews = ref([])
const ratingTrendChartRef = ref(null)
const visitorTrendChartRef = ref(null)

let ratingTrendChart = null
let visitorTrendChart = null

const fetchData = async () => {
  if (!scenicName.value) return
  
  try {
    const [visitorRes, reviewRes] = await Promise.all([
      getVisitorCountAPI({ spotId: scenicName.value }),
      getReviewStatsAPI({ spotId: scenicName.value })
    ])
    
    if (visitorRes.data) {
      stats.value[0].value = visitorRes.data.totalVisitors || 0
      initVisitorTrendChart(visitorRes.data.monthlyData || [])
    }
    
    if (reviewRes.data) {
      stats.value[1].value = reviewRes.data.totalReviews || 0
      stats.value[2].value = (reviewRes.data.avgRating || 0).toFixed(1)
      stats.value[3].value = reviewRes.data.uniqueReviewers || 0
      reviews.value = (reviewRes.data.recentReviews || []).slice(0, 10).map(item => ({
        ...item,
        rating: parseFloat(item.rating || 0)
      }))
      initRatingTrendChart(reviewRes.data.monthlyRating || [])
    }
  } catch (error) {
    console.error('获取景区详情失败:', error)
  }
}

const initRatingTrendChart = (data) => {
  if (!ratingTrendChartRef.value) return
  
  ratingTrendChart = echarts.init(ratingTrendChartRef.value)
  
  const months = data.map(item => `${item.month}月`)
  const ratings = data.map(item => item.avgRating || 0)
  
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: months,
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      name: '评分',
      min: 0,
      max: 5
    },
    series: [{
      name: '平均评分',
      type: 'line',
      data: ratings,
      smooth: true,
      itemStyle: {
        color: '#f093fb'
      },
      lineStyle: {
        width: 3
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(240, 147, 251, 0.5)' },
          { offset: 1, color: 'rgba(245, 87, 108, 0.1)' }
        ])
      }
    }],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    }
  }
  
  ratingTrendChart.setOption(option)
}

const initVisitorTrendChart = (data) => {
  if (!visitorTrendChartRef.value) return
  
  visitorTrendChart = echarts.init(visitorTrendChartRef.value)
  
  const months = data.map(item => `${item.month}月`)
  const visitors = data.map(item => item.count || 0)
  
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: months,
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      name: '游客量'
    },
    series: [{
      name: '游客量',
      type: 'line',
      data: visitors,
      smooth: true,
      itemStyle: {
        color: '#667eea'
      },
      lineStyle: {
        width: 3
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(102, 126, 234, 0.5)' },
          { offset: 1, color: 'rgba(118, 75, 162, 0.1)' }
        ])
      }
    }],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    }
  }
  
  visitorTrendChart.setOption(option)
}

const handleBack = () => {
  router.back()
}

const handleResize = () => {
  ratingTrendChart?.resize()
  visitorTrendChart?.resize()
}

onMounted(() => {
  fetchData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  ratingTrendChart?.dispose()
  visitorTrendChart?.dispose()
})
</script>

<style scoped lang="scss">
.scenic-detail {
  .page-header {
    margin-bottom: 20px;
    
    .scenic-name {
      font-size: 20px;
      font-weight: 600;
    }
  }
  
  .stats-row {
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
  
  .second-row {
    margin-top: 20px;
  }
  
  .chart-card {
    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-weight: 600;
    }
    
    .chart {
      height: 350px;
    }
  }
  
  .review-card {
    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-weight: 600;
    }
  }
}
</style>
