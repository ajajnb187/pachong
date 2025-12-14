<template>
  <div class="seasonal-container">
    <!-- 顶部控制台 -->
    <div class="control-console">
      <div class="console-decoration left"></div>

      <el-form :inline="true" :model="queryParams" class="tech-form">


<!--        <el-form-item label="时间维度 / Year">
          <el-date-picker
              v-model="queryParams.year"
              type="year"
              placeholder="选择年份"
              @change="handleFilterChange"
              value-format="YYYY"
              popper-class="tech-popper"
              class="tech-date"
              :clearable="false"
          />
        </el-form-item>-->
      </el-form>

      <div class="console-decoration right"></div>
    </div>

    <!-- 数据图表区 -->
    <el-row :gutter="24" class="chart-section">
      <!-- 左侧：历史人流量分析 -->
      <el-col :xs="24" :lg="16">
        <div class="tech-panel chart-panel">
          <div class="panel-header">
            <div class="header-title">
              <el-icon class="icon"><TrendCharts /></el-icon>
              <span class="title">历史人流量分析</span>
            </div>
            <div class="header-tag">{{ currentTargetName }}</div>
          </div>
          <div ref="monthlyChartRef" class="chart-box"></div>
          <!-- 装饰角标 -->
          <i class="corner t-l"></i><i class="corner t-r"></i>
          <i class="corner b-l"></i><i class="corner b-r"></i>
        </div>
      </el-col>

      <!-- 右侧：未来人流量预测 -->
      <el-col :xs="24" :lg="8">
        <div class="tech-panel chart-panel">
          <div class="panel-header">
            <div class="header-title">
              <el-icon class="icon"><Histogram /></el-icon>
              <span class="title">未来人流量预测</span>
            </div>
          </div>
          <div ref="forecastChartRef" class="chart-box"></div>
          <!-- 装饰角标 -->
          <i class="corner t-l"></i><i class="corner t-r"></i>
          <i class="corner b-l"></i><i class="corner b-r"></i>
        </div>
      </el-col>
    </el-row>

    <!-- 智能推荐引擎 -->
    <el-row :gutter="24" class="recommend-section">
      <el-col :xs="24">
        <div class="tech-panel full-panel" v-loading="loading" element-loading-background="rgba(0,0,0,0.5)">
          <div class="panel-header">
            <div class="header-title">
              <el-icon class="icon"><Calendar /></el-icon>
              <span class="title">最佳游玩建议</span>
            </div>
            <div class="header-line"></div>
          </div>

          <div class="recommend-body" v-if="recommendData">
            <div class="engine-layout">
              <!-- 核心展示区 -->
              <div class="core-reactor">
                <div class="reactor-ring outer"></div>
                <div class="reactor-ring inner"></div>
                <div class="reactor-content">
                  <div class="label">最佳出游时机</div>
                  <div class="value">{{ recommendData.bestVisitTime || '全 数据分析中...' }}</div>
                  <div class="desc">基于气候舒适度与客流密度综合计算</div>
                </div>
              </div>

              <!-- 右侧详情区 -->
              <div class="details-matrix">
                <!-- 推荐月份 -->
                <div class="matrix-row">
                  <div class="row-label">
                    <span class="dot green"></span> 推荐月份
                  </div>
                  <div class="month-card-grid">
                    <div v-for="month in recommendData.recommendedMonths" :key="month.month" class="mini-month-card">
                      <div class="m-head">
                        <span class="name">{{ month.monthName }}</span>
                        <span class="score"><el-icon><Star /></el-icon> {{ month.avgRating }}</span>
                      </div>
                      <div class="m-body">
                        <span class="tag" :class="getCrowdClass(month.crowdLevel)">{{ month.crowdLevel }}</span>
                        <span class="visitor">约 {{ formatNumber(month.visitorCount) }} 人</span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 预警与错峰 -->
                <div class="matrix-row split">
                  <div class="split-item">
                    <div class="row-label"><span class="dot red"></span> 高峰预警</div>
                    <div class="tags-container">
                      <span v-for="m in recommendData.peakMonths" :key="m" class="tech-tag peak">{{ m }}</span>
                      <span v-if="!recommendData.peakMonths?.length" class="empty-text">无明显高峰</span>
                    </div>
                  </div>
                  <div class="split-item">
                    <div class="row-label"><span class="dot blue"></span> 错峰推荐</div>
                    <div class="tags-container">
                      <span v-for="m in recommendData.offPeakMonths" :key="m" class="tech-tag offpeak">{{ m }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <!-- 装饰角标 -->
          <i class="corner t-l"></i><i class="corner t-r"></i>
          <i class="corner b-l"></i><i class="corner b-r"></i>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { getTrafficAnalysisAPI, getTrafficForecastAPI, getScenicListAPI, getRecommendVisitTimeAPI } from '@/api/analysis'
import { TrendCharts, Histogram, Calendar, Star } from '@element-plus/icons-vue'

// --- 状态定义 ---
const loading = ref(false)
const queryParams = reactive({
  spotId: '', // 默认为空，代表福州全域
  year: new Date().getFullYear().toString()
})

const scenicList = ref([])
const trafficData = ref(null)
const forecastData = ref(null)
const recommendData = ref(null)
const monthlyChartRef = ref(null)
const forecastChartRef = ref(null)
let monthlyChart = null
let forecastChart = null

// 计算属性：当前显示的标题
const currentTargetName = computed(() => {
  if (!queryParams.spotId) return '福州全域 (Fuzhou Overall)'
  const spot = scenicList.value.find(s => s.name === queryParams.spotId) // 注意这里用name匹配，取决于Select绑定的值
  return spot ? `${spot.name} (单点分析)` : queryParams.spotId
})

// --- API 调用 ---
// 1. 获取景区列表
const fetchScenicList = async () => {
  try {
    const res = await getScenicListAPI()
    if (res.data && res.data.length > 0) {
      // 映射数据，但不强制设置 spotId，保持默认为空（全域）
      scenicList.value = res.data.map(item => ({
        id: item.scenic_spot || item.spot_name, // 确保有唯一key
        name: item.scenic_spot || item.spot_name
      }))
    }
  } catch (error) {
    console.error('获取景区列表失败:', error)
  }
}

// 2. 获取核心分析数据
const fetchData = async () => {
  loading.value = true
  try {
    // 构造请求参数，如果为空字符串，通常API会理解为不传或传空，即查询所有
    // 如果后端一定要传 'all' 或其他特殊值，请在此处修改
    const requestParams = {
      spotId: queryParams.spotId || undefined, // undefined 在 axios 中通常会被忽略不传
      year: parseInt(queryParams.year)
    }

    const [trafficRes, forecastRes, recommendRes] = await Promise.all([
      getTrafficAnalysisAPI(requestParams),
      getTrafficForecastAPI({ spotId: queryParams.spotId || undefined, monthsAhead: 12 }),
      getRecommendVisitTimeAPI({ spotId: queryParams.spotId || undefined })
    ])

    // 处理历史人流量数据
    if (trafficRes.data && trafficRes.data.monthly_traffic) {
      trafficData.value = trafficRes.data
      nextTick(() => {
        initMonthlyChart()
      })
    }
    
    // 处理预测数据
    if (forecastRes.data) {
      forecastData.value = forecastRes.data
      nextTick(() => {
        initForecastChart()
      })
    }

    // 前端智能推荐算法：基于福州气候特点和人流量数据
    if (trafficRes.data && trafficRes.data.monthly_traffic) {
      recommendData.value = calculateSmartRecommendation(trafficRes.data.monthly_traffic, forecastRes.data)
    } else {
      recommendData.value = {
        bestVisitTime: '数据不足',
        recommendedMonths: [],
        peakMonths: [],
        offPeakMonths: []
      }
    }
  } catch (error) {
    console.error('数据获取异常:', error)
    ElMessage.warning('部分数据加载失败，请检查网络或后端服务')
  } finally {
    loading.value = false
  }
}

// 事件处理
const handleFilterChange = () => {
  fetchData()
}

const formatNumber = (num) => {
  if (!num) return '0'
  return num.toLocaleString('zh-CN')
}

/**
 * 福州气候舒适度评分（基于实际气候数据）
 * 参考：福州旅游最佳时间建议
 * 最佳季节：秋季(10-11月)、冬季(12-2月)
 * 淡季：春季(3-4月阴雨)、梅雨期(5-6月)、夏季(7-8月高温台风)
 */
const getFuzhouClimateScore = (month) => {
  const climateScores = {
    1: 85,  // 冬季，温暖舒适
    2: 85,  // 冬季，阳光明媚
    3: 60,  // 春季，阴雨绵绵
    4: 65,  // 春季，冷暖变化大
    5: 50,  // 梅雨期，暴雨频繁
    6: 45,  // 梅雨期，降水最多
    7: 40,  // 夏季，高温台风
    8: 40,  // 夏季，极端天气
    9: 80,  // 初秋，开始舒适
    10: 95, // 秋季黄金期，气候宜人
    11: 95, // 秋季黄金期，天高云淡
    12: 85  // 冬季，温和干燥
  }
  return climateScores[month] || 60
}

/**
 * 获取月份名称
 */
const getMonthName = (month) => {
  return `${month}月`
}

/**
 * 获取季节类型
 */
const getSeasonType = (month) => {
  if (month >= 3 && month <= 5) return '春季'
  if (month >= 6 && month <= 8) return '夏季'
  if (month >= 9 && month <= 11) return '秋季'
  return '冬季'
}

/**
 * 智能推荐算法：综合评分模型
 * 评分维度：
 * 1. 人流拥挤度评分（30%）- 人流越少得分越高
 * 2. 游客满意度评分（30%）- 评分越高得分越高  
 * 3. 气候舒适度评分（30%）- 基于福州实际气候特点
 * 4. 未来趋势评分（10%）- 预测人流增长趋势
 */
const calculateSmartRecommendation = (monthlyTraffic, forecastData) => {
  if (!monthlyTraffic || monthlyTraffic.length === 0) {
    return {
      bestVisitTime: '数据不足',
      recommendedMonths: [],
      peakMonths: [],
      offPeakMonths: []
    }
  }

  // 1. 计算统计值
  const visitors = monthlyTraffic.map(m => m.visitor_count)
  const maxVisitors = Math.max(...visitors)
  const minVisitors = Math.min(...visitors)
  const avgVisitors = visitors.reduce((a, b) => a + b, 0) / visitors.length

  // 2. 提取预测数据
  const forecastMap = {}
  if (forecastData && forecastData.forecast) {
    forecastData.forecast.forEach(f => {
      if (f.month && f.predicted_visitors) {
        const monthNum = parseInt(f.month.split('-')[1])
        forecastMap[monthNum] = f.predicted_visitors
      }
    })
  }

  // 3. 为每个月计算综合评分
  const monthScores = monthlyTraffic.map(data => {
    const month = parseInt(data.month.split('-')[1])
    const visitorCount = data.visitor_count
    const avgRating = data.avg_rating || 4.5

    // 3.1 人流拥挤度评分（越少越好）
    let crowdScore = 0
    if (maxVisitors > minVisitors) {
      crowdScore = 100 * (1 - (visitorCount - minVisitors) / (maxVisitors - minVisitors))
    }

    // 3.2 游客满意度评分
    const satisfactionScore = (avgRating / 5.0) * 100

    // 3.3 福州气候舒适度评分
    const climateScore = getFuzhouClimateScore(month)

    // 3.4 未来趋势评分
    let trendScore = 50
    if (forecastMap[month]) {
      const predictedVisitors = forecastMap[month]
      const growthRate = (predictedVisitors - visitorCount) / visitorCount
      if (growthRate < -0.05) {
        trendScore = 100 // 人流下降，最佳
      } else if (growthRate < 0.1) {
        trendScore = 80  // 小幅增长
      } else if (growthRate < 0.3) {
        trendScore = 60  // 中等增长
      } else {
        trendScore = 40  // 大幅增长，拥挤
      }
    }

    // 3.5 综合评分（加权）
    const totalScore = crowdScore * 0.3 + satisfactionScore * 0.3 + 
                      climateScore * 0.3 + trendScore * 0.1

    // 3.6 拥挤等级判断
    let crowdLevel
    if (visitorCount < avgVisitors * 0.7) {
      crowdLevel = '舒适'
    } else if (visitorCount < avgVisitors * 1.3) {
      crowdLevel = '适中'
    } else {
      crowdLevel = '拥挤'
    }

    return {
      month: month,
      monthName: getMonthName(month),
      visitorCount: visitorCount,
      avgRating: Math.round(avgRating * 10) / 10,
      crowdLevel: crowdLevel,
      seasonType: getSeasonType(month),
      totalScore: Math.round(totalScore * 10) / 10,
      crowdScore: Math.round(crowdScore * 10) / 10,
      satisfactionScore: Math.round(satisfactionScore * 10) / 10,
      climateScore: climateScore,
      trendScore: Math.round(trendScore * 10) / 10,
      predictedVisitors: forecastMap[month]
    }
  })

  // 4. 排序并筛选推荐月份（综合得分前6名）
  const sortedMonths = [...monthScores].sort((a, b) => b.totalScore - a.totalScore)
  const recommendedMonths = sortedMonths.slice(0, 6)

  // 5. 识别高峰期（客流量 > 平均值 * 1.5）
  const peakMonthsData = monthScores.filter(m => m.visitorCount > avgVisitors * 1.5)
  const peakMonths = peakMonthsData.map(m => m.monthName)

  // 6. 识别错峰期（客流量 < 平均值 * 0.7 且气候舒适度 >= 70）
  const offPeakMonthsData = monthScores.filter(m => 
    m.visitorCount < avgVisitors * 0.7 && m.climateScore >= 70
  )
  const offPeakMonths = offPeakMonthsData.map(m => m.monthName)

  // 7. 确定最佳游玩时间（综合评分最高的月份）
  const bestMonth = sortedMonths[0]
  const bestVisitTime = bestMonth ? bestMonth.monthName : '10-11月（秋季）'

  return {
    bestVisitTime: bestVisitTime,
    recommendedMonths: recommendedMonths,
    peakMonths: peakMonths,
    offPeakMonths: offPeakMonths,
    peakMonthsDetail: peakMonthsData,
    offPeakMonthsDetail: offPeakMonthsData,
    avgVisitors: Math.round(avgVisitors),
    algorithmVersion: '前端智能推荐v1.0 - 基于福州气候特点'
  }
}

// --- ECharts 配置 (暗黑科技风) ---
const commonChartConfig = {
  backgroundColor: 'transparent',
  textStyle: { fontFamily: 'sans-serif' },
  grid: { left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true },
  tooltip: {
    backgroundColor: 'rgba(5, 10, 31, 0.95)',
    borderColor: '#00f2fe',
    textStyle: { color: '#fff' },
    trigger: 'axis'
  }
}

const initMonthlyChart = () => {
  if (!monthlyChartRef.value || !trafficData.value) return
  if (monthlyChart) monthlyChart.dispose()

  monthlyChart = echarts.init(monthlyChartRef.value)

  const months = trafficData.value.monthly_traffic.map(item => item.month)
  const visitors = trafficData.value.monthly_traffic.map(item => item.visitor_count)

  const option = {
    ...commonChartConfig,
    xAxis: {
      type: 'category',
      data: months,
      boundaryGap: false,
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      axisLabel: { color: '#8fb6e6' },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      name: '游客量 (人次)',
      nameTextStyle: { color: '#8fb6e6', padding: [0, 0, 0, 20] },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)', type: 'dashed' } },
      axisLabel: { color: '#8fb6e6' }
    },
    series: [{
      name: '游客量',
      type: 'line',
      data: visitors,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      itemStyle: { color: '#00f2fe', borderColor: '#fff', borderWidth: 2 },
      lineStyle: { width: 3, color: '#00f2fe', shadowColor: 'rgba(0,242,254,0.5)', shadowBlur: 10 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(0, 242, 254, 0.4)' },
          { offset: 1, color: 'rgba(0, 242, 254, 0.05)' }
        ])
      }
    }]
  }
  monthlyChart.setOption(option)
}

