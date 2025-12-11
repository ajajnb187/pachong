<template>
  <div class="seasonal-analysis">
    <el-card class="filter-card">
      <el-form :inline="true" :model="queryParams">
        <el-form-item label="景区">
          <el-select v-model="queryParams.spotId" @change="fetchData" placeholder="选择景区">
            <el-option
              v-for="spot in scenicList"
              :key="spot.id"
              :label="spot.name"
              :value="spot.name"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="年份">
          <el-date-picker
            v-model="queryParams.year"
            type="year"
            placeholder="选择年份"
            @change="fetchData"
            value-format="YYYY"
          />
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-row :gutter="20">
      <el-col :xs="24" :lg="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>月度游客量趋势</span>
              <el-icon><TrendCharts /></el-icon>
            </div>
          </template>
          <div ref="monthlyChartRef" class="chart"></div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="8">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>季节分布</span>
              <el-icon><Histogram /></el-icon>
            </div>
          </template>
          <div ref="seasonChartRef" class="chart"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="second-row">
      <el-col :xs="24">
        <el-card class="recommend-card">
          <template #header>
            <div class="card-header">
              <span>建议游玩时间</span>
              <el-icon><Calendar /></el-icon>
            </div>
          </template>
          
          <div v-if="recommendData" class="recommend-content">
            <div class="best-time">
              <div class="label">最佳游玩时间</div>
              <div class="value">{{ recommendData.bestVisitTime }}</div>
            </div>
            
            <el-divider />
            
            <div class="month-list">
              <div class="section-title">推荐月份</div>
              <div class="month-grid">
                <div
                  v-for="month in recommendData.recommendedMonths"
                  :key="month.month"
                  class="month-card"
                >
                  <div class="month-name">{{ month.monthName }}</div>
                  <div class="month-info">
                    <el-tag :type="getCrowdLevelType(month.crowdLevel)">
                      {{ month.crowdLevel }}
                    </el-tag>
                    <div class="rating">
                      <el-icon><Star /></el-icon>
                      {{ month.avgRating }}
                    </div>
                  </div>
                  <div class="visitor-count">游客: {{ month.visitorCount }}人</div>
                </div>
              </div>
            </div>
            
            <el-divider />
            
            <el-row :gutter="20">
              <el-col :xs="24" :sm="12">
                <div class="section-title">高峰期月份</div>
                <div class="month-tags">
                  <el-tag
                    v-for="month in recommendData.peakMonths"
                    :key="month"
                    type="danger"
                    class="month-tag"
                  >
                    {{ month }}
                  </el-tag>
                </div>
              </el-col>
              
              <el-col :xs="24" :sm="12">
                <div class="section-title">淡季月份</div>
                <div class="month-tags">
                  <el-tag
                    v-for="month in recommendData.offPeakMonths"
                    :key="month"
                    type="success"
                    class="month-tag"
                  >
                    {{ month }}
                  </el-tag>
                </div>
              </el-col>
            </el-row>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { getSeasonPatternAPI, getRecommendVisitTimeAPI } from '@/api/analysis'
import { getScenicListAPI } from '@/api/analysis'
import { TrendCharts, Histogram, Calendar, Star } from '@element-plus/icons-vue'

const queryParams = reactive({
  spotId: '',
  year: new Date().getFullYear().toString()
})

const scenicList = ref([])
const seasonData = ref([])
const recommendData = ref(null)
const monthlyChartRef = ref(null)
const seasonChartRef = ref(null)

let monthlyChart = null
let seasonChart = null

const fetchScenicList = async () => {
  try {
    const res = await getScenicListAPI()
    if (res.data && res.data.length > 0) {
      scenicList.value = res.data.map(item => ({
        id: item.scenic_spot || item.spot_name,
        name: item.scenic_spot || item.spot_name
      }))
      if (!queryParams.spotId && scenicList.value.length > 0) {
        queryParams.spotId = scenicList.value[0].id
      }
    }
  } catch (error) {
    console.error('获取景区列表失败:', error)
  }
}

