<template>
  <div class="scenic-manage-container">
    <!-- 1. 顶部控制栏 (保持不变) -->
    <div class="control-header">
      <div class="header-left">
        <div class="title-box">
          <el-icon class="icon-pulse"><DataLine /></el-icon>
          <span class="main-title">景点数据资源池</span>
        </div>
        <div class="action-btn">
          <el-button class="tech-btn primary" @click="refreshData" :loading="loading">
            <el-icon><Refresh /></el-icon> 同步数据
          </el-button>
        </div>
      </div>

      <!-- 统计数据仪表盘 (保持不变) -->
      <div class="stats-grid">
        <div class="stat-item delay-0">
          <div class="icon-box blue"><el-icon><Location /></el-icon></div>
          <div class="info">
            <div class="value">{{ stats.totalSpots }}</div>
            <div class="label">景点总数</div>
          </div>
        </div>
        <div class="stat-item delay-1">
          <div class="icon-box green"><el-icon><ChatDotRound /></el-icon></div>
          <div class="info">
            <div class="value">{{ stats.totalReviews }}</div>
            <div class="label">评论总量</div>
          </div>
        </div>
        <div class="stat-item delay-2">
          <div class="icon-box orange"><el-icon><Star /></el-icon></div>
          <div class="info">
            <div class="value">{{ stats.avgRating }}<span class="unit">分</span></div>
            <div class="label">平均评分</div>
          </div>
        </div>
        <div class="stat-item delay-3">
          <div class="icon-box purple"><el-icon><Clock /></el-icon></div>
          <div class="info">
            <div class="value date-text">{{ stats.updateTime }}</div>
            <div class="label">最后更新</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 2. 筛选与搜索栏 (保持不变) -->
    <div class="search-bar tech-panel">
      <el-form :inline="true" :model="searchForm" class="tech-form">
        <el-form-item label="关键字检索">
          <el-input
              v-model="searchForm.keyword"
              placeholder="输入景点名称..."
              clearable
              @clear="handleSearch"
              class="tech-input"
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item label="等级筛选">
          <el-select
              v-model="searchForm.sightLevel"
              placeholder="全部等级"
              clearable
              popper-class="tech-popper"
              class="tech-select"
          >
            <el-option label="全部" value=""></el-option>
            <el-option label="5A级景区" value="5A"></el-option>
            <el-option label="4A级景区" value="4A"></el-option>
            <el-option label="3A级景区" value="3A"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button class="tech-btn primary" @click="handleSearch">
            <el-icon><Search /></el-icon> 查询
          </el-button>
          <el-button class="tech-btn ghost" @click="resetSearch">
            <el-icon><RefreshLeft /></el-icon> 重置
          </el-button>
        </el-form-item>
      </el-form>
      <div class="panel-corner top-left"></div>
      <div class="panel-corner bottom-right"></div>
    </div>

    <!-- 3. 数据表格 (保持不变) -->
    <div class="table-container tech-panel">
      <el-table
          :data="tableData"
          v-loading="loading"
          class="tech-table"
          element-loading-background="rgba(0,0,0,0.5)"
      >
        <el-table-column type="index" label="NO." width="60" align="center" />
        <el-table-column prop="scenicspot" label="景点名称" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="spot-name-cell">
              <span class="level-tag" v-if="row.sightlevel">{{ row.sightlevel }}</span>
              <span class="name-text">{{ row.scenicspot }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="zonename" label="区域" width="120" show-overflow-tooltip />
        <el-table-column prop="commentscore" label="评分" width="100" align="center">
          <template #default="{ row }">
            <span class="score-text">{{ row.commentscore }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="heatscore" label="热度" width="100" align="center">
          <template #default="{ row }">
            <div class="heat-bar">
              <div class="bar-fill" :class="getHeatClass(row.heatscore)" :style="{ width: (row.heatscore * 10) + '%' }"></div>
              <span class="heat-val">{{ row.heatscore }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="isfree" label="门票" width="100" align="center">
          <template #default="{ row }">
            <span class="status-tag" :class="row.isfree === 'True' ? 'free' : 'paid'">
              {{ row.isfree === 'True' ? '免费' : '收费' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="位置" width="100" align="center">
          <template #default="{ row }">
            <el-button link class="action-link" @click="viewLocation(row)">
              <el-icon><MapLocation /></el-icon> 定位
            </el-button>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" align="center" fixed="right">
          <template #default="{ row }">
            <div class="action-group">
              <el-tooltip content="全息档案">
                <div class="icon-btn info" @click="viewDetail(row)"><el-icon><View /></el-icon></div>
              </el-tooltip>
              <el-tooltip content="舆情评论">
                <div class="icon-btn success" @click="viewReviews(row)"><el-icon><ChatLineSquare /></el-icon></div>
              </el-tooltip>
              <el-tooltip content="详情页面" v-if="row.detailurl">
                <div class="icon-btn warning" @click="openDetailUrl(row.detailurl)"><el-icon><DataLine /></el-icon></div>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="pagination.total"
            layout="total, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
            background
        />
      </div>
    </div>

    <!-- 4. 详情弹窗 (布局重构：大图 + 详细信息) -->
    <el-dialog
        v-model="detailDialogVisible"
        title="全息数据档案"
        width="800px"
        class="tech-dialog"
        :close-on-click-modal="false"
        append-to-body
    >
      <div class="detail-layout" v-if="currentSpot">
        <!-- 顶部大图展示区 -->
        <div class="image-section">
          <div class="image-wrapper">
            <el-image
                v-if="currentSpot.coverimageurl"
                :src="currentSpot.coverimageurl"
                :preview-src-list="[currentSpot.coverimageurl]"
                :initial-index="0"
                fit="cover"
                class="big-cover-img"
                preview-teleported
            >
              <template #error>
                <div class="image-error-slot">
                  <el-icon :size="40"><Picture /></el-icon>
                  <span>暂无影像资料</span>
                </div>
              </template>
            </el-image>
            <div v-else class="no-img-placeholder">
              <el-icon :size="40"><PictureRounded /></el-icon>
              <span>暂无影像数据</span>
            </div>
            <!-- 图片遮罩提示 -->
            <div class="img-overlay" v-if="currentSpot.coverimageurl">
              <el-icon><ZoomIn /></el-icon> 点击查看高清原图
            </div>
          </div>

          <div class="spot-main-title">
            <h2>{{ currentSpot.scenicspot }}</h2>
            <div class="title-tags">
              <span class="tech-tag warning" v-if="currentSpot.sightlevel">{{ currentSpot.sightlevel }}</span>
              <span class="tech-tag primary">{{ currentSpot['s.city'] }}</span>
            </div>
          </div>
        </div>

        <!-- 底部信息网格 -->
        <div class="info-grid-container">
          <div class="grid-item">
            <span class="label">业务编码</span>
            <span class="value code-font">{{ currentSpot.businessid }}</span>
          </div>
          <div class="grid-item">
            <span class="label">所属区域</span>
            <span class="value">{{ currentSpot.zonename }}</span>
          </div>
          <div class="grid-item">
            <span class="label">门票策略</span>
            <span class="value" :class="currentSpot.isfree === 'True' ? 'text-green' : 'text-orange'">
              {{ currentSpot.isfree === 'True' ? '免费开放' : '购票入园' }}
            </span>
          </div>
          <div class="grid-item">
            <span class="label">市场参考价</span>
            <span class="value code-font">{{ currentSpot.marketprice || '待定' }}</span>
          </div>
          <div class="grid-item">
            <span class="label">用户评分</span>
            <div class="value rate-box">
              <el-rate
                  v-model="currentSpot.commentscore"
                  disabled
                  show-score
                  text-color="#f7ba2a"
                  score-template="{value}"
              />
            </div>
          </div>
          <div class="grid-item">
            <span class="label">热度指数</span>
            <span class="value heat-text">{{ currentSpot.heatscore }}</span>
          </div>
          <div class="grid-item full">
            <span class="label">地理坐标</span>
            <span class="value code-font">{{ currentSpot['s.latitude'] }}, {{ currentSpot['s.longitude'] }}</span>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 5. 评论列表弹窗 (美化版) -->
    <el-dialog
        v-model="reviewsDialogVisible"
        title="舆情评论监控"
        width="600px"
        class="tech-dialog"
        append-to-body
    >
      <div class="reviews-container">
        <div class="reviews-header">
          <span>当前展示: {{ currentSpot?.scenicspot }}</span>
          <span class="count-badge">Total: {{ currentReviews.length }}</span>
        </div>

        <el-scrollbar max-height="450px">
          <div class="reviews-list" v-if="currentReviews.length > 0">
            <div
                v-for="(review, index) in currentReviews"
                :key="index"
                class="review-card"
            >
              <div class="review-left">
                <el-avatar :size="40" :icon="UserFilled" class="user-avatar" />
              </div>
              <div class="review-right">
                <div class="review-meta">
                  <span class="username">{{ review.username || '匿名游客' }}</span>
                  <el-rate
                      v-model="review.score"
                      disabled
                      size="small"
                      class="mini-rate"
                  />
                  <span class="time">{{ review.time || '近期' }}</span>
                </div>
                <div class="review-content">
                  {{ review.content }}
                </div>
              </div>
            </div>
          </div>

          <!-- 空状态 -->
          <div class="empty-state" v-else>
            <div class="empty-icon"><el-icon><ChatLineSquare /></el-icon></div>
            <p>暂无相关评论数据</p>
          </div>
        </el-scrollbar>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh, Location, ChatDotRound, Star, Clock,
  Search, View, DataLine, RefreshLeft, MapLocation,
  ChatLineSquare, Picture, PictureRounded, ZoomIn, UserFilled
} from '@element-plus/icons-vue'
import axios from 'axios'

const loading = ref(false)
const detailDialogVisible = ref(false)
const reviewsDialogVisible = ref(false)
const currentSpot = ref(null)
const currentReviews = ref([])

const stats = reactive({
  totalSpots: 0,
  totalReviews: 0,
  avgRating: 0,
  updateTime: '-'
})

const searchForm = reactive({
  keyword: '',
  sightLevel: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const tableData = ref([])

// 获取统计数据
const getStats = async () => {
  try {
    const token = localStorage.getItem('token')
    const response = await axios.get('/api/analysis/overview', {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (response.data.code === 200) {
      const data = response.data.data
      stats.totalSpots = data.totalSpots || 0
      stats.totalReviews = data.totalReviews || 0
      stats.avgRating = data.averageRating || 0
      stats.updateTime = data.dataUpdateTime || '-'
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

const getScenicList = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('token')
    const response = await axios.get('/api/scenic-manage/list', {
      params: {
        page: pagination.page,
        pageSize: pagination.pageSize,
        keyword: searchForm.keyword,
        sightLevel: searchForm.sightLevel
      },
      headers: { Authorization: `Bearer ${token}` }
    })

    if (response.data.code === 200) {
      const result = response.data.data
      tableData.value = result.list || []
      pagination.total = result.total || 0
      console.log('获取景点列表:', tableData.value.length, '条，总数:', pagination.total)
    } else {
      ElMessage.error(response.data.msg || '获取景点列表失败')
    }
  } catch (error) {
    console.error('获取景点列表失败:', error)
    ElMessage.error('获取景点列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  getScenicList()
}

// 重置搜索
const resetSearch = () => {
  searchForm.keyword = ''
  searchForm.sightLevel = ''
  handleSearch()
}

// 分页变化
const handleSizeChange = (val) => {
  pagination.pageSize = val
  getScenicList()
}

const handlePageChange = (val) => {
  pagination.page = val
  getScenicList()
}

// 查看详情
const viewDetail = (row) => {
  currentSpot.value = row
  detailDialogVisible.value = true
}

// 查看地图 (修改为高德地图)
const viewLocation = (row) => {
  if (row['s.latitude'] && row['s.longitude']) {
    // 高德地图Web端点位展示
    // 注意：coordinate=wgs84 参数用于声明原坐标系，尝试自动纠偏（取决于高德API是否完全支持该参数透传，通常Web端搜索页更通用）
    // 为了兼容性更好，推荐直接使用 Amap Search
    window.open(`https://uri.amap.com/marker?position=${row['s.longitude']},${row['s.latitude']}&name=${row.scenicspot}&callnative=0`)
  } else {
    // 兜底策略：用名字搜
    window.open(`https://www.amap.com/search?query=${row.scenicspot}`)
  }
}

// 查看评论
const viewReviews = async (row) => {
  currentSpot.value = row
  currentReviews.value = []
  reviewsDialogVisible.value = true

  try {
    const token = localStorage.getItem('token')
    // 确保scenicspot存在且不为undefined
    const spotName = row.scenicspot || ''
    if (!spotName) {
      ElMessage.error('景点名称为空，无法查询评论')
      return
    }
    const response = await axios.get(`/api/scenic-manage/reviews/${encodeURIComponent(spotName)}`, {
      headers: { Authorization: `Bearer ${token}` }
    })

    if (response.data.code === 200) {
      const reviewData = response.data.data
      // 后端返回的是Map，包含list字段
      currentReviews.value = reviewData.list || []
      console.log('获取到评论数据:', currentReviews.value.length, '条')
    } else {
      ElMessage.error(response.data.msg || '获取评论失败')
    }
  } catch (e) {
    console.error('获取评论失败:', e)
    ElMessage.error('获取评论数据失败')
  }
}

// 打开详情链接
const openDetailUrl = (url) => {
  if (url) {
    window.open(url, '_blank')
  }
}

// 热度样式辅助
const getHeatClass = (score) => {
  if (score >= 8) return 'high'
  if (score >= 6) return 'mid'
  return 'low'
}

onMounted(() => {
  getStats()
  getScenicList()
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

.scenic-manage-container {
  min-height: 100vh;
  padding: 20px;
  background:
      radial-gradient(circle at 50% 10%, rgba(0, 242, 254, 0.05) 0%, transparent 60%),
      linear-gradient(180deg, #050a1f 0%, #02040d 100%);
  color: $text-main;
  font-family: 'Inter', sans-serif;
}

/* --- 1. 顶部控制栏 --- */
.control-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  flex-wrap: wrap;
  gap: 20px;

  .header-left {
    display: flex;
    flex-direction: column;
    gap: 15px;

    .title-box {
      display: flex;
      align-items: center;
      gap: 10px;
      .icon-pulse { color: $primary; font-size: 24px; animation: pulse 2s infinite; }
      .main-title { font-size: 24px; font-weight: bold; letter-spacing: 1px; color: #fff; text-shadow: 0 0 10px rgba(0,242,254,0.3); }
    }
  }

  .stats-grid {
    display: flex;
    gap: 20px;

    .stat-item {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.05);
      padding: 12px 20px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      gap: 15px;
      transition: all 0.3s;

      &:hover {
        background: rgba(255, 255, 255, 0.08);
        border-color: rgba(255, 255, 255, 0.1);
        transform: translateY(-2px);
      }

      .icon-box {
        width: 40px; height: 40px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 20px;
        &.blue { background: rgba(0, 242, 254, 0.1); color: $primary; }
        &.green { background: rgba(67, 233, 123, 0.1); color: #43e97b; }
        &.orange { background: rgba(247, 186, 42, 0.1); color: #f7ba2a; }
        &.purple { background: rgba(118, 75, 162, 0.1); color: #a18cd1; }
      }

      .info {
        .value { font-family: 'DIN Alternate'; font-size: 20px; font-weight: bold; color: #fff; }
        .unit { font-size: 12px; font-weight: normal; margin-left: 2px; color: $text-sub; }
        .label { font-size: 12px; color: $text-sub; }
        .date-text { font-size: 14px; }
      }
    }
  }
}

/* --- 2. 筛选栏 --- */
.search-bar {
  background: $panel-bg;
  border: 1px solid $border-color;
  padding: 20px;
  border-radius: 4px;
  position: relative;
  margin-bottom: 20px;

  .tech-form {
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    align-items: center;
    :deep(.el-form-item) { margin: 0; }
    :deep(.el-form-item__label) { color: $text-sub; }
  }

  .panel-corner {
    position: absolute;
    width: 10px; height: 10px;
    border: 2px solid $primary;
    &.top-left { top: -1px; left: -1px; border-width: 2px 0 0 2px; }
    &.bottom-right { bottom: -1px; right: -1px; border-width: 0 2px 2px 0; }
  }
}

/* --- 3. 表格区域 --- */
.table-container {
  background: $panel-bg;
  border: 1px solid rgba(255,255,255,0.05);
  padding: 20px;
  border-radius: 4px;
  min-height: 500px;
}

.tech-table {
  /* 透明化处理 */
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(0,0,0,0.2);
  --el-table-border: none;
  --el-table-row-hover-bg-color: rgba(0, 242, 254, 0.05);
  --el-table-text-color: #a6b9d6;
  --el-table-header-text-color: #fff;

  background: transparent !important;

  .spot-name-cell {
    display: flex;
    align-items: center;
    gap: 8px;
    .level-tag {
      font-size: 12px; padding: 1px 6px; border-radius: 2px;
      background: rgba(247, 186, 42, 0.15); color: #f7ba2a; border: 1px solid rgba(247, 186, 42, 0.3);
    }
    .name-text { font-weight: 500; color: #fff; }
  }

  .score-text { font-family: 'DIN Alternate'; color: #f7ba2a; font-weight: bold; font-size: 16px; }

  .heat-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    .bar-fill { height: 4px; border-radius: 2px; min-width: 10%; transition: width 0.5s; }
    .high { background: #ff4d4f; box-shadow: 0 0 5px #ff4d4f; }
    .mid { background: #f7ba2a; }
    .low { background: #4facfe; }
    .heat-val { font-size: 12px; color: #fff; }
  }

  .status-tag {
    font-size: 12px; padding: 2px 8px; border-radius: 10px;
    &.free { color: #43e97b; background: rgba(67, 233, 123, 0.1); }
    &.paid { color: $text-sub; background: rgba(255,255,255,0.1); }
  }

  .action-group {
    display: flex;
    justify-content: center;
    gap: 15px;
    .icon-btn {
      width: 28px; height: 28px; border-radius: 4px;
      display: flex; align-items: center; justify-content: center;
      cursor: pointer; transition: all 0.2s;
      &.info { background: rgba(79, 172, 254, 0.1); color: $secondary; &:hover { background: $secondary; color: #fff; } }
      &.success { background: rgba(67, 233, 123, 0.1); color: #43e97b; &:hover { background: #43e97b; color: #fff; } }
    }
  }
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  :deep(.el-pagination.is-background .el-pager li:not(.is-disabled).is-active) {
    background-color: $primary;
    color: #000;
  }
  :deep(.el-pagination.is-background .el-pager li) {
    background-color: rgba(255,255,255,0.05);
    color: #fff;
  }
}

/* --- 4. 详情弹窗样式 (重构版) --- */
.detail-layout {
  .image-section {
    position: relative;
    margin-bottom: 25px;

    .image-wrapper {
      width: 100%;
      height: 350px; /* 大图高度 */
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid rgba(0, 242, 254, 0.3);
      background: #000;
      position: relative;

      .big-cover-img {
        width: 100%; height: 100%;
        display: block;
        transition: transform 0.5s;
        &:hover { transform: scale(1.02); }
      }

      .img-overlay {
        position: absolute;
        bottom: 0; left: 0; width: 100%;
        padding: 10px;
        background: linear-gradient(to top, rgba(0,0,0,0.8), transparent);
        color: #fff;
        font-size: 12px;
        display: flex; align-items: center; justify-content: center; gap: 5px;
        opacity: 0;
        transition: opacity 0.3s;
        pointer-events: none;
      }

      &:hover .img-overlay { opacity: 1; }

      .image-error-slot, .no-img-placeholder {
        width: 100%; height: 100%;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        color: $text-sub;
        gap: 10px;
        background: radial-gradient(circle, rgba(255,255,255,0.05), transparent);
      }
    }

    .spot-main-title {
      position: absolute;
      bottom: -15px;
      left: 20px;
      background: rgba(11, 21, 49, 0.95);
      border: 1px solid $primary;
      padding: 10px 20px;
      border-radius: 4px;
      box-shadow: 0 4px 15px rgba(0,0,0,0.5);
      display: flex;
      align-items: center;
      gap: 15px;

      h2 { margin: 0; font-size: 24px; color: #fff; }
      .title-tags { display: flex; gap: 8px; }
      .tech-tag {
        font-size: 12px; padding: 2px 8px; border-radius: 2px;
        &.warning { background: rgba(247,186,42,0.15); color: #f7ba2a; border: 1px solid rgba(247,186,42,0.3); }
        &.primary { background: rgba(0,242,254,0.15); color: $primary; border: 1px solid rgba(0,242,254,0.3); }
      }
    }
  }

  .info-grid-container {
    margin-top: 30px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    padding: 20px;
    background: rgba(255,255,255,0.02);
    border-radius: 4px;

    .grid-item {
      display: flex;
      flex-direction: column;
      gap: 5px;

      &.full { grid-column: span 2; }

      .label { font-size: 12px; color: $text-sub; }
      .value { font-size: 15px; color: #fff; }
      .code-font { font-family: 'Consolas', monospace; color: $secondary; }
      .heat-text { color: #ff4d4f; font-weight: bold; }
      .text-green { color: #43e97b; }
      .text-orange { color: #e6a23c; }

      .rate-box :deep(.el-rate__text) { color: #f7ba2a !important; }
    }
  }
}

/* --- 5. 评论列表弹窗 --- */
.reviews-container {
  .reviews-header {
    display: flex; justify-content: space-between; align-items: center;
    padding-bottom: 15px;
    border-bottom: 1px dashed rgba(255,255,255,0.1);
    color: #fff;
    margin-bottom: 15px;

    .count-badge { background: rgba(0,242,254,0.1); color: $primary; padding: 2px 8px; border-radius: 10px; font-size: 12px; }
  }

  .reviews-list {
    display: flex; flex-direction: column; gap: 15px;

    .review-card {
      display: flex; gap: 15px;
      background: rgba(255,255,255,0.03);
      padding: 15px;
      border-radius: 4px;
      border: 1px solid transparent;
      transition: all 0.3s;

      &:hover { background: rgba(255,255,255,0.05); border-color: rgba(255,255,255,0.1); }

      .user-avatar { background: rgba(255,255,255,0.1); color: $text-sub; }

      .review-right {
        flex: 1;
        .review-meta {
          display: flex; align-items: center; gap: 10px; margin-bottom: 5px;
          .username { color: #fff; font-weight: bold; font-size: 14px; }
          .time { font-size: 12px; color: $text-sub; margin-left: auto; }
        }
        .review-content { color: #dcdfe6; font-size: 13px; line-height: 1.5; }
      }
    }
  }

  .empty-state {
    text-align: center; padding: 40px 0; color: $text-sub;
    .empty-icon { font-size: 48px; margin-bottom: 10px; opacity: 0.5; }
  }
}

/* 按钮通用样式 */
.tech-btn {
  background: transparent;
  border: 1px solid rgba(255,255,255,0.2);
  color: #fff;
  transition: all 0.3s;

  &.primary {
    background: rgba(0, 242, 254, 0.15); border-color: $primary; color: $primary;
    &:hover { background: $primary; color: #000; box-shadow: 0 0 15px $primary; }
  }
  &.ghost {
    &:hover { background: rgba(255,255,255,0.1); border-color: #fff; }
  }
}

/* 动画 */
@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
.delay-0 { animation-delay: 0s; }
.delay-1 { animation-delay: 0.1s; }
.delay-2 { animation-delay: 0.2s; }
.delay-3 { animation-delay: 0.3s; }
</style>

<style lang="scss">
/* 全局覆盖弹窗样式 */
.tech-dialog {
  background: rgba(11, 21, 49, 0.95) !important;
  border: 1px solid #00f2fe !important;
  box-shadow: 0 0 30px rgba(0, 242, 254, 0.15) !important;

  .el-dialog__header {
    margin-right: 0;
    border-bottom: 1px solid rgba(255,255,255,0.1);
  }
  .el-dialog__title { color: #fff !important; font-weight: bold; }
  .el-dialog__headerbtn .el-dialog__close { color: #00f2fe !important; &:hover { transform: rotate(90deg); } }
  .el-dialog__body { color: #a6b9d6 !important; padding: 20px 30px !important; }
}

/* 下拉菜单 */
.tech-popper {
  background-color: rgba(5, 10, 31, 0.95) !important;
  border: 1px solid rgba(0, 242, 254, 0.3) !important;
  .el-select-dropdown__item { color: #a6b9d6 !important; &:hover { color: #00f2fe !important; background: rgba(0, 242, 254, 0.1) !important; } }
}

/* 输入框 */
.tech-input, .tech-select {
  .el-input__wrapper {
    background: rgba(0, 0, 0, 0.3) !important;
    box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.15) !important;
    &.is-focus { box-shadow: 0 0 0 1px #00f2fe !important; }
  }
  .el-input__inner { color: #fff !important; }
}
</style>