<template>
  <div class="dashboard-container">
    <!-- 顶部数据概览 -->
    <div class="stats-grid">
      <div
          class="stat-panel"
          v-for="(stat, index) in stats"
          :key="stat.title"
          :class="`delay-${index}`"
      >
        <!-- 装饰角标 -->
        <i class="corner t-l"></i><i class="corner t-r"></i>
        <i class="corner b-l"></i><i class="corner b-r"></i>

        <div class="icon-wrapper" :class="`style-${index}`">
          <!-- 修复：直接使用动态组件渲染图标 -->
          <el-icon :size="28"><component :is="stat.icon" /></el-icon>
        </div>
        <div class="content">
          <div class="number-wrap">
            <span class="num">{{ stat.value }}</span>
            <span class="unit" v-if="index === 2">分</span>
            <span class="unit" v-else-if="index === 0">个</span>
          </div>
          <div class="label">{{ stat.title }}</div>
        </div>
      </div>
    </div>

    <!-- 中间图表区 -->
    <el-row :gutter="20" class="main-charts">
      <el-col :xs="24" :lg="12">
        <div class="tech-card">
          <div class="card-header">
            <div class="header-icon"><TrophyBase /></div>
            <span class="header-title">景区评分排行榜 TOP10</span>
            <div class="header-line"></div>
          </div>
          <div ref="ratingChartRef" class="chart-box"></div>
        </div>
      </el-col>

      <el-col :xs="24" :lg="12">
        <div class="tech-card">
          <div class="card-header">
            <div class="header-icon"><User /></div>
            <span class="header-title">景区游客流量排行</span>
            <div class="header-line"></div>
          </div>
          <div ref="visitorChartRef" class="chart-box"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 底部图表区 -->
    <el-row :gutter="20" class="bottom-charts">
      <el-col :xs="24" :lg="14">
        <div class="tech-card">
          <div class="card-header">
            <div class="header-icon"><DataLine /></div>
            <span class="header-title">全域评分分布概览</span>
            <div class="header-line"></div>
          </div>
          <!-- 图表容器 -->
          <div ref="ratingDistChartRef" class="chart-box"></div>
        </div>
      </el-col>

      <el-col :xs="24" :lg="10">
        <div class="tech-card">
          <div class="card-header">
            <div class="header-icon"><Star /></div>
            <span class="header-title">热门景区实时榜单</span>
            <div class="header-line"></div>
            <span class="tag">HOT</span>
          </div>
          <div class="ranking-container">
            <!-- 列表头部 -->
            <div class="rank-header-row">
              <span class="col-rank">排名</span>
              <span class="col-name">景区名称</span>
              <span class="col-val">评分热度</span>
            </div>
            <!-- 列表内容 -->
            <div class="rank-list-scroll">
              <div
                  v-for="(spot, index) in topSpots"
                  :key="index"
                  class="rank-item"
              >
                <div class="rank-badge" :class="`top-${index + 1}`">{{ index + 1 }}</div>
                <div class="spot-name">{{ spot.name }}</div>
                <div class="spot-data">
                  <div class="score-text">{{ spot.rating }}分</div>
                  <div class="progress-bg">
                    <div class="progress-bar" :style="{ width: (spot.rating / 5 * 100) + '%' }"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
// 【修复1】导入缺失的 API
import { getOverviewAPI, getScenicRankingAPI, getRatingDistributionAPI } from '@/api/analysis'
import { Location, User, ChatDotRound, Star, TrophyBase, DataLine } from '@element-plus/icons-vue'

// 【修复2】Icon 必须作为对象传递，而不是字符串
const stats = ref([
  { title: '监测景区总数', value: 0, icon: Location },
  { title: '累计评论量', value: 0, icon: ChatDotRound },
  { title: '全域平均分', value: 0, icon: Star },
  { title: '总互动人数', value: 0, icon: User }
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

    if (ratingRes.data?.length > 0) {
      initRatingChart(ratingRes.data)
      topSpots.value = ratingRes.data.slice(0, 5).map(item => ({
        name: item.scenic_spot || item.spot_name,
        rating: parseFloat(item.avg_rating || item.rating || 0).toFixed(1)
      }))
    }

    if (visitorRes.data?.length > 0) {
      initVisitorChart(visitorRes.data)
    }

    // 初始化分布图（无论是否有排行数据）
    await initRatingDistChart()
  } catch (error) {
    console.error('获取排行数据失败:', error)
  }
}

