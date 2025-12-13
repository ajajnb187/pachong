<template>
  <div class="ranking-container">
    <!-- 顶部筛选控制区 -->
    <div class="control-bar">
      <div class="bar-decoration-left"></div>

      <el-form :inline="true" :model="queryParams" class="tech-form">
        <el-form-item label="分析维度 / Dimension">
          <el-select
              v-model="queryParams.rankType"
              @change="fetchRanking"
              popper-class="tech-select-dropdown"
              class="tech-select"
          >
            <el-option label="🔥 评分热度" value="rating" />
            <el-option label="👥 游客流量" value="visitor" />
            <el-option label="💬 评论体量" value="review" />
          </el-select>
        </el-form-item>

        <el-form-item label="TOP 范围 / Range">
          <el-select
              v-model="queryParams.limit"
              @change="fetchRanking"
              popper-class="tech-select-dropdown"
              class="tech-select"
          >
            <el-option label="TOP 10" :value="10" />
            <el-option label="TOP 20" :value="20" />
            <el-option label="TOP 30" :value="30" />
          </el-select>
        </el-form-item>
      </el-form>

      <div class="bar-decoration-right"></div>
    </div>

    <!-- 主内容区 -->
    <el-row :gutter="24" class="main-content">
      <!-- 左侧：可视化图表 -->
      <el-col :xs="24" :lg="16">
        <div class="tech-panel chart-panel">
          <div class="panel-header">
            <el-icon class="icon"><TrendCharts /></el-icon>
            <span class="title">{{ rankTypeMap[queryParams.rankType] }}趋势分析</span>
            <div class="header-line"></div>
          </div>
          <div class="panel-body">
            <div ref="barChartRef" class="chart-container"></div>
          </div>
          <!-- 装饰角标 -->
          <i class="corner t-l"></i><i class="corner t-r"></i>
          <i class="corner b-l"></i><i class="corner b-r"></i>
        </div>
      </el-col>

      <!-- 右侧：排行榜列表 -->
      <el-col :xs="24" :lg="8">
        <div class="tech-panel list-panel">
          <div class="panel-header">
            <el-icon class="icon"><Trophy /></el-icon>
            <span class="title">实时数据榜单</span>
            <div class="header-line"></div>
          </div>

          <div class="ranking-scroll-area">
            <div
                v-for="(item, index) in rankingData"
                :key="index"
                class="rank-item"
                :class="{ 'top-3': index < 3 }"
                @click="handleItemClick(item)"
            >
              <!-- 排名徽章 -->
              <div class="rank-num-wrapper">
                <div class="rank-num" :class="`rank-${index + 1}`">
                  <span v-if="index < 3">NO.</span>{{ index + 1 }}
                </div>
                <div class="rank-line" v-if="index < 3"></div>
              </div>

              <!-- 内容信息 -->
              <div class="item-content">
                <div class="item-main">
                  <span class="spot-name">{{ item.scenic_spot || item.spot_name }}</span>
                  <div class="item-tags" v-if="index < 3">HOT</div>
                </div>

                <div class="item-data">
                  <template v-if="queryParams.rankType === 'rating'">
                    <el-rate
                        v-model="item.displayRating"
                        disabled
                        show-score
                        text-color="#00f2fe"
                        score-template="{value}"
                        class="tech-rate"
                    />
                  </template>
                  <template v-else-if="queryParams.rankType === 'visitor'">
                    <span class="data-value num-font">{{ (item.visitor_count || item.total_visitors).toLocaleString() }}</span>
                    <span class="data-unit">人次</span>
                  </template>
                  <template v-else>
                    <span class="data-value num-font">{{ (item.review_count || item.total_reviews).toLocaleString() }}</span>
                    <span class="data-unit">条</span>
                  </template>
                </div>
              </div>

              <!-- 悬停光效 -->
              <div class="hover-glow"></div>
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
import { ref, reactive, onMounted, onBeforeUnmount, nextTick } from 'vue'
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
  rating: '景区评分',
  visitor: '游客流量',
  review: '评论热度'
}

const rankingData = ref([])
const barChartRef = ref(null)
let barChart = null

// API调用保持不变
const fetchRanking = async () => {
  try {
    const res = await getScenicRankingAPI(queryParams)
    if (res.data) {
      rankingData.value = res.data.map(item => ({
        ...item,
        displayRating: parseFloat(item.avg_rating || item.rating || 0)
      }))
      // 确保DOM更新后再渲染图表
      nextTick(() => {
        initBarChart()
      })
    }
  } catch (error) {
    console.error('获取排行数据失败:', error)
  }
}

