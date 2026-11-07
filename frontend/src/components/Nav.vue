<template>
  <nav class="navbar">
    <!-- 點擊左側 Logo 或標題：若為管理員/專家回首頁，若為會員/訪客則回 Dr. Manhattan -->
    <div class="nav-left" @click="goHome">
      <img src="/dr-manhattan-logo.png" alt="Logo" class="logo-img" />
      <h1 class="product-title">
        {{ t('KCC ToxProfiler 致癌物關鍵特徵歸納平臺', 'KCC ToxProfiler Carcinogen Hazard Platform') }}
      </h1>
    </div>
    
    <!-- 右側導覽列：依據 RBAC 四角色與當前語言動態呈現 -->
    <div class="nav-right">
      <!-- 1. 頁面跳轉群組 -->
      <div class="nav-page-group">
        <!-- 僅『系統管理者』與『專家』開放：危害辨識 & 歷史紀錄 -->
        <button 
          v-if="canAccessHazardAndHistory"
          class="nav-page-btn" 
          :class="{ active: isHazardFlowActive }"
          @click="router.push('/')"
        >
          {{ t('危害辨識', 'Hazard ID') }}
        </button>

        <button 
          v-if="canAccessHazardAndHistory"
          class="nav-page-btn" 
          :class="{ active: route.path.startsWith('/history') }"
          @click="router.push('/history')"
        >
          {{ t('歷史紀錄', 'History') }}
        </button>

        <!-- 四種角色皆開放：Dr. Manhattan 智能助理 -->
        <button 
          class="nav-page-btn" 
          :class="{ active: route.path.startsWith('/chat') }"
          @click="router.push('/chat')"
        >
          Dr. Manhattan
        </button>

        <!-- 僅『系統管理者』開放：帳號管理 -->
        <button 
          v-if="isAdmin"
          class="nav-page-btn" 
          :class="{ active: route.path.startsWith('/account') }"
          @click="router.push('/account')"
        >
          {{ t('帳號管理', 'Accounts') }}
        </button>
      </div>

      <!-- 視覺分隔線 -->
      <span class="nav-divider"></span>

      <!-- 2. 系統功能群組：目前角色徽章 + 登入/登出 + 中英切換 -->
      <div class="nav-utility-group">
        <!-- 顯示當前登入者名稱與角色 -->
        <span v-if="authState.user" class="role-status-pill" :class="getRoleBadgeClass(authState.user.role)">
          {{ displayUserName }} ({{ translateRole(authState.user.role) }})
        </span>

        <button 
          v-if="!authState.isAuthenticated" 
          class="login-nav-btn" 
          @click="openAuthModal('login')"
        >
          {{ t('登入', 'Sign In') }}
        </button>
        <button 
          v-else 
          class="login-nav-btn logout-mode" 
          @click="handleLogout"
          :title="t('點擊登出系統', 'Click to sign out')"
        >
          {{ t('登出', 'Sign Out') }}
        </button>

        <!-- 中英雙語切換按鈕：中文介面時顯示 EN，英文介面時顯示 中文 -->
        <button 
          class="lang-toggle" 
          :class="{ active: isEn }"
          @click="toggleLang"
          :title="t('Switch to English', '切換為繁體中文')"
        >
          {{ isEn ? '中文' : 'EN' }}
        </button>
      </div>
    </div>

    <!-- 掛載全域登入與註冊彈出視窗 -->
    <AuthModal />
  </nav>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AuthModal from './AuthModal.vue'
import { authState, fetchCurrentUser, openAuthModal } from '../utils/authStore'
import { isEn, toggleLang, t, translateRole } from '../utils/i18nStore'

const router = useRouter()
const route = useRoute()

const API_BASE_URL = window.location.port === '5173'
  ? `http://${window.location.hostname}:8000/api`
  : '/api'

