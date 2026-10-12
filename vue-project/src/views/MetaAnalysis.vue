<template>
  <main class="meta-page">
    <header class="meta-header">
      <div class="header-left">
        <h1 class="main-title">證據權重危害變識統合分析 <span style ="color:#e74c3c">Meta-analysis</span></h1>
        <div class="target-info">
          <span class="label">ANALYSIS TARGET</span>
          <h2 class="target-name">BENZO[A]PYRENE</h2>
          <span class="curated-date">Curated: 2026/10/11</span>
        </div>
      </div>
      
      <div class="score-badge">
        <span class="score-label">HAZARD SCORE</span>
        <span class="score-value">96</span>
        <span class="score-risk">HIGH RISK</span>
      </div>
    </header>

    <nav class="tab-nav">
      <button class="info-btn">!</button>
      <button class="action-btn tab-btn" :class="{ active: activeTab === 'Public' }" @click="activeTab = 'Public'">Public</button>
      <button class="action-btn tab-btn" :class="{ active: activeTab === 'Expert' }" @click="activeTab = 'Expert'">Expert</button>
      <button class="action-btn tab-btn" :class="{ active: activeTab === 'Dashboard' }" @click="activeTab = 'Dashboard'">Dashboard</button>
    </nav>

    <!-- 內容區域：根據 activeTab 顯示對應組件 -->
    <section class="content-area">
      <MetaPublic v-if="activeTab === 'Public'" />
      <MetaExpert v-if="activeTab === 'Expert'" />
      <MetaDashboard v-if="activeTab === 'Dashboard'" />
    </section>
  </main>
</template>

<script setup>
import { ref } from 'vue'
import MetaPublic from '../components/MetaPublic.vue'
import MetaExpert from '../components/MetaExpert.vue'
import MetaDashboard from '../components/MetaDashboard.vue'

const activeTab = ref('Public')
</script>

<style scoped>
/* 主頁面只保留最外層佈局的 CSS */
.meta-page { max-width: 1200px; margin: 40px auto; padding: 0 20px; }

.meta-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.main-title { font-family: 'Georgia', serif; font-size: 40px; font-weight: 900; margin: 0 0 12px 0; letter-spacing: -1px; }
.target-info { display: flex; flex-direction: column; gap: 4px; }
.label { font-size: 12px; color: #555; letter-spacing: 1px; }
.target-name { font-size: 28px; margin: 0; color: #333; font-weight: 400; letter-spacing: 1px;}
.curated-date { font-size: 12px; color: #555; }

.score-badge { background-color: #1a1e29; color: #fff; border-bottom: 6px solid #e74c3c; border-radius: 4px; padding: 16px 32px; display: flex; flex-direction: column; align-items: center; box-shadow: 0 8px 16px rgba(0,0,0,0.15); }
.score-label { font-size: 10px; letter-spacing: 1px; color: #aaa; }
.score-value { font-size: 48px; font-weight: bold; line-height: 1.2; margin: 4px 0; }
.score-risk { font-size: 10px; color: #e74c3c; font-weight: bold; letter-spacing: 1px; }

.tab-nav { display: flex; gap: 12px; margin-bottom: 24px; align-items: center;}
.info-btn {
  width: 24px; height: 24px; border-radius: 50%; border: 1px solid var(--dark-color);
  background-color: transparent; color: var(--dark-color); font-weight: bold; cursor: help;
}
.action-btn.tab-btn { background-color: #ffffff; color: #333; border: 1px solid var(--dark-color); padding: 8px 32px; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: all 0.2s ease; min-width: 120px; }
.action-btn.tab-btn.active, .action-btn.tab-btn:hover { background-color: var(--dark-color); color: #ffffff; }
.action-btn.tab-btn:active { opacity: 0.8; transform: scale(0.96); transition: all 0.1s ease; }

.content-area { background-color: #f8f9fa; padding: 24px; border-radius: 8px; min-height: 400px; }
</style>