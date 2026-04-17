<template>
  <div class="login-container" ref="loginContainer">
    <!-- 粒子效果容器 -->
    <div id="particles-js" class="particles-container"></div>
    
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="bg-circle bg-circle-1"></div>
      <div class="bg-circle bg-circle-2"></div>
      <div class="bg-circle bg-circle-3"></div>
      <div class="bg-grid"></div>
      <!-- 炫彩光效 -->
      <div class="bg-light bg-light-1"></div>
      <div class="bg-light bg-light-2"></div>
      <div class="bg-light bg-light-3"></div>
    </div>
    
    <div class="login-form-wrapper" @mousemove="handleMouseMove" ref="formWrapper">
      <div class="login-header">
        <div class="logo-container">
          <div class="logo-icon" @mouseenter="handleLogoHover" @mouseleave="handleLogoLeave">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
            <div class="logo-pulse"></div>
          </div>
          <h1 class="login-title">BEIMS</h1>
        </div>
        <p class="login-subtitle">建筑能源智能管理系统</p>
        <div class="login-subtitle-line"></div>
      </div>
      
      <el-form
        ref="loginForm"
        :model="{ username: username, password: password }"
        :rules="loginRules"
        label-position="top"
        class="login-form"
      >
        <el-form-item label="用户名" prop="username">
          <div class="input-wrapper">
            <div class="input-glow"></div>
            <el-input
              v-model="username"
              placeholder="请输入用户名"
              class="tech-input"
              @focus="handleInputFocus($event, 'username')"
              @blur="handleInputBlur($event, 'username')"
            >
              <template #prefix>
                <div class="input-icon">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                    <circle cx="12" cy="7" r="4"/>
                  </svg>
                </div>
              </template>
            </el-input>
          </div>
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <div class="input-wrapper">
            <div class="input-glow"></div>
            <el-input
              v-model="password"
              type="password"
              placeholder="请输入密码"
              class="tech-input"
              show-password
              @focus="handleInputFocus($event, 'password')"
              @blur="handleInputBlur($event, 'password')"
            >
              <template #prefix>
                <div class="input-icon">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                  </svg>
                </div>
              </template>
            </el-input>
          </div>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            class="login-button"
            @click="handleLogin"
            :loading="loading"
            @mouseenter="handleButtonHover"
            @mouseleave="handleButtonLeave"
          >
            <span class="button-text">登录</span>
            <div class="button-icon" v-if="!loading">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M5 12h14"/>
                <path d="m12 5 7 7-7 7"/>
              </svg>
            </div>
            <div class="button-glow"></div>
          </el-button>
        </el-form-item>
        
        <div class="login-footer">
          <span>还没有账号？</span>
          <el-link type="primary" @click="goToRegister" class="register-link" @mouseenter="handleLinkHover" @mouseleave="handleLinkLeave">立即注册</el-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI, setToken, setUser } from '@/api/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const loading = ref(false)
const loginContainer = ref(null)
const formWrapper = ref(null)

const username = ref('')
const password = ref('')

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'input' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'input' }
  ]
}

// 粒子效果初始化
const initParticles = () => {
  if (window.particlesJS) {
    window.particlesJS('particles-js', {
      particles: {
        number: {
          value: 100,
          density: {
            enable: true,
            value_area: 800
          }
        },
        color: {
          value: ['#00d4ff', '#00ff88', '#0066cc']
        },
        shape: {
          type: 'circle',
          stroke: {
            width: 0,
            color: '#00d4ff'
          }
        },
        opacity: {
          value: 0.5,
          random: true,
          anim: {
            enable: true,
            speed: 1,
            opacity_min: 0.1,
            sync: false
          }
        },
        size: {
          value: 3,
          random: true,
          anim: {
            enable: true,
            speed: 2,
            size_min: 0.1,
            sync: false
          }
        },
        line_linked: {
          enable: true,
          distance: 150,
          color: '#00d4ff',
          opacity: 0.4,
          width: 1
        },
        move: {
          enable: true,
          speed: 1,
          direction: 'none',
          random: true,
          straight: false,
          out_mode: 'out',
          bounce: false,
          attract: {
            enable: false,
            rotateX: 600,
            rotateY: 1200
          }
        }
      },
      interactivity: {
        detect_on: 'canvas',
        events: {
          onhover: {
            enable: true,
            mode: 'grab'
          },
          onclick: {
            enable: true,
            mode: 'push'
          },
          resize: true
        },
        modes: {
          grab: {
            distance: 140,
            line_linked: {
              opacity: 1
            }
          },
          push: {
            particles_nb: 4
          }
        }
      },
      retina_detect: true
    })
  }
}