const initForecastChart = () => {
  if (!forecastChartRef.value || !forecastData.value) return
  if (forecastChart) forecastChart.dispose()

  forecastChart = echarts.init(forecastChartRef.value)

  const months = forecastData.value.forecast.map(item => item.month)
  const predictedVisitors = forecastData.value.forecast.map(item => item.predicted_visitors)

  const option = {
    ...commonChartConfig,
    xAxis: {
      type: 'category',
      data: months,
      boundaryGap: false,
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      axisLabel: { color: '#8fb6e6', rotate: 30 },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      name: '预测游客量',
      nameTextStyle: { color: '#8fb6e6', padding: [0, 0, 0, 20] },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)', type: 'dashed' } },
      axisLabel: { color: '#8fb6e6' }
    },
    series: [{
      name: '预测游客量',
      type: 'line',
      data: predictedVisitors,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      itemStyle: { color: '#f093fb', borderColor: '#fff', borderWidth: 2 },
      lineStyle: { width: 3, color: '#f093fb', shadowColor: 'rgba(240,147,251,0.5)', shadowBlur: 10, type: 'dashed' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(240, 147, 251, 0.4)' },
          { offset: 1, color: 'rgba(240, 147, 251, 0.05)' }
        ])
      }
    }]
  }
  forecastChart.setOption(option)
}

