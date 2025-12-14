<template>
  <div class="visitor-container">
    <!-- 顶部行：省份分布 & 城市排名 -->
    <el-row :gutter="24" class="top-row">
      <el-col :xs="24" :lg="12">
        <div class="tech-panel chart-panel">
          <div class="panel-header">
            <el-icon class="icon"><Place /></el-icon>
            <span class="title">游客来源省份热力分布</span>
            <div class="header-line"></div>
          </div>
          <div ref="provinceChartRef" class="chart-box"></div>
          <!-- 装饰角标 -->
          <i class="corner t-l"></i><i class="corner t-r"></i>
          <i class="corner b-l"></i><i class="corner b-r"></i>
        </div>
      </el-col>

      <el-col :xs="24" :lg="12">
        <div class="tech-panel chart-panel">
          <div class="panel-header">
            <el-icon class="icon"><Location /></el-icon>
            <span class="title">核心客源城市 TOP10</span>
            <div class="header-line"></div>
          </div>
          <div ref="cityChartRef" class="chart-box"></div>
          <!-- 装饰角标 -->
          <i class="corner t-l"></i><i class="corner t-r"></i>
          <i class="corner b-l"></i><i class="corner b-r"></i>
        </div>
      </el-col>
    </el-row>

<!--    &lt;!&ndash; 底部行：人口画像 & 核心指标 &ndash;&gt;
    <el-row :gutter="24" class="bottom-row">
      <el-col :xs="24" :lg="16">
        <div class="tech-panel chart-panel">
          <div class="panel-header">
            <el-icon class="icon"><User /></el-icon>
            <span class="title">游客人口学特征 (年龄/性别)</span>
            <div class="header-line"></div>
          </div>
          <div ref="demographicChartRef" class="chart-box"></div>
          &lt;!&ndash; 装饰角标 &ndash;&gt;
          <i class="corner t-l"></i><i class="corner t-r"></i>
          <i class="corner b-l"></i><i class="corner b-r"></i>
        </div>
      </el-col>

      <el-col :xs="24" :lg="8">
        <div class="tech-panel stats-panel">
          <div class="panel-header">
            <el-icon class="icon"><DataAnalysis /></el-icon>
            <span class="title">全域客流洞察</span>
            <div class="header-line"></div>
          </div>

          <div class="stats-grid">
            <div class="stat-card primary-glow">
              <div class="label">累计接待游客</div>
              <div class="value-group">
                <span class="value num-font">{{ totalVisitors.toLocaleString() }}</span>
                <span class="unit">人次</span>
              </div>
              <div class="progress-bar"></div>
            </div>

            <div class="sub-stats-row">
              <div class="stat-mini-card">
                <div class="label">覆盖省份</div>
                <div class="value num-font">{{ provinceCount }}</div>
              </div>
              <div class="stat-mini-card">
                <div class="label">覆盖城市</div>
                <div class="value num-font">{{ cityCount }}</div>
              </div>
            </div>

            <div class="stat-card secondary-glow">
              <div class="label">数据说明</div>
              <div class="info-text">
                当前分析基于评论IP属地数据，不包含年龄性别等人口学特征
              </div>
            </div>
          </div>

          &lt;!&ndash; 装饰角标 &ndash;&gt;
          <i class="corner t-l"></i><i class="corner t-r"></i>
          <i class="corner b-l"></i><i class="corner b-r"></i>
        </div>
      </el-col>
    </el-row>-->
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { getVisitorSourceAPI, getVisitorDemographicsAPI } from '@/api/analysis'
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
    const res = await getVisitorDemographicsAPI()
    if (res.data) {
      initDemographicChart(res.data)
      avgAge.value = res.data.averageAge || 0
    }
  } catch (error) {
    console.error('获取游客年龄性别数据失败:', error)
  }
}

// ECharts 通用深色配置
const commonChartConfig = {
  backgroundColor: 'transparent',
  textStyle: { fontFamily: 'sans-serif' },
  tooltip: {
    backgroundColor: 'rgba(5, 10, 31, 0.95)',
    borderColor: '#00f2fe',
    textStyle: { color: '#fff' }
  }
}