// 通用图表配置
const commonChartConfig = {
  textStyle: { fontFamily: 'sans-serif' },
  grid: { top: '15%', left: '2%', right: '4%', bottom: '5%', containLabel: true },
  tooltip: {
    backgroundColor: 'rgba(0, 20, 40, 0.95)',
    borderColor: '#00f2fe',
    textStyle: { color: '#fff' },
    padding: [10, 15],
    extraCssText: 'box-shadow: 0 0 10px rgba(0, 242, 254, 0.3);'
  }
}

const initRatingChart = (data) => {
  if (!ratingChartRef.value) return
  ratingChart = echarts.init(ratingChartRef.value)

  const option = {
    ...commonChartConfig,
    tooltip: { ...commonChartConfig.tooltip, trigger: 'axis' },
    xAxis: {
      type: 'value',
      max: 5,
      splitLine: { show: true, lineStyle: { color: 'rgba(255,255,255,0.05)' } },
      axisLabel: { color: '#8fb6e6' }
    },
    yAxis: {
      type: 'category',
      data: data.map(item => item.scenic_spot || item.spot_name).reverse(),
      axisLabel: { color: '#fff', width: 90, overflow: 'truncate' },
      axisTick: { show: false },
      axisLine: { show: false }
    },
    series: [{
      type: 'bar',
      barWidth: 10,
      data: data.map(item => parseFloat(item.avg_rating || item.rating || 0)).reverse(),
      itemStyle: {
        borderRadius: [0, 50, 50, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#0072ff' },
          { offset: 1, color: '#00c6ff' }
        ])
      },
      showBackground: true,
      backgroundStyle: { color: 'rgba(255,255,255,0.02)', borderRadius: [0, 50, 50, 0] },
      label: { show: true, position: 'right', color: '#00c6ff', fontWeight: 'bold' }
    }]
  }
  ratingChart.setOption(option)
}

const initVisitorChart = (data) => {
  if (!visitorChartRef.value) return
  visitorChart = echarts.init(visitorChartRef.value)

  const option = {
    ...commonChartConfig,
    tooltip: { ...commonChartConfig.tooltip, trigger: 'axis' },
    grid: { ...commonChartConfig.grid, bottom: '15%' },
    xAxis: {
      type: 'category',
      data: data.map(item => item.scenic_spot || item.spot_name),
      axisLabel: { color: '#8fb6e6', rotate: 20, fontSize: 10 },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { type: 'dashed', color: 'rgba(255,255,255,0.05)' } },
      axisLabel: { color: '#8fb6e6' }
    },
    series: [{
      type: 'bar',
      barWidth: 14,
      data: data.map(item => parseInt(item.visitor_count || item.total_visitors || 0)),
      itemStyle: {
        borderRadius: [4, 4, 0, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#f72585' },
          { offset: 1, color: '#7209b7' }
        ])
      }
    }]
  }
  visitorChart.setOption(option)
}

