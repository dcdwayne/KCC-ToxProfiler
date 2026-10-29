<template>
  <nav class="navbar">
    <!-- 點擊左側 Logo 或標題皆可回到首頁 -->
    <div class="nav-left" @click="goHome">
      <img src="/dr-manhattan-logo.png" alt="Logo" class="logo-img" />
      <h1 class="product-title">KCC ToxProfiler 致癌物關鍵特徵歸納平臺</h1>
    </div>
    
    <!-- 右側導覽列：前三個為風格一致的頁面跳轉按鈕，接著為分隔線、登入與中英切換 -->
    <div class="nav-right">
      <!-- 1. 三大頁面跳轉群組 (風格統一，並支援當前頁面自動高亮) -->
      <div class="nav-page-group">
        <button 
          class="nav-page-btn" 
          :class="{ active: isHazardFlowActive }"
          @click="router.push('/')"
        >
          危害辨識
        </button>

        <button 
          class="nav-page-btn" 
          :class="{ active: route.path.startsWith('/history') }"
          @click="router.push('/history')"
        >
          歷史紀錄
        </button>

        <button 
          class="nav-page-btn" 
          :class="{ active: route.path.startsWith('/chat') }"
          @click="router.push('/chat')"
        >
          Dr. Manhattan
        </button>
      </div>

      <!-- 視覺分隔線 -->
      <span class="nav-divider"></span>

      <!-- 2. 系統功能群組：登入 & 中英轉換按鈕 -->
      <div class="nav-utility-group">
        <button class="login-nav-btn" @click="handleLoginClick">
          登入
        </button>
        <!--
        <button 
          class="lang-toggle" 
          :class="{ active: currentLang === 'EN' }"
          @click="toggleLang"
          title="切換語言 / Switch Language"
        >
          {{ currentLang }}
        </button>
        -->
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const currentLang = ref('EN')

// 當位於首頁(/)、系統性文獻回顧(/review)或統合分析(/meta)時，皆屬於「危害辨識」主流程
const isHazardFlowActive = computed(() => {
  return route.path === '/' || route.path.startsWith('/review') || route.path.startsWith('/meta')
})

const goHome = () => {
  router.push('/')
}

const handleLoginClick = () => {
  // 若未來有獨立登入路由可改為 router.push('/login')
  router.push('/')
}

const toggleLang = () => {
  currentLang.value = currentLang.value === 'EN' ? '中文' : 'EN'
}
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

/* 左側 Logo 與系統標題 */
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

/* 右側整體容器 */
.nav-right {
  display: flex;
  align-items: center;
  gap: 16px;
  user-select: none;
}

/* 前三個頁面跳轉按鈕群組 (風格完全一致) */
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

/* 當前所在頁面高亮狀態 */
.nav-page-btn.active {
  background-color: #ffffff;
  color: var(--dark-color);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

/* 導覽區與工具區的垂直分隔線 */
.nav-divider {
  width: 1.5px;
  height: 24px;
  background-color: rgba(27, 30, 41, 0.2);
}

/* 右側工具群組：登入 + 中英切換 */
.nav-utility-group {
  display: flex;
  align-items: center;
  gap: 10px;
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

.login-nav-btn:active {
  transform: scale(0.96);
}

.lang-toggle {
  background-color: var(--light-color);
  color: var(--dark-color);
  border: 1.5px solid var(--dark-color);
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14.5px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 58px;
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