// 鼠标移动效果（已移除3D Tilt效果）
const handleMouseMove = (event) => {
  // 3D tilt效果已禁用，保持原始状态
  if (formWrapper.value) {
    formWrapper.value.style.transform = 'none'
  }
}

// 输入框焦点效果
const handleInputFocus = (event, field) => {
  const inputWrapper = event.target.closest('.input-wrapper')
  if (inputWrapper) {
    inputWrapper.classList.add('input-focused')
  }
}

// 输入框失焦效果
const handleInputBlur = (event, field) => {
  const inputWrapper = event.target.closest('.input-wrapper')
  if (inputWrapper) {
    inputWrapper.classList.remove('input-focused')
  }
}

// Logo悬停效果
const handleLogoHover = (event) => {
  const logoIcon = event.target.closest('.logo-icon')
  if (logoIcon) {
    logoIcon.classList.add('logo-hover')
  }
}

// Logo离开效果
const handleLogoLeave = (event) => {
  const logoIcon = event.target.closest('.logo-icon')
  if (logoIcon) {
    logoIcon.classList.remove('logo-hover')
  }
}

// 按钮悬停效果
const handleButtonHover = (event) => {
  const button = event.target.closest('.login-button')
  if (button) {
    button.classList.add('button-hover')
  }
}

// 按钮离开效果
const handleButtonLeave = (event) => {
  const button = event.target.closest('.login-button')
  if (button) {
    button.classList.remove('button-hover')
  }
}

// 链接悬停效果
const handleLinkHover = (event) => {
  const link = event.target.closest('.register-link')
  if (link) {
    link.classList.add('link-hover')
  }
}

// 链接离开效果
const handleLinkLeave = (event) => {
  const link = event.target.closest('.register-link')
  if (link) {
    link.classList.remove('link-hover')
  }
}

