<template>
  <nav class="navbar">
    <!-- 點擊左側 Logo 或標題皆可回到首頁 -->
    <div class="nav-left" @click="goHome">
      <img src="/dr-manhattan-logo.png" alt="Logo" class="logo-img" />
      <h1 class="product-title">KCC ToxProfiler 致癌物關鍵特徵歸納平臺</h1>
    </div>
    
    <div class="nav-right">
      <button 
        class="lang-toggle" 
        :class="{ active: currentLang === 'EN' }"
        @click="toggleLang"
      >
        {{ currentLang }}
      </button>
    </div>
  </nav>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const currentLang = ref('EN')

const goHome = () => {
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
  padding: 0 24px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer; /* 滑鼠移過去變可點擊手勢 */
  user-select: none;
}

.logo-img {
  height: 40px;
  width: auto;
  object-fit: contain;
}

.product-title {
  color: #343434;
  font-size: 20px;
  margin: 0;
  font-weight: 600;
}

.lang-toggle {
  background-color: var(--light-color);
  color: var(--dark-color);
  border: none;
  padding: 6px 16px;
  border-radius: 20px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
}

.lang-toggle:hover {
  background-color: var(--white);
}

.lang-toggle.active {
  background-color: var(--dark-color);
  color: var(--white);
}
</style>