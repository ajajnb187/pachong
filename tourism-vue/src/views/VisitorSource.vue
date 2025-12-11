<template>
  <div class="visitor-source">
    <el-row :gutter="20">
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>游客来源省份分布</span>
              <el-icon><Place /></el-icon>
            </div>
          </template>
          <div ref="provinceChartRef" class="chart"></div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>游客来源城市TOP10</span>
              <el-icon><Location /></el-icon>
            </div>
          </template>
          <div ref="cityChartRef" class="chart"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="second-row">
      <el-col :xs="24" :lg="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>游客年龄与性别分布</span>
              <el-icon><User /></el-icon>
            </div>
          </template>
          <div ref="demographicChartRef" class="chart"></div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="8">
        <el-card class="stats-card">
          <template #header>
            <div class="card-header">
              <span>游客统计</span>
              <el-icon><DataAnalysis /></el-icon>
            </div>
          </template>
          
          <div class="stats-list">
            <div class="stat-item">
              <div class="stat-label">总游客数</div>
              <div class="stat-value">{{ totalVisitors }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">省份数量</div>
              <div class="stat-value">{{ provinceCount }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">城市数量</div>
              <div class="stat-value">{{ cityCount }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">平均年龄</div>
              <div class="stat-value">{{ avgAge }} 岁</div>
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
import { getVisitorSourceAPI, getVisitorDemographicAPI } from '@/api/analysis'
import { Place, Location, User, DataAnalysis } from '@element-plus/icons-vue'

const provinceChartRef = ref(null)
const cityChartRef = ref(null)
const demographicChartRef = ref(null)

const totalVisitors = ref(0)
const provinceCount = ref(0)
const cityCount = ref(0)
const avgAge = ref(0)

let provinceChart = null
let cityChart = null
let demographicChart = null

const fetchVisitorSource = async () => {
  try {
    const res = await getVisitorSourceAPI()
    if (res.data) {
      const { provinceDistribution, cityDistribution } = res.data
      
      if (provinceDistribution && provinceDistribution.length > 0) {
        provinceCount.value = provinceDistribution.length
        initProvinceChart(provinceDistribution)
      }
      
      if (cityDistribution && cityDistribution.length > 0) {
        cityCount.value = cityDistribution.length
        initCityChart(cityDistribution.slice(0, 10))
      }
      
      totalVisitors.value = res.data.totalVisitors || 0
    }
  } catch (error) {
    console.error('获取客源地数据失败:', error)
  }
}

const fetchDemographic = async () => {
  try {
    const res = await getVisitorDemographicAPI()
    if (res.data) {
      initDemographicChart(res.data)
      avgAge.value = res.data.averageAge || 0
    }
  } catch (error) {
    console.error('获取游客年龄性别数据失败:', error)
  }
}

const initProvinceChart = (data) => {
  if (!provinceChartRef.value) return
  
  provinceChart = echarts.init(provinceChartRef.value)
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}人 ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      type: 'scroll',
      pageIconSize: 12,
      pageTextStyle: {
        fontSize: 10
      }
    },
    series: [{
      name: '省份分布',
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: false,
        position: 'center'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 18,
          fontWeight: 'bold'
        }
      },
      labelLine: {
        show: false
      },
      data: data.map((item, index) => ({
        value: item.visitor_count || item.count,
        name: item.province || item.source_province,
        itemStyle: {
          color: [
            '#667eea', '#764ba2', '#f093fb', '#f5576c',
            '#4facfe', '#00f2fe', '#43e97b', '#38f9d7',
            '#fa709a', '#fee140', '#30cfd0', '#330867'
          ][index % 12]
        }
      }))
    }]
  }
  provinceChart.setOption(option)
}

const initCityChart = (data) => {
  if (!cityChartRef.value) return
  
  cityChart = echarts.init(cityChartRef.value)
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
      data: data.map(item => item.city || item.source_city).reverse()
    },
    series: [{
      type: 'bar',
      data: data.map(item => item.visitor_count || item.count).reverse(),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#f093fb' },
          { offset: 1, color: '#f5576c' }
        ]),
        borderRadius: [0, 4, 4, 0]
      },
      label: {
        show: true,
        position: 'right'
      },
      barWidth: '60%'
    }]
  }
  cityChart.setOption(option)
}

const initDemographicChart = (data) => {
  if (!demographicChartRef.value) return
  
  demographicChart = echarts.init(demographicChartRef.value)
  
  const ageGroups = data.ageDistribution || [
    { ageGroup: '18-25', male: 120, female: 150 },
    { ageGroup: '26-35', male: 200, female: 180 },
    { ageGroup: '36-45', male: 150, female: 160 },
    { ageGroup: '46-55', male: 100, female: 120 },
    { ageGroup: '56+', male: 80, female: 90 }
  ]
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['男性', '女性']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ageGroups.map(item => item.ageGroup || item.age_group)
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '男性',
        type: 'bar',
        stack: 'total',
        data: ageGroups.map(item => item.male || item.male_count),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#667eea' },
            { offset: 1, color: '#764ba2' }
          ])
        }
      },
      {
        name: '女性',
        type: 'bar',
        stack: 'total',
        data: ageGroups.map(item => item.female || item.female_count),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#f093fb' },
            { offset: 1, color: '#f5576c' }
          ])
        }
      }
    ]
  }
  demographicChart.setOption(option)
}

const handleResize = () => {
  provinceChart?.resize()
  cityChart?.resize()
  demographicChart?.resize()
}

onMounted(async () => {
  await fetchVisitorSource()
  await fetchDemographic()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  provinceChart?.dispose()
  cityChart?.dispose()
  demographicChart?.dispose()
})
</script>

<style scoped lang="scss">
.visitor-source {
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
  
  .stats-card {
    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-weight: 600;
    }
    
    .stats-list {
      .stat-item {
        padding: 20px;
        border-bottom: 1px solid #f0f0f0;
        transition: background 0.3s;
        
        &:last-child {
          border-bottom: none;
        }
        
        &:hover {
          background: #f5f7fa;
        }
        
        .stat-label {
          font-size: 14px;
          color: #909399;
          margin-bottom: 8px;
        }
        
        .stat-value {
          font-size: 24px;
          font-weight: 600;
          color: #303133;
        }
      }
    }
  }
}
</style>
