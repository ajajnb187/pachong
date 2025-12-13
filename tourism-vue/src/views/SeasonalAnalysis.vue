<template>
  <div class="seasonal-container">
    <!-- 顶部控制台 -->
    <div class="control-console">
      <div class="console-decoration left"></div>

      <el-form :inline="true" :model="queryParams" class="tech-form">
        <el-form-item label="分析对象 / Target">
          <el-select
              v-model="queryParams.spotId"
              @change="handleFilterChange"
              placeholder="请选择分析对象"
              popper-class="tech-popper"
              class="tech-select"
          >
            <!-- 核心修复：添加福州全域选项 -->
            <el-option label="福州全域 (总体分析)" value="" />
            <el-option
                v-for="spot in scenicList"
                :key="spot.id"
                :label="spot.name"
                :value="spot.name"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="时间维度 / Year">
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
        </el-form-item>
      </el-form>

      <div class="console-decoration right"></div>
    </div>

    <!-- 数据图表区 -->
    <el-row :gutter="24" class="chart-section">
      <!-- 左侧：月度趋势图 -->
      <el-col :xs="24" :lg="16">
        <div class="tech-panel chart-panel">
          <div class="panel-header">
            <div class="header-title">
              <el-icon class="icon"><TrendCharts /></el-icon>
              <span class="title">月度客流波动趋势</span>
            </div>
            <div class="header-tag">{{ currentTargetName }}</div>
          </div>
          <div ref="monthlyChartRef" class="chart-box"></div>
          <!-- 装饰角标 -->
          <i class="corner t-l"></i><i class="corner t-r"></i>
          <i class="corner b-l"></i><i class="corner b-r"></i>
        </div>
      </el-col>

      <!-- 右侧：季节分布饼图 -->
      <el-col :xs="24" :lg="8">
        <div class="tech-panel chart-panel">
          <div class="panel-header">
            <div class="header-title">
              <el-icon class="icon"><Histogram /></el-icon>
              <span class="title">季节性客流占比</span>
            </div>
          </div>
          <div ref="seasonChartRef" class="chart-box"></div>
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
              <span class="title">AI 智能出行建议引擎</span>
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
import { getSeasonPatternAPI, getRecommendVisitTimeAPI, getScenicListAPI } from '@/api/analysis'
import { TrendCharts, Histogram, Calendar, Star } from '@element-plus/icons-vue'

// --- 状态定义 ---
const loading = ref(false)
const queryParams = reactive({
  spotId: '', // 默认为空，代表福州全域
  year: new Date().getFullYear().toString()
})

const scenicList = ref([])
const seasonData = ref([])
const recommendData = ref(null)
const monthlyChartRef = ref(null)
const seasonChartRef = ref(null)

let monthlyChart = null
let seasonChart = null

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

    const [seasonRes, recommendRes] = await Promise.all([
      getSeasonPatternAPI(requestParams),
      getRecommendVisitTimeAPI({ spotId: queryParams.spotId || undefined })
    ])

    // 处理图表数据
    if (seasonRes.data) {
      // 兼容后端返回结构
      seasonData.value = seasonRes.data.monthlyStats || seasonRes.data || []
      nextTick(() => {
        initMonthlyChart()
        initSeasonChart()
      })
    }

    // 处理推荐数据
    if (recommendRes.data) {
      recommendData.value = recommendRes.data
    } else {
      // 兜底空数据防止报错
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
  return num ? (num / 10000).toFixed(1) + 'w' : '0'
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
  if (!monthlyChartRef.value) return
  if (monthlyChart) monthlyChart.dispose()

  monthlyChart = echarts.init(monthlyChartRef.value)

  const months = seasonData.value.map(item => `${item.month}月`)
  const visitors = seasonData.value.map(item => item.visitorCount || item.visitor_count || 0)

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

const initSeasonChart = () => {
  if (!seasonChartRef.value) return
  if (seasonChart) seasonChart.dispose()

  seasonChart = echarts.init(seasonChartRef.value)

  // 聚合季节数据
  const seasonMap = { '春季': 0, '夏季': 0, '秋季': 0, '冬季': 0 }
  seasonData.value.forEach(item => {
    // 兼容后端字段可能的大小写或下划线
    const season = item.seasonType || item.season_type
    const count = item.visitorCount || item.visitor_count || 0
    if (seasonMap.hasOwnProperty(season)) {
      seasonMap[season] += count
    }
  })

  const option = {
    ...commonChartConfig,
    tooltip: { trigger: 'item', formatter: '{b}: {c}人 ({d}%)' },
    legend: { bottom: '0', textStyle: { color: '#fff' }, icon: 'circle' },
    series: [{
      name: '季节分布',
      type: 'pie',
      radius: ['45%', '70%'],
      center: ['50%', '45%'],
      itemStyle: {
        borderRadius: 4,
        borderColor: '#0b1531',
        borderWidth: 2
      },
      label: { show: false },
      data: [
        { value: seasonMap['春季'], name: '春季', itemStyle: { color: '#43e97b' } },
        { value: seasonMap['夏季'], name: '夏季', itemStyle: { color: '#f5576c' } },
        { value: seasonMap['秋季'], name: '秋季', itemStyle: { color: '#f093fb' } },
        { value: seasonMap['冬季'], name: '冬季', itemStyle: { color: '#4facfe' } }
      ]
    }]
  }
  seasonChart.setOption(option)
}

const getCrowdClass = (level) => {
  const map = { '舒适': 'comfort', '适中': 'medium', '拥挤': 'crowded' }
  return map[level] || ''
}

const handleResize = () => {
  monthlyChart?.resize()
  seasonChart?.resize()
}

onMounted(async () => {
  await fetchScenicList()
  await fetchData() // 初始调用，spotId为空，查询福州全域
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  monthlyChart?.dispose()
  seasonChart?.dispose()
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