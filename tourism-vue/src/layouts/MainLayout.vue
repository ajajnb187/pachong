<template>
  <!-- 背景层：福州山水科技风（深蓝+榕城绿光晕） -->
  <div class="data-platform-container">
    <div class="bg-animation">
      <!-- 动态星空 -->
      <div class="stars"></div>
      <div class="stars2"></div>
      <!-- 底部赛博网格 -->
      <div class="cyber-grid"></div>
      <!-- 顶部极光流光 (模拟福州闽江水韵) -->
      <div class="aurora-glow"></div>
    </div>

    <el-container class="main-layout">
      <!-- 侧边栏：磨砂玻璃 + 科技边框 -->
      <el-aside :width="isCollapse ? '70px' : '230px'" class="sidebar glass-effect">
        <div class="logo-box" :class="{ collapse: isCollapse }">
          <div class="logo-icon-wrapper">
            <!-- 替换为代表数据的雷达图标，并增加旋转动画 -->
            <el-icon :size="24" class="logo-icon"><DataAnalysis /></el-icon>
            <div class="icon-glow"></div>
          </div>
          <transition name="fade-slide">
            <div v-if="!isCollapse" class="logo-text">
              <span class="main-title">福州智旅云图</span>
              <span class="sub-title">FUZHOU TOURISM BRAIN</span>
            </div>
          </transition>
        </div>

        <!-- 菜单区域 -->
        <el-scrollbar class="menu-scrollbar">
          <el-menu
              :default-active="activeMenu"
              :collapse="isCollapse"
              :collapse-transition="false"
              router
              unique-opened
              class="sidebar-menu"
          >
            <el-menu-item
                v-for="item in menuRoutes"
                :key="item.path"
                :index="item.path"
            >
              <el-icon><component :is="item.meta.icon" /></el-icon>
              <template #title>
                <span>{{ item.meta.title }}</span>
                <!-- 激活时光效条 -->
                <div class="active-light-bar" v-if="activeMenu === item.path"></div>
              </template>
            </el-menu-item>
          </el-menu>
        </el-scrollbar>
      </el-aside>

      <el-container class="content-container">
        <!-- 头部：悬浮全息面板 -->
        <el-header class="header">
          <div class="header-inner glass-effect">
            <div class="header-left">
              <div class="collapse-btn" @click="toggleCollapse">
                <el-icon :size="20">
                  <component :is="isCollapse ? 'Expand' : 'Fold'" />
                </el-icon>
              </div>

              <el-breadcrumb separator="/" class="tech-breadcrumb">
                <el-breadcrumb-item>全域态势感知</el-breadcrumb-item>
                <el-breadcrumb-item class="active-crumb">{{ currentTitle }}</el-breadcrumb-item>
              </el-breadcrumb>
            </div>

            <!-- 头部中间：数字时钟 -->
            <div class="header-center">
              <div class="digital-clock">
                <span class="date">{{ currentDate }}</span>
                <span class="divider">|</span>
                <span class="time">{{ currentTime }}</span>
              </div>
            </div>

            <div class="header-right">
              <el-dropdown @command="handleCommand" trigger="click" popper-class="tech-dropdown">
                <div class="user-info">
                  <!-- 固定的友好头像 + 在线状态点 -->
                  <div class="avatar-wrapper">
                    <el-avatar :size="36" :src="defaultAvatar" class="user-avatar" />
                    <span class="status-dot"></span>
                  </div>
                  <span class="username">{{ userStore.userInfo?.username || '管理员' }}</span>
                  <el-icon class="el-icon--right"><CaretBottom /></el-icon>
                </div>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="profile"><el-icon><User /></el-icon> 账号信息</el-dropdown-item>
                    <el-dropdown-item command="logout" divided><el-icon><SwitchButton /></el-icon> 安全退出</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </el-header>

        <!-- 主内容区 -->
        <el-main class="main-content">
          <router-view v-slot="{ Component }">
            <transition name="zoom-fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  UserFilled, Expand, Fold, DataAnalysis, CaretBottom,
  User, Setting, SwitchButton
} from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isCollapse = ref(false)
const currentTime = ref('')
const currentDate = ref('')

// 使用本地头像，避免外部URL加载失败
const defaultAvatar = ref('data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Ccircle cx="50" cy="50" r="50" fill="%2300f2fe"/%3E%3Ctext x="50" y="65" font-size="48" text-anchor="middle" fill="white" font-weight="bold"%3E管%3C/text%3E%3C/svg%3E')

// 菜单路由逻辑 (排除 Login)
const menuRoutes = computed(() => {
  const mainRoute = router.options.routes.find(r => r.path === '/')
  if (!mainRoute || !mainRoute.children) return []
  return mainRoute.children
      .filter(item => !item.meta?.hidden && item.meta?.title)
      .map(item => ({
        ...item,
        path: item.path.startsWith('/') ? item.path : `/${item.path}`
      }))
})

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => route.meta?.title || '首页')

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