// ECharts 配置重写：暗黑科技风格
const initBarChart = () => {
  if (!barChartRef.value) return

  // 销毁旧实例防止内存泄漏或样式残留
  if (barChart) {
    barChart.dispose()
  }
  barChart = echarts.init(barChartRef.value)

  const names = rankingData.value.map(item => item.scenic_spot || item.spot_name).reverse()
  let values, valueName, startColor, endColor

  // 根据不同类型设置不同的渐变色
  if (queryParams.rankType === 'rating') {
    values = rankingData.value.map(item => parseFloat(item.avg_rating || item.rating || 0)).reverse()
    valueName = '评分'
    startColor = '#00f2fe' // 青色
    endColor = '#4facfe'   // 蓝色
  } else if (queryParams.rankType === 'visitor') {
    values = rankingData.value.map(item => parseInt(item.visitor_count || item.total_visitors || 0)).reverse()
    valueName = '游客量'
    startColor = '#f093fb' // 粉色
    endColor = '#f5576c'   // 红色
  } else {
    values = rankingData.value.map(item => parseInt(item.review_count || item.total_reviews || 0)).reverse()
    valueName = '评论数'
    startColor = '#43e97b' // 绿色
    endColor = '#38f9d7'   // 青绿
  }

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(5, 10, 31, 0.9)',
      borderColor: startColor,
      textStyle: { color: '#fff' }
    },
    grid: {
      left: '3%',
      right: '8%', // 给右侧标签留空间
      bottom: '3%',
      top: '5%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '',
      splitLine: { show: true, lineStyle: { color: 'rgba(255,255,255,0.05)', type: 'dashed' } },
      axisLabel: { color: '#8fb6e6' },
      axisLine: { show: false }
    },
    yAxis: {
      type: 'category',
      data: names,
      axisLabel: {
        color: '#fff',
        fontSize: 13,
        formatter: (value) => value.length > 8 ? value.substring(0, 8) + '...' : value
      },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      axisTick: { show: false }
    },
    series: [{
      name: valueName,
      type: 'bar',
      data: values,
      barWidth: '40%',
      itemStyle: {
        borderRadius: [0, 20, 20, 0], // 右侧圆角
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: endColor },
          { offset: 1, color: startColor }
        ]),
        shadowColor: startColor,
        shadowBlur: 10
      },
      // 背景条
      showBackground: true,
      backgroundStyle: {
        color: 'rgba(255, 255, 255, 0.03)',
        borderRadius: [0, 20, 20, 0]
      },
      label: {
        show: true,
        position: 'right',
        color: startColor,
        fontWeight: 'bold',
        fontFamily: 'sans-serif',
        formatter: '{c}'
      }
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
/* --- 变量定义 --- */
$primary: #00f2fe;
$secondary: #4facfe;
$bg-deep: #02040d;
$panel-bg: rgba(13, 27, 62, 0.65);
$border-color: rgba(0, 242, 254, 0.25);
$text-main: #fff;
$text-sub: #8fb6e6;

.ranking-container {
  min-height: 100vh; /* 保证撑满 */
  padding: 20px;
  /* 沉浸式背景 */
  background:
      radial-gradient(circle at 50% 0%, rgba(0, 242, 254, 0.1) 0%, transparent 60%),
      linear-gradient(180deg, #050a1f 0%, #02040d 100%);
  color: $text-main;
  font-family: 'Inter', sans-serif;
}

/* --- 1. 顶部控制栏 --- */
.control-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.2);
  padding: 15px 0;
  margin-bottom: 25px;
  border-radius: 4px;
  position: relative;

  /* 左右装饰线 */
  .bar-decoration-left, .bar-decoration-right {
    position: absolute;
    width: 100px;
    height: 1px;
    background: linear-gradient(90deg, transparent, $primary, transparent);
    opacity: 0.5;
  }
  .bar-decoration-left { left: 0; }
  .bar-decoration-right { right: 0; }

  .tech-form {
    :deep(.el-form-item) {
      margin-bottom: 0;
      margin-right: 40px;
    }
    :deep(.el-form-item__label) {
      color: $text-sub;
      font-weight: 500;
    }

    /* 输入框样式重写 */
    :deep(.el-select) {
      width: 180px;
      .el-input__wrapper {
        background: rgba(0, 0, 0, 0.3) !important;
        box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.15) !important;
        border-radius: 4px;
        transition: all 0.3s;

        &.is-focus {
          box-shadow: 0 0 0 1px $primary !important;
        }
      }
      .el-input__inner {
        color: #fff !important;
        font-weight: bold;
      }
    }
  }
}