// 登录处理
const handleLogin = async () => {
  loading.value = true
  try {
    const response = await authAPI.login(username.value, password.value)
    const { access_token, user } = response.data
    
    setToken(access_token)
    setUser(user)
    
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (error) {
    ElMessage.error('登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}

// 跳转到注册页面
const goToRegister = () => {
  router.push('/register')
}

// 生命周期钩子
onMounted(() => {
  // 加载粒子效果库
  const script = document.createElement('script')
  script.src = 'https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js'
  script.onload = initParticles
  document.head.appendChild(script)
  
  // 清理函数
  return () => {
    document.head.removeChild(script)
  }
})

onUnmounted(() => {
  // 清理粒子效果
  if (window.pJSDom) {
    window.pJSDom.forEach(pJS => {
      pJS.pJS.fn.vendors.destroypJS()
    })
  }
})
</script>

<style scoped>
.login-container {
  width: 100%;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #0a1628 0%, #1a2a4a 50%, #0d1f3c 100%);
  position: relative;
  overflow: hidden;
  z-index: 0;
}

/* 粒子效果容器 */
.particles-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 2;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  filter: blur(50px);
  opacity: 0.3;
  animation: float 6s ease-in-out infinite;
}

.bg-circle-1 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #00d4ff, #0066cc);
  top: -100px;
  left: -100px;
  animation-delay: 0s;
}

.bg-circle-2 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #00ff88, #00d4ff);
  bottom: -150px;
  right: -150px;
  animation-delay: 2s;
}

.bg-circle-3 {
  width: 200px;
  height: 200px;
  background: linear-gradient(135deg, #0066cc, #00ff88);
  top: 50%;
  right: 10%;
  transform: translateY(-50%);
  animation-delay: 4s;
}

/* 炫彩光效 */
.bg-light {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.2;
  animation: lightPulse 4s ease-in-out infinite;
}

.bg-light-1 {
  width: 500px;
  height: 500px;
  background: linear-gradient(135deg, #ff00ff, #00ffff);
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.bg-light-2 {
  width: 600px;
  height: 600px;
  background: linear-gradient(135deg, #ffff00, #ff00ff);
  bottom: 10%;
  right: 10%;
  animation-delay: 2s;
}

.bg-light-3 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #00ffff, #ffff00);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: 1s;
}

.bg-grid {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    linear-gradient(rgba(0, 212, 255, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 212, 255, 0.1) 1px, transparent 1px);
  background-size: 50px 50px;
  animation: gridMove 20s linear infinite;
}

/* 动画 */
@keyframes float {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(20px, 20px);
  }
}

@keyframes gridMove {
  0% {
    background-position: 0 0;
  }
  100% {
    background-position: 50px 50px;
  }
}

@keyframes lightPulse {
  0%, 100% {
    opacity: 0.2;
    transform: scale(1);
  }
  50% {
    opacity: 0.3;
    transform: scale(1.1);
  }
}

@keyframes glowPulse {
  0%, 100% {
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
  }
  50% {
    box-shadow: 0 0 40px rgba(0, 212, 255, 0.8), 0 0 60px rgba(0, 255, 136, 0.5);
  }
}

@keyframes buttonGlow {
  0%, 100% {
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
  }
  50% {
    box-shadow: 0 0 30px rgba(0, 212, 255, 0.8), 0 0 40px rgba(0, 255, 136, 0.6);
  }
}

@keyframes inputGlow {
  0%, 100% {
    box-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
  }
  50% {
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.6), 0 0 30px rgba(0, 255, 136, 0.4);
  }
}

@keyframes linkGlow {
  0%, 100% {
    text-shadow: 0 0 5px rgba(0, 212, 255, 0.5);
  }
  50% {
    text-shadow: 0 0 10px rgba(0, 212, 255, 0.8), 0 0 20px rgba(0, 255, 136, 0.6);
  }
}

/* 登录表单容器 */
.login-form-wrapper {
  width: 420px;
  background: rgba(10, 22, 40, 0.8);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 16px;
  padding: 50px;
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.3),
    0 0 0 1px rgba(0, 212, 255, 0.1),
    0 0 30px rgba(0, 212, 255, 0.05),
    inset 0 0 50px rgba(0, 212, 255, 0.05);
  position: relative;
  z-index: 10;
  transition: all 0.3s ease;
  overflow: hidden;
}

.login-form-wrapper::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent, rgba(0, 212, 255, 0.1), transparent);
  transform: rotate(45deg);
  animation: shine 6s linear infinite;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.login-form-wrapper:hover::before {
  opacity: 1;
}

.login-form-wrapper:hover {
  box-shadow: 
    0 25px 50px rgba(0, 0, 0, 0.4),
    0 0 0 1px rgba(0, 212, 255, 0.3),
    0 0 40px rgba(0, 212, 255, 0.2),
    0 0 60px rgba(0, 255, 136, 0.1),
    inset 0 0 60px rgba(0, 212, 255, 0.1);
  transform: translateY(-5px) scale(1.02);
}

/* 登录头部 */
.login-header {
  text-align: center;
  margin-bottom: 40px;
  position: relative;
  z-index: 1;
}

.logo-container {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  position: relative;
}

.logo-icon {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #00d4ff, #0066cc);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
  animation: logoPulse 2s ease-in-out infinite;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
}

.logo-icon::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.6s ease;
}

.logo-icon:hover::before {
  left: 100%;
}

