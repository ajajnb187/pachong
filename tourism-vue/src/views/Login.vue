<template>
  <div class="login-container">
    <!-- 背景动态特效层 -->
    <div class="bg-layer">
      <div class="grid-animation"></div>
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
    </div>

    <div class="login-box">
      <!-- 科技感边框装饰 -->
      <div class="tech-border t-l"></div>
      <div class="tech-border t-r"></div>
      <div class="tech-border b-l"></div>
      <div class="tech-border b-r"></div>

      <div class="login-header">
        <div class="logo-wrapper">
          <div class="logo-ring-outer"></div>
          <div class="logo-ring-inner"></div>
          <el-icon :size="32" class="main-icon"><DataAnalysis /></el-icon>
        </div>
        <div class="title-section">
          <h1 class="main-title">福州旅游大数据分析</h1>
          <p class="sub-title">福州旅游数据分析可视化平台</p>
        </div>
      </div>

      <!-- 这里的 ref 和 model 保持原样，对接原逻辑 -->
      <el-form
          :model="loginForm"
          :rules="rules"
          ref="loginFormRef"
          class="login-form custom-input"
          @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
              v-model="loginForm.username"
              placeholder="请输入管理员账号"
              size="large"
              :prefix-icon="User"
              class="tech-input"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入访问密码"
              size="large"
              :prefix-icon="Lock"
              show-password
              class="tech-input"
          />
        </el-form-item>

        <el-form-item>
          <div class="btn-wrapper">
            <el-button
                type="primary"
                size="large"
                :loading="loading"
                @click="handleLogin"
                class="login-btn"
            >
              <span class="btn-text">立即进入系统</span>
              <div class="btn-glare"></div>
            </el-button>
          </div>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <span class="system-status">System Status: Online</span>
        <span class="version">V1.0.0 Stable</span>
      </div>
    </div>
  </div>
</template>