const initProvinceChart = (data) => {
  if (!provinceChartRef.value) return

  if (provinceChart) provinceChart.dispose()
  provinceChart = echarts.init(provinceChartRef.value)

  const option = {
    ...commonChartConfig,
    tooltip: { ...commonChartConfig.tooltip, trigger: 'item', formatter: '{b}: {c}人 ({d}%)' },
    legend: {
      type: 'scroll',
      orient: 'vertical',
      right: 10,
      top: 20,
      bottom: 20,
      textStyle: { color: '#8fb6e6' },
      pageTextStyle: { color: '#fff' }
    },
    series: [{
      name: '省份分布',
      type: 'pie',
      radius: ['45%', '70%'],
      center: ['40%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 5,
        borderColor: '#0b1531',
        borderWidth: 2
      },
      label: { show: false },
      labelLine: { show: false },
      emphasis: {
        label: { show: true, fontSize: 18, fontWeight: 'bold', color: '#fff' },
        itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,242,254,0.5)' }
      },
      data: data.map((item, index) => ({
        value: item.visitor_count || item.count,
        name: item.province || item.source_province,
        itemStyle: {
          color: [
            '#00f2fe', '#4facfe', '#00c6ff', '#0072ff',
            '#f093fb', '#f5576c', '#43e97b', '#38f9d7'
          ][index % 8]
        }
      }))
    }]
  }
  provinceChart.setOption(option)
}

const initCityChart = (data) => {
  if (!cityChartRef.value) return

  if (cityChart) cityChart.dispose()
  cityChart = echarts.init(cityChartRef.value)

  const option = {
    ...commonChartConfig,
    tooltip: { ...commonChartConfig.tooltip, trigger: 'axis' },
    grid: { left: '3%', right: '8%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)', type: 'dashed' } },
      axisLabel: { color: '#8fb6e6' }
    },
    yAxis: {
      type: 'category',
      data: data.map(item => item.city || item.source_city).reverse(),
      axisLabel: { color: '#fff', fontSize: 13 },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      axisTick: { show: false }
    },
    series: [{
      type: 'bar',
      data: data.map(item => item.visitor_count || item.count).reverse(),
      barWidth: '50%',
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#f093fb' },
          { offset: 1, color: '#f5576c' }
        ]),
        borderRadius: [0, 20, 20, 0]
      },
      label: { show: true, position: 'right', color: '#f5576c', fontWeight: 'bold' }
    }]
  }
  cityChart.setOption(option)
}

const initDemographicChart = (data) => {
  if (!demographicChartRef.value) return

  if (demographicChart) demographicChart.dispose()
  demographicChart = echarts.init(demographicChartRef.value)

  const ageGroups = data.ageDistribution || [
    { ageGroup: '18-25', male: 120, female: 150 },
    { ageGroup: '26-35', male: 200, female: 180 },
    { ageGroup: '36-45', male: 150, female: 160 },
    { ageGroup: '46-55', male: 100, female: 120 },
    { ageGroup: '56+', male: 80, female: 90 }
  ]

  const option = {
    ...commonChartConfig,
    tooltip: { ...commonChartConfig.tooltip, trigger: 'axis' },
    legend: { top: 10, textStyle: { color: '#fff' }, icon: 'roundRect' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: ageGroups.map(item => item.ageGroup || item.age_group),
      axisLabel: { color: '#8fb6e6' },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)', type: 'dashed' } },
      axisLabel: { color: '#8fb6e6' }
    },
    series: [
      {
        name: '男性',
        type: 'bar',
        stack: 'total',
        barWidth: '40%',
        data: ageGroups.map(item => item.male || item.male_count),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#00c6ff' },
            { offset: 1, color: '#0072ff' }
          ])
        }
      },
      {
        name: '女性',
        type: 'bar',
        stack: 'total',
        barWidth: '40%',
        data: ageGroups.map(item => item.female || item.female_count),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#f72585' },
            { offset: 1, color: '#b5179e' }
          ]),
          borderRadius: [4, 4, 0, 0]
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
/* --- 变量定义 --- */
$primary: #00f2fe;
$secondary: #4facfe;
$bg-panel: rgba(13, 27, 62, 0.65);
$border-color: rgba(0, 242, 254, 0.25);
$text-main: #fff;
$text-sub: #8fb6e6;

