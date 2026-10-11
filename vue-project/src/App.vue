<script setup>
import NavBar from './components/Nav.vue'
</script>

<template>
  <div class="app-container">
    <NavBar />
    <!-- 這裡會根據網址自動替換成 HomeView, SystematicReview 或 MetaAnalysis -->
    <router-view></router-view>
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
</style>