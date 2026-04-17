<template>
  <div class="register-container">
    <div class="register-form-wrapper">
      <div class="register-header">
        <h1 class="register-title">BEIMS</h1>
        <p class="register-subtitle">建筑能源智能管理系统</p>
      </div>
      
      <el-form
        ref="registerForm"
        :model="registerForm"
        :rules="registerRules"
        label-position="top"
        class="register-form"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="请输入用户名"
            prefix-icon="User"
          />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="registerForm.email"
            placeholder="请输入邮箱"
            prefix-icon="Message"
          />
        </el-form-item>
        
        <el-form-item label="姓名" prop="full_name">
          <el-input
            v-model="registerForm.full_name"
            placeholder="请输入姓名"
            prefix-icon="Avatar"
          />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input
            v-model="registerForm.confirm_password"
            type="password"
            placeholder="请再次输入密码"
            prefix-icon="Check"
            show-password
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            class="register-button"
            @click="handleRegister"
            :loading="loading"
          >
            注册
          </el-button>
        </el-form-item>
        
        <div class="register-footer">
          <span>已有账号？</span>
          <el-link type="primary" @click="goToLogin">立即登录</el-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI } from '@/api/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const loading = ref(false)

const registerForm = reactive({
  username: '',
  email: '',
  full_name: '',
  password: '',
  confirm_password: ''
})

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在3到20个字符之间', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  full_name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const handleRegister = async () => {
  loading.value = true
  try {
    const response = await authAPI.register({
      username: registerForm.username,
      email: registerForm.email,
      full_name: registerForm.full_name,
      password: registerForm.password,
      role: 'user'
    })
    
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (error) {
    ElMessage.error('注册失败，请检查输入信息')
  } finally {
    loading.value = false
  }
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.register-container {
  width: 100%;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #0a1628 0%, #1a2a4a 50%, #0d1f3c 100%);
}

.register-form-wrapper {
  width: 450px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.register-header {
  text-align: center;
  margin-bottom: 30px;
}

.register-title {
  font-size: 32px;
  font-weight: bold;
  background: linear-gradient(90deg, #00d4ff, #00ff88);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 10px 0;
  letter-spacing: 2px;
}

.register-subtitle {
  font-size: 14px;
  color: #8ec6e3;
  margin: 0;
}

.register-form {
  width: 100%;
}

.register-button {
  width: 100%;
  height: 40px;
  font-size: 16px;
  font-weight: bold;
  background: linear-gradient(135deg, #0066cc, #00d4ff);
  border: none;
  transition: all 0.3s;
}

.register-button:hover {
  background: linear-gradient(135deg, #0080ff, #00e6ff);
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
}

.register-footer {
  text-align: center;
  margin-top: 20px;
  color: #8ec6e3;
  font-size: 14px;
}

.register-footer span {
  margin-right: 5px;
}

.register-footer .el-link {
  color: #00d4ff;
}

.register-footer .el-link:hover {
  color: #00ff88;
}
</style>