// 【重点修改】全域评分分布概览图表 - 美化版
const initRatingDistChart = async () => {
  if (!ratingDistChartRef.value) return
  ratingDistChart = echarts.init(ratingDistChartRef.value)

  try {
    const res = await getRatingDistributionAPI()
    const distribution = res.data?.distribution || []

    // 定义评分段渐变色板
    const colorMap = {
      '4.5-5.0分': { start: '#00f2fe', end: '#4facfe' },
      '4.0-4.5分': { start: '#43e97b', end: '#38f9d7' },
      '3.5-4.0分': { start: '#fa709a', end: '#fee140' },
      '3.0-3.5分': { start: '#f093fb', end: '#f5576c' },
      '3.0分以下': { start: '#ff6b6b', end: '#ee5a6f' }
    }

    // 使用后端返回的评分段数据
    let chartData = distribution.length > 0 ? distribution.map((item) => {
      const label = item.label || '未知'
      const g = colorMap[label] || { start: '#96fbc4', end: '#f9f586' }
      
      return {
        value: item.count || 0,
        name: label,
        percentage: item.percentage || 0,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
            { offset: 0, color: g.start },
            { offset: 1, color: g.end }
          ])
        }
      }
    }) : [{ value: 0, name: '暂无数据', percentage: 0, itemStyle: { color: '#333' } }]

    // 计算总数用于中心显示
    const total = chartData.reduce((prev, curr) => prev + (curr.value || 0), 0)

    const option = {
      // 移除 tooltip，因为右侧图例已经很详细了，或者保留做简单提示
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(0, 20, 40, 0.9)',
        borderColor: '#00f2fe',
        formatter: (params) => {
          return `${params.marker} ${params.name}<br/>
                  <span style="display:inline-block;width:50px;color:#ccc">数量:</span> <b style="color:#fff">${params.value}</b><br/>
                  <span style="display:inline-block;width:50px;color:#ccc">占比:</span> <b style="color:#fff">${params.percent}%</b>`
        }
      },
      legend: {
        orient: 'vertical',
        right: '5%',
        top: 'center',
        itemGap: 15,
        itemWidth: 14,
        itemHeight: 14,
        icon: 'circle',
        textStyle: {
          color: '#fff',
          rich: {
            a: { color: '#8fb6e6', width: 70, fontSize: 13 },
            b: { color: '#fff', fontWeight: 'bold', width: 40, align: 'right', fontSize: 13 },
            c: { color: 'rgba(255,255,255,0.5)', width: 40, align: 'right', fontSize: 12 }
          }
        },
        // 自定义图例格式：评分段 | 数量 | 占比
        formatter: (name) => {
          const item = chartData.find(d => d.name === name)
          if(!item) return name
          return `{a|${name}}{b|${item.value}}{c|${item.percentage}%}`
        }
      },
      series: [
        {
          name: '评分分布',
          type: 'pie',
          radius: ['50%', '75%'], // 环形图更现代
          center: ['30%', '50%'], // 左移，给右侧图例留空间
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 8,
            borderColor: '#0d1b3e', // 配合背景色产生间隙感
            borderWidth: 3
          },
          label: {
            show: false, // 隐藏连线标签，保持整洁
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 18,
              fontWeight: 'bold',
              color: '#fff',
              formatter: '{d}%' // 鼠标悬停显示百分比
            },
            scale: true,
            scaleSize: 10
          },
          data: chartData
        }
      ],
      // 中心装饰文字
      graphic: {
        type: 'group',
        left: '28%', // 配合 center 的 30%
        top: 'center',
        children: [
          {
            type: 'text',
            style: {
              text: total.toString(),
              textAlign: 'center',
              fill: '#fff',
              fontSize: 24,
              fontWeight: 'bold',
              fontFamily: 'DIN Alternate'
            },
            position: [0, -10]
          },
          {
            type: 'text',
            style: {
              text: '总评数',
              textAlign: 'center',
              fill: '#8fb6e6',
              fontSize: 12
            },
            position: [0, 15]
          }
        ]
      }
    }
    ratingDistChart.setOption(option)
  } catch (error) {
    console.error('获取评分分布失败:', error)
  }
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
/* 定义深色科技主题变量 */
$bg-color: transparent;
$card-bg: rgba(13, 27, 62, 0.65);
$border-color: rgba(64, 158, 255, 0.15);
$primary-cyan: #00f2fe;
$primary-blue: #4facfe;
$text-main: #ffffff;
$text-sub: #8fb6e6;

.dashboard-container {
  width: 100%;
  color: $text-main;
  padding-bottom: 20px;
}

/* --- 1. 顶部数据统计面板 --- */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
  @media (max-width: 992px) { grid-template-columns: repeat(2, 1fr); }
  @media (max-width: 576px) { grid-template-columns: 1fr; }
}