.logo-icon:hover {
  transform: scale(1.1) rotate(5deg);
  box-shadow: 0 0 30px rgba(0, 212, 255, 0.8), 0 0 40px rgba(0, 255, 136, 0.6);
  background: linear-gradient(135deg, #00ff88, #00d4ff);
}

.logo-pulse {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  background: radial-gradient(circle, rgba(0, 212, 255, 0.5) 0%, transparent 70%);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: all 0.6s ease;
}

.logo-icon:hover .logo-pulse {
  width: 200px;
  height: 200px;
}

.logo-icon svg {
  color: white;
  z-index: 1;
  position: relative;
  transition: all 0.3s ease;
}

.logo-icon:hover svg {
  transform: scale(1.2);
}

@keyframes logoPulse {
  0%, 100% {
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
  }
  50% {
    box-shadow: 0 0 30px rgba(0, 212, 255, 0.8), 0 0 40px rgba(0, 255, 136, 0.6);
  }
}

.login-title {
  font-size: 36px;
  font-weight: bold;
  background: linear-gradient(90deg, #00d4ff, #00ff88, #00d4ff);
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  letter-spacing: 2px;
  text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
  animation: titleGlow 3s ease-in-out infinite;
}

@keyframes titleGlow {
  0% {
    background-position: 0% 50%;
    text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
  }
  50% {
    background-position: 100% 50%;
    text-shadow: 0 0 30px rgba(0, 212, 255, 0.6), 0 0 40px rgba(0, 255, 136, 0.4);
  }
  100% {
    background-position: 0% 50%;
    text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
  }
}

.login-subtitle {
  font-size: 16px;
  color: #8ec6e3;
  margin: 10px 0 20px 0;
  letter-spacing: 1px;
  text-shadow: 0 0 10px rgba(0, 212, 255, 0.2);
}

.login-subtitle-line {
  width: 80px;
  height: 2px;
  background: linear-gradient(90deg, #00d4ff, #00ff88, transparent);
  margin: 0 auto;
  border-radius: 1px;
  animation: lineGlow 2s ease-in-out infinite;
}

@keyframes lineGlow {
  0%, 100% {
    box-shadow: 0 0 5px rgba(0, 212, 255, 0.3);
  }
  50% {
    box-shadow: 0 0 15px rgba(0, 212, 255, 0.6), 0 0 20px rgba(0, 255, 136, 0.4);
  }
}

/* 表单样式 */
.login-form {
  width: 100%;
  position: relative;
  z-index: 1;
}

.input-wrapper {
  position: relative;
  margin-bottom: 25px;
  transition: all 0.3s ease;
}

.input-wrapper::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  background: radial-gradient(circle, rgba(0, 212, 255, 0.1) 0%, transparent 70%);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: all 0.6s ease;
  z-index: -1;
}

.input-wrapper.input-focused::before {
  width: 300px;
  height: 300px;
}

.input-glow {
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(45deg, #00d4ff, #00ff88, #00d4ff, #00ff88);
  background-size: 400% 400%;
  border-radius: 10px;
  z-index: -1;
  opacity: 0;
  transition: all 0.3s ease;
  animation: gradientShift 3s ease infinite;
}

.input-wrapper.input-focused .input-glow {
  opacity: 1;
  animation: gradientShift 3s ease infinite, inputGlow 2s ease-in-out infinite;
}

@keyframes gradientShift {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

.tech-input {
  background: rgba(10, 22, 40, 0.8);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 8px;
  color: #ffffff;
  height: 48px;
  font-size: 16px;
  transition: all 0.3s ease;
  position: relative;
  z-index: 1;
  backdrop-filter: blur(10px);
}

.tech-input:focus {
  border-color: #00d4ff;
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.3), inset 0 0 10px rgba(0, 212, 255, 0.1);
  background: rgba(10, 22, 40, 0.9);
  transform: translateY(-2px);
}

.tech-input::placeholder {
  color: rgba(142, 198, 227, 0.6);
  transition: all 0.3s ease;
}

.tech-input:focus::placeholder {
  color: rgba(142, 198, 227, 0.8);
  transform: translateX(5px);
}

.input-icon {
  color: #00d4ff;
  transition: all 0.3s ease;
  position: relative;
  z-index: 1;
}

.tech-input:focus .input-icon {
  color: #00ff88;
  transform: scale(1.1) rotate(5deg);
  animation: iconPulse 1s ease-in-out;
}

@keyframes iconPulse {
  0%, 100% {
    transform: scale(1) rotate(0deg);
  }
  50% {
    transform: scale(1.2) rotate(10deg);
  }
}

/* 登录按钮 */
.login-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: bold;
  background: linear-gradient(135deg, #0066cc, #00d4ff);
  border: none;
  border-radius: 8px;
  color: white;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  position: relative;
  overflow: hidden;
  cursor: pointer;
  z-index: 1;
}

.login-button::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transform: rotate(45deg);
  animation: shine 3s linear infinite;
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: -1;
}

.login-button:hover::before {
  opacity: 1;
}

.login-button::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #00d4ff, #00ff88, #00d4ff);
  background-size: 300% 300%;
  border-radius: 8px;
  opacity: 0;
  transition: opacity 0.3s ease;
  animation: gradientShift 3s ease infinite;
  z-index: -1;
}

.login-button:hover::after {
  opacity: 1;
}

.login-button:hover {
  box-shadow: 0 0 30px rgba(0, 212, 255, 0.6), 0 0 40px rgba(0, 255, 136, 0.4);
  transform: translateY(-2px) scale(1.02);
  animation: buttonGlow 2s ease-in-out infinite;
}

.button-glow {
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(45deg, #00d4ff, #00ff88, #00d4ff, #00ff88);
  background-size: 400% 400%;
  border-radius: 10px;
  z-index: -2;
  opacity: 0;
  transition: all 0.3s ease;
  animation: gradientShift 3s ease infinite;
}

.login-button:hover .button-glow {
  opacity: 1;
  animation: gradientShift 3s ease infinite, buttonGlow 2s ease-in-out infinite;
}

.button-text {
  position: relative;
  z-index: 1;
  transition: all 0.3s ease;
}

.login-button:hover .button-text {
  transform: translateY(-2px);
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
}

.button-icon {
  position: relative;
  z-index: 1;
  transition: all 0.3s ease;
}

.login-button:hover .button-icon {
  transform: translateX(8px) scale(1.2);
  animation: iconPulse 1s ease-in-out;
}

@keyframes shine {
  0% {
    transform: translateX(-100%) rotate(45deg);
  }
  100% {
    transform: translateX(100%) rotate(45deg);
  }
}

/* 登录底部 */
.login-footer {
  text-align: center;
  margin-top: 30px;
  color: #8ec6e3;
  font-size: 14px;
  position: relative;
  z-index: 1;
  text-shadow: 0 0 5px rgba(0, 212, 255, 0.2);
}

.login-footer span {
  margin-right: 5px;
  transition: all 0.3s ease;
}

.login-footer:hover span {
  color: #00d4ff;
  text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
}

.register-link {
  color: #00d4ff !important;
  transition: all 0.3s ease;
  position: relative;
  text-shadow: 0 0 5px rgba(0, 212, 255, 0.3);
  cursor: pointer;
}

.register-link:hover {
  color: #00ff88 !important;
  animation: linkGlow 2s ease-in-out infinite;
  transform: translateY(-2px);
}

.register-link::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 0;
  height: 2px;
  background: linear-gradient(90deg, #00d4ff, #00ff88, #00d4ff);
  background-size: 200% auto;
  transition: width 0.3s ease, background-position 0.6s ease;
  animation: gradientShift 3s ease infinite;
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
}

.register-link:hover::after {
  width: 100%;
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.8), 0 0 30px rgba(0, 255, 136, 0.6);
}

.register-link.link-hover {
  color: #00ff88 !important;
  animation: linkGlow 2s ease-in-out infinite;
}

.register-link.link-hover::after {
  width: 100%;
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.8), 0 0 30px rgba(0, 255, 136, 0.6);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-form-wrapper {
    width: 90%;
    padding: 40px 30px;
  }
  
  .login-title {
    font-size: 30px;
  }
  
  .bg-circle-1 {
    width: 200px;
    height: 200px;
  }
  
  .bg-circle-2 {
    width: 300px;
    height: 300px;
  }
  
  .bg-circle-3 {
    width: 150px;
    height: 150px;
  }
}

/* 加载动画 */
.el-button--loading .el-icon-loading {
  color: white !important;
}

/* 表单验证提示 */
.el-form-item__error {
  color: #ff6b6b !important;
  font-size: 12px !important;
  margin-top: 5px !important;
}

/* 密码显示/隐藏按钮 */
.el-input__suffix-inner .el-icon {
  color: rgba(142, 198, 227, 0.6) !important;
  transition: all 0.3s ease;
}

.el-input__suffix-inner .el-icon:hover {
  color: #00d4ff !important;
}
</style>
