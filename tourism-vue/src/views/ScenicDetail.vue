<template>
  <div class="scenic-detail-container">
    <!-- 自定义科技感头部 -->
    <div class="tech-header">
      <div class="back-btn" @click="handleBack">
        <el-icon><ArrowLeft /></el-icon>
        <span>返回全域视图</span>
      </div>
      <div class="title-wrapper">
        <div class="tech-decoration-line"></div>
        <h1 class="scenic-title">{{ scenicName }}</h1>
        <span class="sub-label">Real-time Monitoring</span>
        <div class="tech-decoration-line"></div>
      </div>
      <!-- 右侧装饰占位，保持平衡 -->
      <div class="header-right-decoration"></div>
    </div>

    <!-- 顶部统计数据 -->
    <el-row :gutter="24" class="stats-row">
      <el-col :xs="12" :sm="6" v-for="(stat, index) in stats" :key="stat.label">
        <div
            class="stat-panel"
            :class="`delay-${index}`"
        >
          <!-- 装饰角标 -->
          <i class="corner t-l"></i><i class="corner t-r"></i>
          <i class="corner b-l"></i><i class="corner b-r"></i>

          <div class="stat-inner">
            <div class="icon-box" :class="`style-${index}`">
              <el-icon :size="24"><component :is="stat.icon" /></el-icon>
            </div>
            <div class="info-box">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 中间图表区域 -->
    <el-row :gutter="24" class="charts-row">
      <el-col :xs="24" :lg="12">
        <div class="tech-card">
          <div class="card-title">
            <el-icon class="icon"><TrendCharts /></el-icon>
            <span>景区评分波动趋势</span>
          </div>
          <div ref="ratingTrendChartRef" class="chart-box"></div>
        </div>
      </el-col>

      <el-col :xs="24" :lg="12">
        <div class="tech-card">
          <div class="card-title">
            <el-icon class="icon"><DataLine /></el-icon>
            <span>月度游客流量分析</span>
          </div>
          <div ref="visitorTrendChartRef" class="chart-box"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 底部评论表格 -->
    <el-row :gutter="24" class="review-row">
      <el-col :xs="24">
        <div class="tech-card full-height">
          <div class="card-title">
            <el-icon class="icon"><ChatDotRound /></el-icon>
            <span>最新游客评价采集</span>
          </div>

          <div class="table-container">
            <el-table
                :data="reviews"
                class="custom-tech-table"
                :header-cell-style="{ background: 'rgba(255,255,255,0.05)', color: '#fff', borderBottom: '1px solid rgba(0,242,254,0.2)' }"
                :cell-style="{ background: 'transparent', color: '#a6b9d6', borderBottom: '1px solid rgba(255,255,255,0.05)' }"
            >
              <el-table-column prop="visitor_name" label="游客ID" width="150">
                <template #default="{ row }">
                  <div class="user-cell">
                    <el-avatar :size="24" :icon="User" class="table-avatar" />
                    <span>{{ row.visitor_name }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="rating" label="满意度评分" width="180">
                <template #default="{ row }">
                  <el-rate
                      v-model="row.rating"
                      disabled
                      show-score
                      text-color="#ff9900"
                      score-template="{value}"
                      class="tech-rate"
                  />
                </template>
              </el-table-column>
              <el-table-column prop="travel_date" label="游玩时间" width="150">
                <template #default="{ row }">
                  <span class="date-font">{{ row.travel_date }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="review_content" label="评论详情" show-overflow-tooltip>
                <template #default="{ row }">
                  <span class="review-text">{{ row.review_content }}</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
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
import { Star, User, ChatDotRound, Calendar, TrendCharts, DataLine, ArrowLeft } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const scenicName = computed(() => route.query.spot || '未指定景区')
// 保持原有数据结构
const stats = ref([
  { label: '累计接待游客', value: 0, icon: 'User' },
  { label: '全网评论总数', value: 0, icon: 'ChatDotRound' },
  { label: '综合评分指数', value: 0, icon: 'Star' },
  { label: '参与互动人数', value: 0, icon: 'Calendar' }
])

const reviews = ref([])
const ratingTrendChartRef = ref(null)
const visitorTrendChartRef = ref(null)

let ratingTrendChart = null
let visitorTrendChart = null

// --- API 逻辑保持不变 ---
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

// --- ECharts 配置重写：暗黑风格 ---
const commonChartConfig = {
  grid: { left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true },
  textStyle: { fontFamily: 'sans-serif' },
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(5, 10, 31, 0.9)',
    borderColor: '#00f2fe',
    textStyle: { color: '#fff' }
  }
}

const initRatingTrendChart = (data) => {
  if (!ratingTrendChartRef.value) return
  ratingTrendChart = echarts.init(ratingTrendChartRef.value)

  const months = data.map(item => `${item.month}月`)
  const ratings = data.map(item => item.avgRating || 0)

  const option = {
    ...commonChartConfig,
    tooltip: { ...commonChartConfig.tooltip, formatter: '{b} <br/> 评分: {c}分' },
    xAxis: {
      type: 'category',
      data: months,
      boundaryGap: false,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#8fb6e6' }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 5,
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)', type: 'dashed' } },
      axisLabel: { color: '#8fb6e6' }
    },
    series: [{
      name: '平均评分',
      type: 'line',
      data: ratings,
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      itemStyle: { color: '#f093fb', borderColor: '#fff', borderWidth: 2 },
      lineStyle: { width: 3, color: '#f093fb', shadowColor: 'rgba(240, 147, 251, 0.5)', shadowBlur: 10 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(240, 147, 251, 0.4)' },
          { offset: 1, color: 'rgba(240, 147, 251, 0.05)' }
        ])
      }
    }]
  }
  ratingTrendChart.setOption(option)
}