.visitor-container {
  min-height: 100vh;
  padding: 20px;
  /* 深蓝科技背景 */
  background:
      radial-gradient(circle at 10% 20%, rgba(0, 242, 254, 0.08) 0%, transparent 40%),
      radial-gradient(circle at 90% 80%, rgba(247, 37, 133, 0.08) 0%, transparent 40%),
      linear-gradient(180deg, #050a1f 0%, #02040d 100%);
  color: $text-main;
  font-family: 'Inter', sans-serif;
}

/* --- 通用面板 --- */
.tech-panel {
  background: $bg-panel;
  border: 1px solid $border-color;
  position: relative;
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(10px);

  /* 装饰角标 */
  .corner {
    position: absolute;
    width: 8px;
    height: 8px;
    border: 2px solid $primary;
    transition: all 0.3s;
    opacity: 0.6;
    &.t-l { top: -1px; left: -1px; border-width: 2px 0 0 2px; }
    &.t-r { top: -1px; right: -1px; border-width: 2px 2px 0 0; }
    &.b-l { bottom: -1px; left: -1px; border-width: 0 0 2px 2px; }
    &.b-r { bottom: -1px; right: -1px; border-width: 0 2px 2px 0; }
  }

  &:hover .corner { width: 12px; height: 12px; opacity: 1; box-shadow: 0 0 8px $primary; }

  .panel-header {
    height: 50px;
    padding: 0 20px;
    display: flex;
    align-items: center;
    background: rgba(255, 255, 255, 0.02);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);

    .icon { color: $primary; font-size: 18px; margin-right: 10px; }
    .title { color: #fff; font-size: 16px; font-weight: 600; letter-spacing: 0.5px; }
    .header-line {
      flex: 1;
      height: 1px;
      background: linear-gradient(90deg, rgba(255,255,255,0.1), transparent);
      margin-left: 20px;
    }
  }
}

.chart-panel {
  height: 420px;
  .chart-box {
    width: 100%;
    height: 100%;
    padding: 10px;
  }
}

/* --- 统计面板 (右下角) --- */
.stats-panel {
  height: 420px;

  .stats-grid {
    padding: 25px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 100%;

    .stat-card {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.08);
      padding: 20px;
      border-radius: 4px;
      position: relative;
      overflow: hidden;

      .label { font-size: 14px; color: $text-sub; margin-bottom: 10px; }

      .value-group {
        display: flex;
        align-items: baseline;
        gap: 6px;

        .num-font { font-family: 'DIN Alternate', sans-serif; font-size: 32px; font-weight: bold; color: #fff; }
        .unit { font-size: 12px; color: rgba(255,255,255,0.5); }
      }

      &.primary-glow {
        border-color: rgba(0, 242, 254, 0.3);
        background: linear-gradient(135deg, rgba(0, 242, 254, 0.05) 0%, transparent 100%);
        .num-font { color: $primary; text-shadow: 0 0 10px rgba(0, 242, 254, 0.4); }
        .progress-bar {
          margin-top: 15px;
          height: 4px;
          width: 100%;
          background: rgba(255,255,255,0.1);
          position: relative;
          &::after {
            content: '';
            position: absolute;
            left: 0; top: 0; height: 100%; width: 75%;
            background: linear-gradient(90deg, $secondary, $primary);
            box-shadow: 0 0 8px $primary;
          }
        }
      }

      &.secondary-glow {
        border-color: rgba(240, 147, 251, 0.3);
        background: linear-gradient(135deg, rgba(240, 147, 251, 0.05) 0%, transparent 100%);
        display: flex;
        justify-content: space-between;
        align-items: center;

        .num-font { color: #f093fb; text-shadow: 0 0 10px rgba(240, 147, 251, 0.4); }

        .age-icon {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          border: 2px solid #f093fb;
          display: flex;
          align-items: center;
          justify-content: center;

          .icon-circle {
            width: 20px;
            height: 20px;
            background: #f093fb;
            border-radius: 50%;
            box-shadow: 0 0 10px #f093fb;
          }
        }
      }
    }

    .sub-stats-row {
      display: flex;
      gap: 15px;

      .stat-mini-card {
        flex: 1;
        background: rgba(0, 0, 0, 0.2);
        padding: 15px;
        text-align: center;
        border: 1px dashed rgba(255,255,255,0.1);
        border-radius: 4px;
        transition: all 0.3s;

        &:hover {
          background: rgba(255,255,255,0.05);
          border-color: rgba(255,255,255,0.2);
        }

        .label { font-size: 12px; color: $text-sub; margin-bottom: 5px; }
        .num-font { font-family: 'DIN Alternate'; font-size: 24px; color: #fff; font-weight: bold; }
      }
    }
  }
}

/* 响应式 */
@media (max-width: 768px) {
  .chart-panel, .stats-panel { height: 350px; }
}
</style>