<script setup>
// 脚本部分完全保持不变，确保您的API和逻辑正常运行
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock, DataAnalysis } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const loginFormRef = ref(null)
const loading = ref(false)
const loginForm = ref({
  username: 'admin',
  password: '123456'
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const success = await userStore.login(loginForm.value.username, loginForm.value.password)
        if (success) {
          router.push('/')
        }
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped lang="scss">
/* 定义科技主题色变量 */
$primary-color: #00f2fe;
$secondary-color: #4facfe;
$bg-deep: #050a1f;
$bg-panel: rgba(13, 27, 62, 0.75);
$border-glow: rgba(0, 242, 254, 0.3);
$text-main: #ffffff;
$text-sub: #8fb6e6;

.login-container {
  min-height: 100vh;
  width: 100vw;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: $bg-deep;
  position: relative;
  overflow: hidden;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif;
}

/* --- 背景动画层 --- */
.bg-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  /* 深蓝径向渐变背景 */
  background: radial-gradient(circle at 50% 50%, #1a2a4f 0%, #050a1f 100%);

  /* 动态网格线 */
  .grid-animation {
    position: absolute;
    width: 200%;
    height: 200%;
    top: -50%;
    left: -50%;
    background-image:
        linear-gradient(rgba(0, 242, 254, 0.1) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 242, 254, 0.1) 1px, transparent 1px);
    background-size: 50px 50px;
    transform: perspective(500px) rotateX(60deg);
    animation: gridMove 20s linear infinite;
    opacity: 0.3;
  }

  /* 漂浮的光球 */
  .orb {
    position: absolute;
    border-radius: 50%;
    filter: blur(80px);
    opacity: 0.6;
    animation: floatOrb 10s ease-in-out infinite;
  }
  .orb-1 {
    width: 300px;
    height: 300px;
    background: $primary-color;
    top: -50px;
    left: 20%;
  }
  .orb-2 {
    width: 400px;
    height: 400px;
    background: #7209b7;
    bottom: -100px;
    right: 10%;
    animation-delay: -5s;
  }
}

/* --- 登录主体框 --- */
.login-box {
  width: 460px;
  padding: 50px 40px;
  position: relative;
  z-index: 10;
  background: $bg-panel;
  /* 玻璃拟态特效 */
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 4px; /* 稍微硬一点的圆角更像科技面板 */
  box-shadow: 0 0 40px rgba(0, 0, 0, 0.4);
  animation: slideUp 0.8s cubic-bezier(0.2, 0.8, 0.2, 1);

  /* 四角发光装饰 */
  .tech-border {
    position: absolute;
    width: 20px;
    height: 20px;
    border-color: $primary-color;
    border-style: solid;
    transition: all 0.3s;

    &.t-l { top: -1px; left: -1px; border-width: 2px 0 0 2px; }
    &.t-r { top: -1px; right: -1px; border-width: 2px 2px 0 0; }
    &.b-l { bottom: -1px; left: -1px; border-width: 0 0 2px 2px; }
    &.b-r { bottom: -1px; right: -1px; border-width: 0 2px 2px 0; }
  }

  &:hover .tech-border {
    width: 30px;
    height: 30px;
    box-shadow: 0 0 15px $border-glow;
  }
}

/* --- 头部区域 --- */
.login-header {
  text-align: center;
  margin-bottom: 40px;

  .logo-wrapper {
    position: relative;
    width: 70px;
    height: 70px;
    margin: 0 auto 20px;
    display: flex;
    align-items: center;
    justify-content: center;

    .main-icon {
      color: $primary-color;
      z-index: 2;
      filter: drop-shadow(0 0 5px $primary-color);
    }

    /* 旋转光环 */
    .logo-ring-outer {
      position: absolute;
      width: 100%;
      height: 100%;
      border: 2px dashed rgba(0, 242, 254, 0.3);
      border-radius: 50%;
      animation: spin 10s linear infinite;
    }
    .logo-ring-inner {
      position: absolute;
      width: 70%;
      height: 70%;
      border: 2px solid rgba(79, 172, 254, 0.4);
      border-left-color: transparent;
      border-right-color: transparent;
      border-radius: 50%;
      animation: spin 4s linear infinite reverse;
    }
  }

  .title-section {
    .main-title {
      font-size: 28px;
      font-weight: 700;
      color: #fff;
      margin: 0;
      letter-spacing: 2px;
      background: linear-gradient(90deg, #fff, $primary-color);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .sub-title {
      margin-top: 8px;
      font-size: 13px;
      color: $text-sub;
      text-transform: uppercase;
      letter-spacing: 1px;
    }
  }
}

/* --- 表单样式覆盖 (Deep Selector) --- */
.login-form {
  :deep(.el-form-item) {
    margin-bottom: 24px;
  }

  /* 输入框重写 */
  :deep(.el-input__wrapper) {
    background-color: rgba(0, 0, 0, 0.2) !important;
    box-shadow: none !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0;
    padding: 8px 0;
    transition: all 0.3s;

    &.is-focus {
      border-bottom-color: $primary-color;
      box-shadow: 0 10px 10px -10px rgba(0, 242, 254, 0.2) !important;
    }
  }

  :deep(.el-input__inner) {
    color: #fff !important;
    height: 40px;

    &::placeholder {
      color: rgba(255, 255, 255, 0.4);
    }
  }

  :deep(.el-input__prefix-inner) {
    color: $text-sub;
    font-size: 18px;
  }

  /* 按钮重写 */
  .btn-wrapper {
    width: 100%;
    margin-top: 10px;
    position: relative;
    overflow: hidden;
    border-radius: 4px;
  }

  .login-btn {
    width: 100%;
    height: 48px;
    background: linear-gradient(90deg, $secondary-color, $primary-color);
    border: none;
    font-size: 16px;
    font-weight: 600;
    letter-spacing: 2px;
    transition: all 0.3s;
    position: relative;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 0 20px rgba(0, 242, 254, 0.4);
    }

    &:active {
      transform: translateY(0);
    }

    /* 按钮流光特效 */
    .btn-glare {
      position: absolute;
      top: 0;
      left: -100%;
      width: 50%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
      transform: skewX(-20deg);
      animation: glare 3s infinite;
    }
  }
}

/* --- 底部状态栏 --- */
.login-footer {
  margin-top: 30px;
  display: flex;
  justify-content: space-between;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  padding-top: 15px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.3);
  font-family: 'Consolas', monospace;

  .system-status {
    &::before {
      content: '';
      display: inline-block;
      width: 6px;
      height: 6px;
      background: #00ff00;
      border-radius: 50%;
      margin-right: 6px;
      box-shadow: 0 0 5px #00ff00;
    }
  }
}

/* --- 关键帧动画 --- */
@keyframes gridMove {
  0% { transform: perspective(500px) rotateX(60deg) translateY(0); }
  100% { transform: perspective(500px) rotateX(60deg) translateY(50px); }
}

@keyframes floatOrb {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(30px, -30px); }
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(40px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes glare {
  0% { left: -100%; }
  20% { left: 200%; }
  100% { left: 200%; }
}
</style>