.stat-panel {
  position: relative;
  height: 100px;
  background: $card-bg;
  border: 1px solid $border-color;
  padding: 0 20px;
  display: flex;
  align-items: center;
  transition: all 0.3s;
  overflow: hidden;

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 5px 15px rgba(0, 242, 254, 0.15);
    border-color: rgba(0, 242, 254, 0.5);
    background: rgba(13, 27, 62, 0.85);
  }

  .corner {
    position: absolute;
    width: 8px;
    height: 8px;
    border: 2px solid $primary-cyan;
    transition: all 0.3s;
    opacity: 0.6;
    &.t-l { top: 0; left: 0; border-width: 2px 0 0 2px; }
    &.t-r { top: 0; right: 0; border-width: 2px 2px 0 0; }
    &.b-l { bottom: 0; left: 0; border-width: 0 0 2px 2px; }
    &.b-r { bottom: 0; right: 0; border-width: 0 2px 2px 0; }
  }
  &:hover .corner { opacity: 1; width: 12px; height: 12px; }

  .icon-wrapper {
    width: 50px;
    height: 50px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 15px;
    backdrop-filter: blur(4px);
    &.style-0 { background: rgba(0, 242, 254, 0.1); color: #00f2fe; }
    &.style-1 { background: rgba(240, 147, 251, 0.1); color: #f093fb; }
    &.style-2 { background: rgba(255, 206, 86, 0.1); color: #ffce56; }
    &.style-3 { background: rgba(67, 233, 123, 0.1); color: #43e97b; }
  }

  .content {
    .number-wrap {
      display: flex;
      align-items: baseline;
      .num {
        font-family: 'DIN Alternate', sans-serif;
        font-size: 28px;
        font-weight: 700;
        letter-spacing: 1px;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
      }
      .unit { font-size: 12px; color: $text-sub; margin-left: 4px; }
    }
    .label { font-size: 13px; color: $text-sub; margin-top: 4px; }
  }
}

/* --- 2. 通用图表卡片 --- */
.tech-card {
  background: $card-bg;
  border: 1px solid $border-color;
  margin-bottom: 20px;
  height: 420px;
  display: flex;
  flex-direction: column;
  position: relative;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 2px;
    background: linear-gradient(90deg, transparent, $primary-cyan, transparent);
    opacity: 0.5;
  }

  .card-header {
    height: 50px;
    padding: 0 15px;
    display: flex;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    .header-icon { color: $primary-blue; margin-right: 8px; display: flex; align-items: center; }
    .header-title { font-size: 16px; font-weight: 600; color: #fff; letter-spacing: 0.5px; }
    .header-line { flex: 1; height: 1px; background: linear-gradient(90deg, rgba(255,255,255,0.1), transparent); margin: 0 15px; }
    .tag { font-size: 12px; padding: 2px 8px; background: rgba(247, 37, 133, 0.2); color: #f72585; border: 1px solid #f72585; border-radius: 4px; transform: scale(0.9); }
  }

  .chart-box {
    flex: 1;
    width: 100%;
    padding: 10px;
    min-height: 0;
  }
}

/* --- 3. 排行榜样式 --- */
.ranking-container {
  flex: 1;
  padding: 10px 15px;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .rank-header-row {
    display: flex;
    font-size: 12px;
    color: $text-sub;
    padding-bottom: 8px;
    border-bottom: 1px dashed rgba(255, 255, 255, 0.1);
    margin-bottom: 8px;
    .col-rank { width: 40px; text-align: center; }
    .col-name { flex: 1; padding-left: 10px; }
    .col-val { width: 80px; text-align: right; }
  }

  .rank-list-scroll {
    flex: 1;
    overflow-y: auto;
    &::-webkit-scrollbar { width: 4px; }
    &::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 2px; }

    .rank-item {
      display: flex;
      align-items: center;
      padding: 10px 0;
      transition: background 0.2s;
      border-bottom: 1px solid rgba(255, 255, 255, 0.02);
      &:hover { background: rgba(255, 255, 255, 0.03); }

      .rank-badge {
        width: 24px; height: 24px; line-height: 24px; text-align: center;
        border-radius: 4px; background: rgba(255, 255, 255, 0.08); color: $text-sub;
        font-weight: bold; font-size: 12px; margin: 0 8px; flex-shrink: 0;
        &.top-1 { background: #ffc107; color: #000; box-shadow: 0 0 8px rgba(255, 193, 7, 0.4); }
        &.top-2 { background: #e0e0e0; color: #000; }
        &.top-3 { background: #cd7f32; color: #000; }
      }
      .spot-name { flex: 1; font-size: 14px; padding: 0 10px; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .spot-data {
        width: 100px; display: flex; flex-direction: column; align-items: flex-end; justify-content: center;
        .score-text { font-size: 14px; color: $primary-cyan; font-family: 'DIN Alternate', sans-serif; font-weight: bold; }
        .progress-bg {
          width: 100%; height: 4px; background: rgba(255, 255, 255, 0.1); border-radius: 2px; margin-top: 4px; overflow: hidden;
          .progress-bar { height: 100%; background: linear-gradient(90deg, $primary-blue, $primary-cyan); border-radius: 2px; }
        }
      }
    }
  }
}

/* 动画类 */
.delay-0 { animation: fadeIn 0.5s ease 0s backwards; }
.delay-1 { animation: fadeIn 0.5s ease 0.1s backwards; }
.delay-2 { animation: fadeIn 0.5s ease 0.2s backwards; }
.delay-3 { animation: fadeIn 0.5s ease 0.3s backwards; }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>