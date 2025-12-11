<template>
  <div class="scenic-ranking">
    <el-card class="filter-card">
      <el-form :inline="true" :model="queryParams">
        <el-form-item label="排序类型">
          <el-select v-model="queryParams.rankType" @change="fetchRanking">
            <el-option label="评分排行" value="rating" />
            <el-option label="游客量排行" value="visitor" />
            <el-option label="评论数排行" value="review" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="显示数量">
          <el-select v-model="queryParams.limit" @change="fetchRanking">
            <el-option label="前10名" :value="10" />
            <el-option label="前20名" :value="20" />
            <el-option label="前30名" :value="30" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-row :gutter="20" class="charts-row">
      <el-col :xs="24" :lg="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>{{ rankTypeMap[queryParams.rankType] }}</span>
              <el-icon><TrendCharts /></el-icon>
            </div>
          </template>
          <div ref="barChartRef" class="chart"></div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="8">
        <el-card class="ranking-list-card">
          <template #header>
            <div class="card-header">
              <span>排行榜</span>
              <el-icon><Trophy /></el-icon>
            </div>
          </template>
          
          <div class="ranking-list">
            <div
              v-for="(item, index) in rankingData"
              :key="index"
              class="ranking-item"
              @click="handleItemClick(item)"
            >
              <div class="rank-badge" :class="`rank-${index + 1}`">
                {{ index + 1 }}
              </div>
              <div class="item-info">
                <div class="item-name">{{ item.scenic_spot || item.spot_name }}</div>
                <div class="item-value">
                  <template v-if="queryParams.rankType === 'rating'">
                    <el-rate v-model="item.displayRating" disabled show-score />
                  </template>
                  <template v-else-if="queryParams.rankType === 'visitor'">
                    <el-text type="primary">{{ item.visitor_count || item.total_visitors }} 人次</el-text>
                  </template>
                  <template v-else>
                    <el-text type="success">{{ item.review_count || item.total_reviews }} 条评论</el-text>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { getScenicRankingAPI } from '@/api/analysis'
import { TrendCharts, Trophy } from '@element-plus/icons-vue'

const router = useRouter()

const queryParams = reactive({
  rankType: 'rating',
  limit: 10
})

const rankTypeMap = {
  rating: '景区评分排行榜',
  visitor: '景区游客量排行榜',
  review: '景区评论数排行榜'
}

const rankingData = ref([])
const barChartRef = ref(null)
let barChart = null

const fetchRanking = async () => {
  try {
    const res = await getScenicRankingAPI(queryParams)
    if (res.data) {
      rankingData.value = res.data.map(item => ({
        ...item,
        displayRating: parseFloat(item.avg_rating || item.rating || 0)
      }))
      initBarChart()
    }
  } catch (error) {
    console.error('获取排行数据失败:', error)
  }
}

const initBarChart = () => {
  if (!barChartRef.value) return
  
  if (!barChart) {
    barChart = echarts.init(barChartRef.value)
  }
  
  const names = rankingData.value.map(item => item.scenic_spot || item.spot_name).reverse()
  let values, valueName
  
  if (queryParams.rankType === 'rating') {
    values = rankingData.value.map(item => parseFloat(item.avg_rating || item.rating || 0)).reverse()
    valueName = '评分'
  } else if (queryParams.rankType === 'visitor') {
    values = rankingData.value.map(item => parseInt(item.visitor_count || item.total_visitors || 0)).reverse()
    valueName = '游客量'
  } else {
    values = rankingData.value.map(item => parseInt(item.review_count || item.total_reviews || 0)).reverse()
    valueName = '评论数'
  }
  
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
      name: valueName
    },
    yAxis: {
      type: 'category',
      data: names,
      axisLabel: {
        formatter: (value) => value.length > 8 ? value.substring(0, 8) + '...' : value
      }
    },
    series: [{
      name: valueName,
      type: 'bar',
      data: values,
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#667eea' },
          { offset: 1, color: '#764ba2' }
        ]),
        borderRadius: [0, 4, 4, 0]
      },
      label: {
        show: true,
        position: 'right',
        formatter: queryParams.rankType === 'rating' ? '{c}' : '{c}'
      },
      barWidth: '60%'
    }]
  }
  
  barChart.setOption(option)
}

const handleItemClick = (item) => {
  router.push({
    path: '/scenic-detail',
    query: { spot: item.scenic_spot || item.spot_name }
  })
}

const handleResize = () => {
  barChart?.resize()
}

onMounted(() => {
  fetchRanking()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  barChart?.dispose()
})
</script>

<style scoped lang="scss">
.scenic-ranking {
  .filter-card {
    margin-bottom: 20px;
  }
  
  .charts-row {
    .chart-card {
      .card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-weight: 600;
      }
      
      .chart {
        height: 600px;
      }
    }
    
    .ranking-list-card {
      .card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-weight: 600;
      }
      
      .ranking-list {
        max-height: 600px;
        overflow-y: auto;
        
        .ranking-item {
          display: flex;
          align-items: center;
          padding: 16px;
          border-bottom: 1px solid #f0f0f0;
          cursor: pointer;
          transition: all 0.3s;
          
          &:last-child {
            border-bottom: none;
          }
          
          &:hover {
            background: #f5f7fa;
            transform: translateX(4px);
          }
          
          .rank-badge {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 16px;
            margin-right: 12px;
            flex-shrink: 0;
            
            &.rank-1 {
              background: linear-gradient(135deg, #ffd700, #ffed4e);
              color: #fff;
              box-shadow: 0 2px 8px rgba(255, 215, 0, 0.4);
            }
            
            &.rank-2 {
              background: linear-gradient(135deg, #c0c0c0, #e8e8e8);
              color: #fff;
              box-shadow: 0 2px 8px rgba(192, 192, 192, 0.4);
            }
            
            &.rank-3 {
              background: linear-gradient(135deg, #cd7f32, #f0a663);
              color: #fff;
              box-shadow: 0 2px 8px rgba(205, 127, 50, 0.4);
            }
            
            &:not(.rank-1):not(.rank-2):not(.rank-3) {
              background: #f0f0f0;
              color: #606266;
            }
          }
          
          .item-info {
            flex: 1;
            min-width: 0;
            
            .item-name {
              font-weight: 500;
              font-size: 15px;
              margin-bottom: 6px;
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
            }
            
            .item-value {
              font-size: 14px;
            }
          }
        }
      }
    }
  }
}
</style>