const fetchData = async () => {
  if (!queryParams.spotId) return
  
  try {
    const [seasonRes, recommendRes] = await Promise.all([
      getSeasonPatternAPI({ 
        spotId: queryParams.spotId,
        year: parseInt(queryParams.year)
      }),
      getRecommendVisitTimeAPI({ spotId: queryParams.spotId })
    ])
    
    if (seasonRes.data) {
      seasonData.value = seasonRes.data.monthlyStats || []
      initMonthlyChart()
      initSeasonChart()
    }
    
    if (recommendRes.data) {
      recommendData.value = recommendRes.data
    }
  } catch (error) {
    console.error('获取季节性数据失败:', error)
  }
}

const initMonthlyChart = () => {
  if (!monthlyChartRef.value) return
  
  if (!monthlyChart) {
    monthlyChart = echarts.init(monthlyChartRef.value)
  }
  
  const months = seasonData.value.map(item => `${item.month}月`)
  const visitors = seasonData.value.map(item => item.visitorCount || item.visitor_count)
  
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
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(102, 126, 234, 0.5)' },
          { offset: 1, color: 'rgba(118, 75, 162, 0.1)' }
        ])
      },
      itemStyle: {
        color: '#667eea'
      },
      lineStyle: {
        width: 3
      }
    }],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    }
  }
  
  monthlyChart.setOption(option)
}

const initSeasonChart = () => {
  if (!seasonChartRef.value) return
  
  if (!seasonChart) {
    seasonChart = echarts.init(seasonChartRef.value)
  }
  
  const seasonMap = { '春季': 0, '夏季': 0, '秋季': 0, '冬季': 0 }
  seasonData.value.forEach(item => {
    const season = item.seasonType || item.season_type
    if (seasonMap.hasOwnProperty(season)) {
      seasonMap[season] += item.visitorCount || item.visitor_count || 0
    }
  })
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}人 ({d}%)'
    },
    series: [{
      name: '季节分布',
      type: 'pie',
      radius: '70%',
      data: [
        { value: seasonMap['春季'], name: '春季', itemStyle: { color: '#43e97b' } },
        { value: seasonMap['夏季'], name: '夏季', itemStyle: { color: '#f5576c' } },
        { value: seasonMap['秋季'], name: '秋季', itemStyle: { color: '#f093fb' } },
        { value: seasonMap['冬季'], name: '冬季', itemStyle: { color: '#4facfe' } }
      ],
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      label: {
        formatter: '{b}\n{c}人'
      }
    }]
  }
  
  seasonChart.setOption(option)
}

const getCrowdLevelType = (level) => {
  const typeMap = {
    '舒适': 'success',
    '适中': 'warning',
    '拥挤': 'danger'
  }
  return typeMap[level] || 'info'
}

const handleResize = () => {
  monthlyChart?.resize()
  seasonChart?.resize()
}

onMounted(async () => {
  await fetchScenicList()
  await fetchData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  monthlyChart?.dispose()
  seasonChart?.dispose()
})
</script>

<style scoped lang="scss">
.seasonal-analysis {
  .filter-card {
    margin-bottom: 20px;
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
      height: 400px;
    }
  }
  
  .recommend-card {
    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-weight: 600;
    }
    
    .recommend-content {
      .best-time {
        text-align: center;
        padding: 20px;
        
        .label {
          font-size: 16px;
          color: #909399;
          margin-bottom: 12px;
        }
        
        .value {
          font-size: 32px;
          font-weight: 600;
          color: #409EFF;
        }
      }
      
      .section-title {
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 16px;
        color: #303133;
      }
      
      .month-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 16px;
        margin-bottom: 20px;
        
        .month-card {
          padding: 16px;
          border: 1px solid #EBEEF5;
          border-radius: 8px;
          transition: all 0.3s;
          
          &:hover {
            border-color: #409EFF;
            box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
          }
          
          .month-name {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 12px;
            color: #303133;
          }
          
          .month-info {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
            
            .rating {
              display: flex;
              align-items: center;
              gap: 4px;
              color: #F7BA2A;
              font-weight: 500;
            }
          }
          
          .visitor-count {
            font-size: 14px;
            color: #909399;
          }
        }
      }
      
      .month-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        
        .month-tag {
          font-size: 14px;
        }
      }
    }
  }
}
</style>