const initVisitorTrendChart = (data) => {
  if (!visitorTrendChartRef.value) return
  visitorTrendChart = echarts.init(visitorTrendChartRef.value)

  const months = data.map(item => `${item.month}月`)
  const visitors = data.map(item => item.count || 0)

  const option = {
    ...commonChartConfig,
    tooltip: { ...commonChartConfig.tooltip, formatter: '{b} <br/> 游客: {c}人' },
    xAxis: {
      type: 'category',
      data: months,
      boundaryGap: false,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#8fb6e6' }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)', type: 'dashed' } },
      axisLabel: { color: '#8fb6e6' }
    },
    series: [{
      name: '游客量',
      type: 'line',
      data: visitors,
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      itemStyle: { color: '#00f2fe', borderColor: '#fff', borderWidth: 2 },
      lineStyle: { width: 3, color: '#00f2fe', shadowColor: 'rgba(0, 242, 254, 0.5)', shadowBlur: 10 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(0, 242, 254, 0.4)' },
          { offset: 1, color: 'rgba(0, 242, 254, 0.05)' }
        ])
      }
    }]
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
/* --- 变量定义 --- */
$primary: #00f2fe;
$secondary: #4facfe;
$accent: #f093fb;
$bg-dark: #02040d;
$panel-bg: rgba(13, 27, 62, 0.6);
$border-color: rgba(0, 242, 254, 0.2);
$text-main: #fff;
$text-sub: #8fb6e6;

.scenic-detail-container {
  min-height: 100vh;
  padding: 20px;
  background: radial-gradient(circle at 90% 10%, rgba(79, 172, 254, 0.1) 0%, transparent 40%),
  radial-gradient(circle at 10% 90%, rgba(240, 147, 251, 0.1) 0%, transparent 40%),
  linear-gradient(180deg, #050a1f 0%, #02040d 100%);
  color: $text-main;
}

/* --- 1. 科技感头部 --- */
.tech-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 30px;
  position: relative;
  height: 60px;

  .back-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    color: $text-sub;
    transition: all 0.3s;
    padding: 8px 16px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
    border: 1px solid transparent;

    &:hover {
      color: $primary;
      background: rgba(0, 242, 254, 0.1);
      border-color: $border-color;
    }
  }

  .title-wrapper {
    display: flex;
    align-items: center;
    gap: 15px;

    .tech-decoration-line {
      width: 40px;
      height: 2px;
      background: linear-gradient(90deg, transparent, $primary, transparent);
    }

    .scenic-title {
      font-size: 28px;
      font-weight: 700;
      color: #fff;
      text-shadow: 0 0 10px rgba(0, 242, 254, 0.4);
      margin: 0;
    }

    .sub-label {
      font-size: 12px;
      color: $text-sub;
      letter-spacing: 1px;
      text-transform: uppercase;
      background: rgba(0, 0, 0, 0.3);
      padding: 2px 6px;
      border-radius: 2px;
    }
  }

  .header-right-decoration {
    width: 100px;
  }
}

