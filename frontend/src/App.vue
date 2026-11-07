<script setup>
import NavBar from './components/Nav.vue'
import GlobalPinTooltip from './components/GlobalPinTooltip.vue'
</script>

<template>
  <div class="app-container">
    <NavBar />
    <!-- 這裡會根據網址自動替換成 HomeView, SystematicReview 或 MetaAnalysis -->
    <router-view />
    <!-- 全站通用：Hover 預覽 + 點擊定住複製 PMID / 匹配片段視窗 -->
    <GlobalPinTooltip />
  </div>
</template>

<style>
/* 全域 CSS 變數定義，方便統一控管色系 */
:root {
  --primary-color: #80cad0;
  --dark-color: #3d7a8c;
  --light-color: #d1f5f8;
  --white: #ffffff;
  --bg-gray: #f5f5f5;
}

body {
  margin: 0;
  font-family: 'Helvetica Neue', Arial, sans-serif;
  background-color: var(--light-color);
  color: #333;
}

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 停用舊版無法選取複製的 ::after 偽元素，統一交由 GlobalPinTooltip 處理 Hover 與點擊定住 */
.apa-citation::after,
.highlight-sentence::after,
.matched-sentence::after {
  display: none !important;
  content: none !important;
}

/* 當某個引用或黃色匹配片段被點擊定住時的高亮外框提示 */
.pinned-highlight-active {
  outline: 2px solid #e25740 !important;
  box-shadow: 0 0 0 3px rgba(246, 211, 45, 0.5) !important;
  border-radius: 4px;
}

/* ================= 全站 RWD 基礎防溢位設定  ================= */
html, body {
  max-width: 100vw;
  overflow-x: hidden;
  box-sizing: border-box;
}

*, *::before, *::after {
  box-sizing: border-box;
}
</style>