// RBAC 權限計算
const currentRole = computed(() => authState.user?.role || '訪客')
const isAdmin = computed(() => currentRole.value === '系統管理者')
const canAccessHazardAndHistory = computed(() => {
  return currentRole.value === '系統管理者' || currentRole.value === '專家'
})

const displayUserName = computed(() => {
  const rawName = authState.user?.name || ''
  if (isEn.value) {
    if (rawName === '訪客') return 'Guest'
    if (rawName === '系統最高管理員') return 'System Admin'
  }
  return rawName
})

const isHazardFlowActive = computed(() => {
  return route.path === '/' || route.path.startsWith('/review') || route.path.startsWith('/meta')
})

const goHome = () => {
  if (canAccessHazardAndHistory.value) {
    router.push('/')
  } else {
    router.push('/chat')
  }
}

const handleLogout = async () => {
  try {
    await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      credentials: 'include'
    })
  } finally {
    authState.isAuthenticated = false
    authState.isGuest = false
    authState.user = null
    router.push('/chat')
    openAuthModal('login', t('您已成功登出系統。', 'You have successfully signed out.'))
  }
}

const getRoleBadgeClass = (role) => {
  if (role === '系統管理者') return 'pill-admin'
  if (role === '專家') return 'pill-expert'
  if (role === '會員') return 'pill-member'
  return 'pill-guest'
}

onMounted(() => {
  fetchCurrentUser()
})
</script>

<style scoped>
.navbar {
  background-color: var(--primary-color);
  height: 64px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 28px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 14px;
  cursor: pointer;
  user-select: none;
  transition: opacity 0.2s ease;
}

.nav-left:hover {
  opacity: 0.9;
}

.logo-img {
  height: 40px;
  width: auto;
  object-fit: contain;
}

.product-title {
  color: #1b1e29;
  font-size: 20px;
  margin: 0;
  font-weight: 800;
  letter-spacing: 0.5px;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 16px;
  user-select: none;
}

.nav-page-group {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: rgba(255, 255, 255, 0.22);
  padding: 4px;
  border-radius: 12px;
}

.nav-page-btn {
  background-color: transparent;
  color: #1b1e29;
  border: none;
  padding: 7px 18px;
  border-radius: 9px;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.4px;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.nav-page-btn:hover:not(.active) {
  background-color: rgba(255, 255, 255, 0.55);
  color: var(--dark-color);
}

.nav-page-btn.active {
  background-color: #ffffff;
  color: var(--dark-color);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.nav-divider {
  width: 1.5px;
  height: 24px;
  background-color: rgba(27, 30, 41, 0.2);
}

.nav-utility-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.role-status-pill {
  font-size: 12.5px;
  font-weight: 800;
  padding: 5px 12px;
  border-radius: 14px;
  white-space: nowrap;
}

.pill-admin {
  background-color: #fef3c7;
  color: #92400e;
  border: 1px solid #f59e0b;
}

.pill-expert {
  background-color: #e0f2fe;
  color: #075985;
  border: 1px solid #38bdf8;
}

.pill-member {
  background-color: #dcfce7;
  color: #166534;
  border: 1px solid #4ade80;
}

.pill-guest {
  background-color: rgba(255, 255, 255, 0.65);
  color: #475569;
}

.login-nav-btn {
  background-color: #1b1e29;
  color: #ffffff;
  border: 1.5px solid #1b1e29;
  padding: 6px 18px;
  border-radius: 20px;
  font-size: 14.5px;
  font-weight: 800;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.login-nav-btn:hover {
  background-color: var(--dark-color);
  border-color: var(--dark-color);
  transform: translateY(-1px);
}

.login-nav-btn.logout-mode {
  background-color: rgba(27, 30, 41, 0.85);
}

.lang-toggle {
  background-color: var(--light-color);
  color: var(--dark-color);
  border: 1.5px solid var(--dark-color);
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 62px;
  text-align: center;
}

.lang-toggle:hover {
  background-color: #ffffff;
}

.lang-toggle.active {
  background-color: var(--dark-color);
  color: #ffffff;
}
</style>