// 时间更新
let timer = null
const updateTime = () => {
  const now = new Date()
  const weeks = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  currentTime.value = now.toLocaleTimeString('zh-CN', { hour12: false })
  currentDate.value = `${now.getFullYear()}/${(now.getMonth()+1).toString().padStart(2,'0')}/${now.getDate().toString().padStart(2,'0')} ${weeks[now.getDay()]}`
}

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if(timer) clearInterval(timer)
})

const handleCommand = (command) => {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'logout') {
    ElMessageBox.confirm('即将断开与福州旅游数据中心的连接，是否确认？', '系统警告', {
      confirmButtonText: '立即断开',
      cancelButtonText: '取消',
      type: 'warning',
      customClass: 'tech-message-box'
    }).then(async () => {
      await userStore.logout()
      router.push('/login')
    }).catch(() => {})
  }
}
</script>

<style lang="scss">
/* --- 全局变量：福州印象科技色系 --- */
:root {
  --tech-bg-deep: #050a15;       /* 深空底色 */
  --tech-primary: #00f2fe;       /* 数据青 (主色) */
  --tech-secondary: #00dbde;     /* 海洋蓝 (辅色) */
  --tech-accent: #11998e;        /* 榕城绿 (强调色) */
  --tech-text-main: #ffffff;
  --tech-text-sub: #94a9c9;
  --glass-bg: rgba(16, 30, 56, 0.75);
  --glass-border: rgba(0, 242, 254, 0.25);
  --sidebar-width: 230px;
}

body {
  margin: 0;
  background-color: var(--tech-bg-deep);
  font-family: 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
  overflow: hidden;
}