/* --- 2. 面板通用样式 --- */
.tech-panel {
  background: $panel-bg;
  border: 1px solid $border-color;
  position: relative;
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  backdrop-filter: blur(10px);

  /* 装饰角标 */
  .corner {
    position: absolute;
    width: 10px;
    height: 10px;
    border: 2px solid $primary;
    transition: all 0.3s;
    opacity: 0.8;
    &.t-l { top: -1px; left: -1px; border-width: 2px 0 0 2px; }
    &.t-r { top: -1px; right: -1px; border-width: 2px 2px 0 0; }
    &.b-l { bottom: -1px; left: -1px; border-width: 0 0 2px 2px; }
    &.b-r { bottom: -1px; right: -1px; border-width: 0 2px 2px 0; }
  }

  &:hover .corner {
    width: 15px;
    height: 15px;
    box-shadow: 0 0 10px $primary;
  }

  .panel-header {
    height: 50px;
    padding: 0 20px;
    display: flex;
    align-items: center;
    background: rgba(255, 255, 255, 0.02);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);

    .icon { color: $primary; font-size: 18px; margin-right: 10px; }
    .title { color: #fff; font-size: 16px; font-weight: 600; letter-spacing: 1px; }

    .header-line {
      flex: 1;
      height: 1px;
      background: linear-gradient(90deg, rgba(255,255,255,0.1), transparent);
      margin-left: 20px;
    }
  }

  .panel-body {
    padding: 20px;
    flex: 1;
  }
}

.chart-panel {
  height: 650px; /* 固定高度 */
  .chart-container {
    width: 100%;
    height: 100%;
  }
}

.list-panel {
  height: 650px;

  .ranking-scroll-area {
    flex: 1;
    overflow-y: auto;
    padding: 10px;

    /* 滚动条 */
    &::-webkit-scrollbar { width: 4px; }
    &::-webkit-scrollbar-thumb { background: rgba(0, 242, 254, 0.2); border-radius: 2px; }
  }
}

/* --- 3. 排行榜列表项 --- */
.rank-item {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  padding: 15px 15px 15px 0;
  background: linear-gradient(90deg, rgba(255,255,255,0.02) 0%, transparent 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.02);
  cursor: pointer;
  position: relative;
  transition: all 0.3s;

  &:hover {
    background: linear-gradient(90deg, rgba(255,255,255,0.08) 0%, transparent 100%);
    transform: translateX(5px);

    .hover-glow { opacity: 1; }
  }

  .hover-glow {
    position: absolute;
    left: 0; top: 0; bottom: 0; width: 4px;
    background: $primary;
    opacity: 0;
    transition: opacity 0.3s;
    box-shadow: 0 0 10px $primary;
  }

  /* 排名数字区域 */
  .rank-num-wrapper {
    width: 60px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin-right: 10px;

    .rank-num {
      font-family: 'DIN Alternate', sans-serif;
      font-size: 18px;
      font-weight: bold;
      color: $text-sub;

      &.rank-1 { color: #f7ba2a; font-size: 24px; text-shadow: 0 0 10px rgba(247, 186, 42, 0.5); }
      &.rank-2 { color: #e0e0e0; font-size: 22px; text-shadow: 0 0 10px rgba(224, 224, 224, 0.5); }
      &.rank-3 { color: #d48806; font-size: 20px; text-shadow: 0 0 10px rgba(212, 136, 6, 0.5); }
    }

    .rank-line {
      width: 20px;
      height: 2px;
      background: currentColor;
      margin-top: 4px;
      opacity: 0.5;
    }
  }

  /* 内容区域 */
  .item-content {
    flex: 1;
    display: flex;
    justify-content: space-between;
    align-items: center;

    .item-main {
      display: flex;
      flex-direction: column;

      .spot-name {
        color: #fff;
        font-size: 15px;
        margin-bottom: 4px;
      }

      .item-tags {
        font-size: 10px;
        color: #ff4d4f;
        border: 1px solid rgba(255, 77, 79, 0.5);
        padding: 0 4px;
        width: fit-content;
        border-radius: 2px;
      }
    }

    .item-data {
      text-align: right;

      .num-font {
        font-family: 'DIN Alternate', sans-serif;
        font-size: 18px;
        font-weight: bold;
        color: $primary;
      }

      .data-unit {
        font-size: 12px;
        color: $text-sub;
        margin-left: 4px;
      }

      .tech-rate {
        :deep(.el-rate__icon) { margin-right: 0; font-size: 16px; }
        :deep(.el-rate__text) { font-family: 'DIN Alternate'; font-size: 16px; margin-left: 5px; }
      }
    }
  }
}
</style>

<style lang="scss">
/* 全局样式覆盖 - 为了让 Select 下拉菜单也符合暗黑风格 */
.tech-select-dropdown {
  background-color: rgba(5, 10, 31, 0.95) !important;
  border: 1px solid rgba(0, 242, 254, 0.3) !important;

  .el-select-dropdown__item {
    color: #a6b9d6 !important;

    &.selected {
      color: #00f2fe !important;
      background-color: rgba(0, 242, 254, 0.1);
      font-weight: bold;
    }

    &:hover {
      background-color: rgba(255, 255, 255, 0.05);
    }
  }

  .el-popper__arrow::before {
    background-color: rgba(5, 10, 31, 0.95) !important;
    border: 1px solid rgba(0, 242, 254, 0.3) !important;
  }
}
</style>