const getCrowdClass = (level) => {
  const map = { '舒适': 'comfort', '适中': 'medium', '拥挤': 'crowded' }
  return map[level] || ''
}

const handleResize = () => {
  monthlyChart?.resize()
  forecastChart?.resize()
}

onMounted(async () => {
  await fetchScenicList()
  await fetchData() // 初始调用，spotId为空，查询福州全域
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  monthlyChart?.dispose()
  forecastChart?.dispose()
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

.seasonal-container {
  min-height: 100vh;
  padding: 20px;
  background:
      radial-gradient(circle at 50% 0%, rgba(0, 242, 254, 0.1) 0%, transparent 60%),
      linear-gradient(180deg, #050a1f 0%, #02040d 100%);
  color: $text-main;
  font-family: 'Inter', sans-serif;
}

/* --- 1. 顶部控制台 --- */
.control-console {
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.2);
  padding: 15px 0;
  margin-bottom: 25px;
  border-radius: 4px;
  position: relative;

  .console-decoration {
    position: absolute;
    width: 40px; height: 100%;
    border: 1px solid rgba(255,255,255,0.1);
    border-top: none; border-bottom: none;
    &.left { left: 20px; border-left: 3px solid $primary; }
    &.right { right: 20px; border-right: 3px solid $primary; }
  }

  .tech-form {
    z-index: 1;
    :deep(.el-form-item) { margin-bottom: 0; margin-right: 40px; }
    :deep(.el-form-item__label) { color: $text-sub; font-weight: 500; }
  }
}

/* --- 2. 通用面板 --- */
.tech-panel {
  background: $bg-panel;
  border: 1px solid $border-color;
  position: relative;
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(10px);

  .corner {
    position: absolute;
    width: 10px; height: 10px;
    border: 2px solid $primary;
    transition: all 0.3s;
    opacity: 0.7;
    &.t-l { top: -1px; left: -1px; border-width: 2px 0 0 2px; }
    &.t-r { top: -1px; right: -1px; border-width: 2px 2px 0 0; }
    &.b-l { bottom: -1px; left: -1px; border-width: 0 0 2px 2px; }
    &.b-r { bottom: -1px; right: -1px; border-width: 0 2px 2px 0; }
  }

  &:hover .corner { width: 15px; height: 15px; opacity: 1; box-shadow: 0 0 10px $primary; }

  .panel-header {
    height: 50px;
    padding: 0 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(255, 255, 255, 0.02);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);

    .header-title {
      display: flex; align-items: center; gap: 8px;
      .icon { color: $primary; font-size: 18px; }
      .title { color: #fff; font-size: 16px; font-weight: 600; letter-spacing: 1px; }
    }

    .header-tag {
      font-size: 12px;
      background: rgba(0,242,254,0.1);
      color: $primary;
      padding: 2px 8px;
      border-radius: 4px;
      border: 1px solid rgba(0,242,254,0.3);
    }

    .header-line {
      flex: 1; margin-left: 20px;
      height: 1px;
      background: linear-gradient(90deg, rgba(255,255,255,0.1), transparent);
    }
  }
}

.chart-panel {
  height: 400px;
  .chart-box { width: 100%; height: 100%; padding: 10px; }
}

/* --- 3. 智能推荐引擎样式 --- */
.full-panel { min-height: 400px; }

.recommend-body {
  padding: 30px;
}

.engine-layout {
  display: flex;
  gap: 40px;
  align-items: stretch;

  @media (max-width: 992px) { flex-direction: column; }
}

/* 左侧核心反应堆 */
.core-reactor {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  min-height: 250px;
  background: radial-gradient(circle, rgba(0,242,254,0.05), transparent 70%);

  .reactor-ring {
    position: absolute;
    border-radius: 50%;
    border: 2px solid transparent;
    &.outer { width: 220px; height: 220px; border-top-color: rgba(0,242,254,0.3); border-bottom-color: rgba(0,242,254,0.3); animation: spin 10s linear infinite; }
    &.inner { width: 180px; height: 180px; border-left-color: $secondary; border-right-color: $secondary; animation: spin 6s linear infinite reverse; }
  }

  .reactor-content {
    text-align: center;
    z-index: 1;
    .label { color: $secondary; font-size: 12px; letter-spacing: 2px; margin-bottom: 10px; }
    .value { font-size: 28px; font-weight: bold; color: #fff; text-shadow: 0 0 15px $primary; margin-bottom: 5px; }
    .desc { font-size: 12px; color: $text-sub; transform: scale(0.9); }
  }
}

/* 右侧详情矩阵 */
.details-matrix {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;

  .matrix-row {
    background: rgba(255,255,255,0.02);
    padding: 15px;
    border-radius: 6px;

    .row-label {
      font-size: 14px; color: #fff; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;
      .dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
      .green { background: #43e97b; box-shadow: 0 0 5px #43e97b; }
      .red { background: #f56c6c; box-shadow: 0 0 5px #f56c6c; }
      .blue { background: #4facfe; box-shadow: 0 0 5px #4facfe; }
    }

    &.split {
      display: flex; gap: 20px;
      .split-item { flex: 1; }
    }
  }
}

/* 月份小卡片 */
.month-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 10px;

  .mini-month-card {
    background: rgba(0,0,0,0.2);
    border: 1px solid rgba(255,255,255,0.1);
    padding: 10px;
    border-radius: 4px;
    transition: all 0.3s;

    &:hover { border-color: $primary; box-shadow: 0 0 10px rgba(0,242,254,0.1); }

    .m-head {
      display: flex; justify-content: space-between; margin-bottom: 8px;
      .name { color: #fff; font-weight: bold; }
      .score { color: #f7ba2a; font-size: 12px; display: flex; align-items: center; gap: 2px; }
    }
    .m-body {
      display: flex; flex-direction: column; gap: 4px;
      .tag {
        font-size: 10px; padding: 1px 4px; border-radius: 2px; width: fit-content;
        &.comfort { color: #43e97b; border: 1px solid rgba(67, 233, 123, 0.3); }
        &.medium { color: #e6a23c; border: 1px solid rgba(230, 162, 60, 0.3); }
        &.crowded { color: #f56c6c; border: 1px solid rgba(245, 108, 108, 0.3); }
      }
      .visitor { font-size: 12px; color: $text-sub; }
    }
  }
}

/* 标签样式 */
.tags-container {
  display: flex; flex-wrap: wrap; gap: 8px;
  .tech-tag {
    padding: 2px 10px; border-radius: 12px; font-size: 12px;
    &.peak { background: rgba(245, 108, 108, 0.1); border: 1px solid rgba(245, 108, 108, 0.3); color: #f56c6c; }
    &.offpeak { background: rgba(79, 172, 254, 0.1); border: 1px solid rgba(79, 172, 254, 0.3); color: #4facfe; }
  }
  .empty-text { color: $text-sub; font-size: 12px; font-style: italic; }
}

@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>

<style lang="scss">
/* 全局覆盖 Select 和 DatePicker 下拉样式 */
.tech-popper {
  background-color: rgba(5, 10, 31, 0.95) !important;
  border: 1px solid rgba(0, 242, 254, 0.3) !important;

  .el-select-dropdown__item, .el-date-table td {
    color: #a6b9d6 !important;
    &:hover, &.current, &.selected {
      color: #00f2fe !important;
      background-color: rgba(0, 242, 254, 0.1) !important;
      font-weight: bold;
    }
  }

  .el-picker-panel {
    background: transparent !important;
    color: #fff !important;
    border: none !important;
  }

  .el-date-picker__header {
    margin: 10px;
    .el-date-picker__header-label { color: #fff !important; }
    button { color: #00f2fe !important; }
  }

  .el-popper__arrow::before {
    background-color: rgba(5, 10, 31, 0.95) !important;
    border: 1px solid rgba(0, 242, 254, 0.3) !important;
  }
}

/* 输入框通用覆盖 */
.tech-select, .tech-date {
  width: 220px;
  .el-input__wrapper {
    background: rgba(0, 0, 0, 0.3) !important;
    box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.15) !important;
    &.is-focus { box-shadow: 0 0 0 1px #00f2fe !important; }
  }
  .el-input__inner { color: #fff !important; font-weight: bold; }
}
</style>