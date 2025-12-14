<template>
  <div class="profile-container">
    <el-card class="profile-card glass-effect">
      <template #header>
        <div class="card-header">
          <el-icon :size="24" class="header-icon"><User /></el-icon>
          <span>账号信息</span>
        </div>
      </template>

      <el-form
          ref="formRef"
          :model="formData"
          :rules="rules"
          label-width="100px"
          class="profile-form"
      >
        <el-form-item label="用户名">
          <el-input v-model="userInfo.username" disabled>
            <template #prefix>
              <el-icon><UserFilled /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="真实姓名" prop="realName">
          <el-input v-model="formData.realName" placeholder="请输入真实姓名">
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model="formData.email" placeholder="请输入邮箱">
            <template #prefix>
              <el-icon><Message /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="手机号" prop="phone">
          <el-input v-model="formData.phone" placeholder="请输入手机号">
            <template #prefix>
              <el-icon><Phone /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-divider>
          <el-icon><Lock /></el-icon>
          修改密码（选填）
        </el-divider>

        <el-form-item label="新密码" prop="newPassword">
          <el-input
              v-model="formData.newPassword"
              type="password"
              placeholder="不修改请留空"
              show-password
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
              v-model="formData.confirmPassword"
              type="password"
              placeholder="请再次输入新密码"
              show-password
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSubmit">
            <el-icon><CircleCheck /></el-icon>
            保存修改
          </el-button>
          <el-button @click="handleReset">
            <el-icon><RefreshLeft /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  User, UserFilled, Message, Phone, Lock,
  CircleCheck, RefreshLeft
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { getUserInfoAPI, updateUserInfoAPI } from '@/api/auth'

const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)

const userInfo = reactive({
  username: '',
  realName: '',
  email: '',
  phone: ''
})

const formData = reactive({
  realName: '',
  email: '',
  phone: '',
  newPassword: '',
  confirmPassword: ''
})

const validatePassword = (rule, value, callback) => {
  if (formData.newPassword && !value) {
    callback(new Error('请确认新密码'))
  } else if (value && value !== formData.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  email: [
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  confirmPassword: [
    { validator: validatePassword, trigger: 'blur' }
  ]
}

const fetchUserInfo = async () => {
  try {
    const res = await getUserInfoAPI()
    if (res.code === 200) {
      Object.assign(userInfo, res.data)
      formData.realName = res.data.realName || ''
      formData.email = res.data.email || ''
      formData.phone = res.data.phone || ''
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const updateData = {
          realName: formData.realName,
          email: formData.email,
          phone: formData.phone
        }

        if (formData.newPassword) {
          updateData.password = formData.newPassword
        }

        const res = await updateUserInfoAPI(updateData)
        if (res.code === 200) {
          ElMessage.success('信息更新成功')
          await userStore.getUserInfo()
          formData.newPassword = ''
          formData.confirmPassword = ''
        }
      } catch (error) {
        ElMessage.error(error.message || '更新失败')
      } finally {
        loading.value = false
      }
    }
  })
}

const handleReset = () => {
  formData.realName = userInfo.realName
  formData.email = userInfo.email
  formData.phone = userInfo.phone
  formData.newPassword = ''
  formData.confirmPassword = ''
  formRef.value?.clearValidate()
}

onMounted(() => {
  fetchUserInfo()
})
</script>

<style scoped lang="scss">
.profile-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;

  .profile-card {
    background: rgba(13, 27, 46, 0.8);
    border: 1px solid rgba(0, 242, 254, 0.2);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(10px);

    :deep(.el-card__header) {
      background: rgba(0, 0, 0, 0.3);
      border-bottom: 1px solid rgba(0, 242, 254, 0.2);
      padding: 18px 20px;

      .card-header {
        display: flex;
        align-items: center;
        gap: 10px;
        color: #fff;
        font-size: 18px;
        font-weight: bold;

        .header-icon {
          color: var(--tech-primary);
          filter: drop-shadow(0 0 5px var(--tech-primary));
        }
      }
    }

    :deep(.el-card__body) {
      padding: 30px;
    }
  }

  .profile-form {
    :deep(.el-form-item__label) {
      color: var(--tech-text-sub);
      font-weight: 500;
    }

    :deep(.el-input) {
      .el-input__wrapper {
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: none;

        &:hover {
          border-color: rgba(0, 242, 254, 0.3);
        }

        &.is-focus {
          border-color: var(--tech-primary);
          box-shadow: 0 0 10px rgba(0, 242, 254, 0.2);
        }
      }

      .el-input__inner {
        color: #fff;

        &::placeholder {
          color: rgba(255, 255, 255, 0.3);
        }

        &:disabled {
          color: rgba(255, 255, 255, 0.5);
        }
      }

      .el-input__prefix {
        color: var(--tech-text-sub);
      }
    }

    :deep(.el-divider) {
      margin: 30px 0;
      border-color: rgba(255, 255, 255, 0.1);

      .el-divider__text {
        background: transparent;
        color: var(--tech-text-sub);
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 8px;
      }
    }

    :deep(.el-button) {
      &.el-button--primary {
        background: linear-gradient(90deg, var(--tech-accent), var(--tech-primary));
        border: none;
        font-weight: 500;

        &:hover {
          box-shadow: 0 0 15px rgba(0, 242, 254, 0.4);
          transform: translateY(-2px);
        }
      }

      &:not(.el-button--primary) {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: #fff;

        &:hover {
          background: rgba(255, 255, 255, 0.15);
          border-color: rgba(0, 242, 254, 0.3);
        }
      }
    }
  }
}

:root {
  --tech-primary: #00f2fe;
  --tech-accent: #11998e;
  --tech-text-sub: #94a9c9;
}
</style>