/* 覆盖 Element Plus 全局弹窗 */
.tech-message-box {
  background: rgba(12, 25, 48, 0.95) !important;
  border: 1px solid var(--tech-primary) !important;
  box-shadow: 0 0 40px rgba(0, 242, 254, 0.15) !important;
  backdrop-filter: blur(10px);

  .el-message-box__title { color: #fff !important; font-weight: bold; }
  .el-message-box__content { color: var(--tech-text-sub) !important; }

  .el-button--primary {
    background: linear-gradient(90deg, var(--tech-accent), var(--tech-primary)) !important;
    border: none !important;
    &:hover { box-shadow: 0 0 15px var(--tech-primary); }
  }
}

/* 覆盖 Dropdown 样式 */
.tech-dropdown {
  background: rgba(12, 25, 48, 0.95) !important;
  border: 1px solid var(--glass-border) !important;

  .el-dropdown-menu__item {
    color: var(--tech-text-sub) !important;
    &:hover {
      background: rgba(0, 242, 254, 0.1) !important;
      color: var(--tech-primary) !important;
    }
  }
  .el-dropdown-menu__item--divided {
    border-top-color: rgba(255, 255, 255, 0.1) !important;
  }
}
</style>

<style scoped lang="scss">
.data-platform-container {
  height: 100vh;
  width: 100vw;
  position: relative;
  /* 基础背景：深邃的蓝黑渐变 */
  background: radial-gradient(ellipse at bottom, #0d1b2a 0%, #000000 100%);
  color: var(--tech-text-main);
  overflow: hidden;
}

/* --- 背景动效层 --- */
.bg-animation {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  z-index: 0;
  pointer-events: none;

  /* 顶部极光流光 */
  .aurora-glow {
    position: absolute;
    top: -20%; left: 0; width: 100%; height: 50%;
    background: radial-gradient(circle at 50% 50%, rgba(0, 242, 254, 0.1), transparent 70%);
    filter: blur(60px);
    animation: aurora 10s infinite alternate;
  }

  /* 粒子星星 */
  .stars {
    width: 2px; height: 2px;
    background: transparent;
    box-shadow: 10px 10px #FFF, 50px 80px #FFF, 120px 200px #FFF, 300px 100px #FFF, 450px 300px #FFF;
    animation: starMove 100s linear infinite;
    opacity: 0.4;
  }

  /* 底部赛博网格 */
  .cyber-grid {
    position: absolute;
    width: 200%; height: 100%;
    bottom: -50%; left: -50%;
    background-image:
        linear-gradient(rgba(0, 242, 254, 0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 242, 254, 0.05) 1px, transparent 1px);
    background-size: 50px 50px;
    transform: perspective(500px) rotateX(60deg);
    mask-image: linear-gradient(to top, rgba(0,0,0,1) 0%, transparent 50%);
    animation: gridFlow 20s linear infinite;
  }
}

.main-layout {
  position: relative;
  z-index: 10;
  height: 100%;
}

/* --- 侧边栏 --- */
.sidebar {
  background: linear-gradient(180deg, rgba(13, 27, 46, 0.9) 0%, rgba(5, 10, 20, 0.95) 100%);
  border-right: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 5px 0 20px rgba(0, 0, 0, 0.5);

  .logo-box {
    height: 70px;
    display: flex;
    align-items: center;
    padding-left: 24px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    background: rgba(0, 0, 0, 0.2);
    overflow: hidden;

    .logo-icon-wrapper {
      width: 40px; height: 40px;
      position: relative;
      display: flex; align-items: center; justify-content: center;

      .logo-icon {
        color: var(--tech-primary);
        z-index: 2;
        filter: drop-shadow(0 0 5px var(--tech-primary));
      }

      /* 图标背后的光圈 */
      .icon-glow {
        position: absolute;
        width: 100%; height: 100%;
        border: 2px dashed rgba(0, 242, 254, 0.3);
        border-radius: 50%;
        animation: rotate 10s linear infinite;
      }
    }

    .logo-text {
      margin-left: 12px;
      display: flex;
      flex-direction: column;

      .main-title {
        font-size: 16px;
        font-weight: 800;
        background: linear-gradient(90deg, #fff, var(--tech-primary));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 1px;
      }
      .sub-title {
        font-size: 9px;
        color: #5c7c9e;
        letter-spacing: 1px;
        margin-top: 2px;
      }
    }

    &.collapse {
      padding-left: 0;
      justify-content: center;
    }
  }

  .sidebar-menu {
    border: none;
    background: transparent;
    padding: 10px;

    :deep(.el-menu-item) {
      height: 54px;
      line-height: 54px;
      margin-bottom: 5px;
      border-radius: 8px;
      color: var(--tech-text-sub);
      border: 1px solid transparent;

      &:hover {
        background: rgba(0, 242, 254, 0.05);
        color: #fff;
        transform: translateX(3px);
        transition: all 0.3s;
      }

      &.is-active {
        background: linear-gradient(90deg, rgba(0, 242, 254, 0.15), transparent);
        color: var(--tech-primary);
        font-weight: bold;
        border-color: rgba(0, 242, 254, 0.2);

        .el-icon { color: var(--tech-primary); filter: drop-shadow(0 0 8px var(--tech-primary)); }

        .active-light-bar {
          position: absolute;
          left: 0; top: 15%; height: 70%; width: 3px;
          background: var(--tech-primary);
          box-shadow: 0 0 10px var(--tech-primary);
          border-radius: 2px;
        }
      }
    }
  }
}

/* --- 头部 --- */
.header {
  height: 64px;
  padding: 0 20px;
  margin-top: 15px; /* 悬浮感 */
}

.header-inner {
  height: 100%;
  background: rgba(13, 27, 46, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);

  .header-left {
    display: flex;
    align-items: center;
    gap: 25px;

    .collapse-btn {
      color: var(--tech-text-sub);
      cursor: pointer;
      transition: all 0.3s;
      &:hover { color: var(--tech-primary); transform: scale(1.1); }
    }

    .tech-breadcrumb {
      :deep(.el-breadcrumb__inner) { color: #5c7c9e; font-weight: normal; }
      .active-crumb :deep(.el-breadcrumb__inner) {
        color: #fff;
        text-shadow: 0 0 5px rgba(0, 242, 254, 0.3);
      }
    }
  }

  .header-center {
    .digital-clock {
      font-family: 'DIN Alternate', monospace;
      color: #fff;
      font-size: 16px;
      letter-spacing: 1px;
      display: flex;
      gap: 10px;
      padding: 6px 20px;
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 20px;
      box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.5);

      .time { color: var(--tech-primary); font-weight: bold; }
      .divider { color: #555; }
    }
  }

  .header-right {
    .user-info {
      display: flex;
      align-items: center;
      gap: 12px;
      cursor: pointer;
      padding: 4px 8px;
      border-radius: 6px;
      transition: background 0.3s;

      &:hover { background: rgba(255, 255, 255, 0.05); }

      .avatar-wrapper {
        position: relative;
        .user-avatar {
          border: 2px solid var(--tech-primary);
          background: #fff;
          padding: 2px;
        }
        .status-dot {
          position: absolute;
          bottom: 0; right: 0;
          width: 8px; height: 8px;
          background: #00ff00;
          border-radius: 50%;
          border: 2px solid #0d1b2a;
          box-shadow: 0 0 5px #00ff00;
        }
      }

      .username {
        font-size: 14px;
        color: #fff;
        font-weight: 500;
      }
    }
  }
}

/* --- 内容区 --- */
.main-content {
  padding: 20px 24px;
  overflow-x: hidden;
}

/* 动画定义 */
@keyframes gridFlow {
  0% { transform: perspective(500px) rotateX(60deg) translateY(0); }
  100% { transform: perspective(500px) rotateX(60deg) translateY(50px); }
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes aurora {
  0% { opacity: 0.3; transform: scale(1); }
  100% { opacity: 0.6; transform: scale(1.1); }
}

/* 页面切换动画 */
.zoom-fade-enter-active {
  transition: all 0.4s ease-out;
}
.zoom-fade-leave-active {
  transition: all 0.3s cubic-bezier(1, 0.5, 0.8, 1);
}
.zoom-fade-enter-from {
  transform: translateY(20px) scale(0.98);
  opacity: 0;
}
.zoom-fade-leave-to {
  transform: translateY(-20px);
  opacity: 0;
}

.fade-slide-enter-active, .fade-slide-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}
.fade-slide-enter-from, .fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}
</style>