/* --- 2. 统计卡片 --- */
.stats-row {
  margin-bottom: 24px;
}

.stat-panel {
  position: relative;
  height: 100px;
  background: $panel-bg;
  border: 1px solid $border-color;
  padding: 0 20px;
  display: flex;
  align-items: center;
  transition: all 0.3s;
  overflow: hidden;
  animation: slideUp 0.5s ease-out backwards;

  &:hover {
    transform: translateY(-5px);
    background: rgba(13, 27, 62, 0.8);
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);

    .icon-box { transform: scale(1.1); }
  }

  /* 装饰角标 */
  .corner {
    position: absolute;
    width: 6px;
    height: 6px;
    border-color: $primary;
    border-style: solid;
    transition: all 0.3s;
    &.t-l { top: -1px; left: -1px; border-width: 2px 0 0 2px; }
    &.t-r { top: -1px; right: -1px; border-width: 2px 2px 0 0; }
    &.b-l { bottom: -1px; left: -1px; border-width: 0 0 2px 2px; }
    &.b-r { bottom: -1px; right: -1px; border-width: 0 2px 2px 0; }
  }

  .stat-inner {
    display: flex;
    align-items: center;
    width: 100%;

    .icon-box {
      width: 50px;
      height: 50px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 15px;
      transition: transform 0.3s;

      &.style-0 { background: rgba(0, 242, 254, 0.15); color: #00f2fe; }
      &.style-1 { background: rgba(240, 147, 251, 0.15); color: #f093fb; }
      &.style-2 { background: rgba(79, 172, 254, 0.15); color: #4facfe; }
      &.style-3 { background: rgba(67, 233, 123, 0.15); color: #43e97b; }
    }

    .info-box {
      .stat-value {
        font-family: 'DIN Alternate', sans-serif;
        font-size: 26px;
        font-weight: 700;
        color: #fff;
        text-shadow: 0 0 8px rgba(255,255,255,0.2);
      }
      .stat-label {
        font-size: 13px;
        color: $text-sub;
        margin-top: 4px;
      }
    }
  }
}

/* --- 3. 图表与卡片通用 --- */
.charts-row {
  margin-bottom: 24px;
}

.tech-card {
  background: $panel-bg;
  border: 1px solid rgba(255, 255, 255, 0.05);
  padding: 20px;
  position: relative;
  margin-bottom: 20px; /* 移动端适配 */

  /* 顶部发光条 */
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0, 242, 254, 0.5), transparent);
  }

  .card-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 600;
    color: #fff;
    margin-bottom: 20px;

    .icon { color: $primary; font-size: 18px; }
  }

  .chart-box {
    height: 350px;
    width: 100%;
  }
}

/* --- 4. 表格区域 --- */
.custom-tech-table {
  /* 覆盖 Element 表格默认背景 */
  --el-table-bg-color: transparent !important;
  --el-table-tr-bg-color: transparent !important;
  --el-table-header-bg-color: transparent !important;
  --el-table-border: none;
  --el-table-row-hover-bg-color: rgba(0, 242, 254, 0.05) !important;
  background: transparent !important;

  .user-cell {
    display: flex;
    align-items: center;
    gap: 8px;
    .table-avatar { background: rgba(255,255,255,0.1); color: $primary; }
  }

  .date-font {
    font-family: monospace;
    color: $text-sub;
  }

  .review-text {
    color: #dcdfe6;
  }

  /* 评分组件微调 */
  .tech-rate {
    :deep(.el-rate__icon) {
      margin-right: 2px;
    }
    :deep(.el-rate__text) {
      color: #ff9900 !important;
      font-weight: bold;
    }
  }
}

/* 动画延迟类 */
.delay-0 { animation-delay: 0s; }
.delay-1 { animation-delay: 0.1s; }
.delay-2 { animation-delay: 0.2s; }
.delay-3 { animation-delay: 0.3s; }

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 响应式 */
@media (max-width: 768px) {
  .tech-header {
    flex-direction: column;
    height: auto;
    align-items: flex-start;
    gap: 15px;

    .title-wrapper {
      width: 100%;
      justify-content: center;
    }
  }
}
</style>