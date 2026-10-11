<template>
  <main class="meta-page">
    <!-- 頂部標題與分數區塊 -->
    <header class="meta-header">
      <div class="header-left">
        <h1 class="main-title">Meta-analysis</h1>
        <div class="target-info">
          <span class="label">ANALYSIS TARGET</span>
          <h2 class="target-name">BENZO[A]PYRENE</h2>
          <span class="curated-date">Curated: 2026/10/11</span>
        </div>
      </div>
      
      <!-- 右側 Hazard Score 徽章 -->
      <div class="score-badge">
        <span class="score-label">HAZARD SCORE</span>
        <span class="score-value">96</span>
        <span class="score-risk">HIGH RISK</span>
      </div>
    </header>

    <!-- 頁籤導覽列 -->
    <nav class="tab-nav">
      <button class="info-btn">!</button>
      <button 
        class="action-btn tab-btn" 
        :class="{ active: activeTab === 'Public' }" 
        @click="activeTab = 'Public'"
      >Public</button>
      <button 
        class="action-btn tab-btn" 
        :class="{ active: activeTab === 'Expert' }" 
        @click="activeTab = 'Expert'"
      >Expert</button>
      <button 
        class="action-btn tab-btn" 
        :class="{ active: activeTab === 'Dashboard' }" 
        @click="activeTab = 'Dashboard'"
      >Dashboard</button>
    </nav>

    <!-- 內容區域 -->
    <section class="content-area">
      
      <!-- Public / Expert 文字報告視圖 -->
      <div v-if="activeTab === 'Public' || activeTab === 'Expert'" class="report-view">
        <div class="report-header">
          <span class="section-subtitle">SCIENTIFIC SYNTHESIS / CONCLUSION</span>
        </div>
        <div class="report-content">
          <h3 v-if="activeTab === 'Expert'">Toxicological Assessment of Benzo[a]pyrene (BaP)</h3>
          <h3 v-else>大眾版風險摘要：苯駢芘 (BaP)</h3>
          
          <!-- 這裡放置由 AI 生成的報告內容 -->
          <p v-if="activeTab === 'Expert'">
            <strong>Benzo[a]pyrene</strong> is a classic, high-potency carcinogen that meets the majority of the 10 Key Characteristics (KCC) defined by the IARC framework. Based on the provided literature, there is <strong>Strong</strong> evidence for its metabolic activation into electrophilic metabolites (KCC 1), specifically via the <strong>CYP450 system</strong> (PMID: 9542332). This activation leads to the formation of stable <strong>DNA adducts</strong> and significant DNA damage (KCC 2)...
          </p>
          <p v-else>
            苯駢芘 (BaP) 是一種極強的致癌物質，廣泛存在於燒烤食物與汽車廢氣中。根據最新的科學文獻分析，我們發現它具備高度的基因毒性，會直接破壞人體細胞的 DNA...
          </p>
          
          <p class="conclusion">
            <strong>Conclusion:</strong> BaP is a definitive carcinogenic hazard with a score of <strong>96/100</strong>, acting primarily through genotoxicity, metabolic activation, and oxidative damage.
          </p>
        </div>
      </div>

      <!-- Dashboard 10 KCC 儀表板視圖 -->
      <div v-if="activeTab === 'Dashboard'" class="dashboard-view">
        <div class="dashboard-header">
          <span class="section-subtitle">MECHANISM ATTRIBUTION / WEIGH OF EVIDENCE</span>
          <span class="model-tag">10 Key Characteristics Model</span>
        </div>
        
        <div class="kcc-grid">
          <!-- 透過 v-for 動態渲染 10 張 KCC 卡片 -->
          <div 
            v-for="kcc in kccData" 
            :key="kcc.id" 
            class="kcc-card"
          >
            <div class="card-top">
              <span class="kc-id">KC {{ kcc.id }}</span>
              <h4 class="kc-title">{{ kcc.title }}</h4>
              
              <!-- 動態證據等級 Badge -->
              <div 
                v-if="kcc.evidence !== 'Inadequate'"
                class="evidence-badge" 
                :class="getEvidenceClass(kcc.evidence)"
              >
                {{ kcc.evidence.toUpperCase() }} EVIDENCE
              </div>
            </div>
            
            <div class="card-bottom">
              <div class="status-text">
                <span :class="getEvidenceTextClass(kcc.evidence)">{{ kcc.statusText }}</span>
                <span class="percentage">{{ kcc.score }}%</span>
              </div>
              <!-- 動態進度條顏色 -->
              <div class="progress-bar">
                <div class="progress-fill" :class="getEvidenceClass(kcc.evidence)" :style="{ width: kcc.score + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </section>
  </main>
</template>

<script setup>
import { ref } from 'vue'

const activeTab = ref('Public')

// 幫助判斷 CSS class 的函式
const getEvidenceClass = (level) => {
  switch(level) {
    case 'High': return 'bg-high';
    case 'Moderate': return 'bg-moderate';
    case 'Weak': return 'bg-weak';
    default: return 'bg-inadequate';
  }
}

const getEvidenceTextClass = (level) => {
  switch(level) {
    case 'High': return 'text-high';
    case 'Moderate': return 'text-moderate';
    case 'Weak': return 'text-weak';
    default: return 'text-inadequate';
  }
}

// 模擬後端傳來的 10 KCC 分析數據
const kccData = ref([
  { id: '01', title: 'ELECTROPHILIC', evidence: 'High', statusText: 'STRONG', score: 95 },
  { id: '02', title: 'GENOTOXIC', evidence: 'High', statusText: 'STRONG', score: 98 },
  { id: '03', title: 'ALTERS DNA REPAIR', evidence: 'Inadequate', statusText: 'INADEQUATE', score: 25 },
  { id: '04', title: 'EPIGENETIC ALTERATIONS', evidence: 'High', statusText: 'MODERATE', score: 70 },
  { id: '05', title: 'OXIDATIVE STRESS', evidence: 'High', statusText: 'STRONG', score: 92 },
  { id: '06', title: 'CHRONIC INFLAMMATION', evidence: 'Moderate', statusText: 'MODERATE', score: 65 },
  { id: '07', title: 'IMMUNOSUPPRESSIVE', evidence: 'Weak', statusText: 'WEAK', score: 30 },
  { id: '08', title: 'RECEPTOR-MEDIATED EFFECTS', evidence: 'High', statusText: 'MODERATE', score: 75 },
  { id: '09', title: 'IMMORTALIZATION', evidence: 'High', statusText: 'STRONG', score: 90 },
  { id: '10', title: 'CELL PROLIFERATION/DEATH', evidence: 'High', statusText: 'STRONG', score: 94 }
])
</script>

<style scoped>
.meta-page {
  max-width: 1200px;
  margin: 40px auto;
  padding: 0 20px;
}

/* 頂部 Header 樣式 */
.meta-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}
.main-title {
  font-family: 'Georgia', serif; /* 模擬截圖中帶有襯線的粗體字 */
  font-size: 56px;
  font-weight: 900;
  margin: 0 0 12px 0;
  letter-spacing: -1px;
}
.target-info { display: flex; flex-direction: column; gap: 4px; }
.label { font-size: 12px; color: #888; letter-spacing: 1px; }
.target-name { font-size: 28px; margin: 0; color: #333; font-weight: 400; letter-spacing: 1px;}
.curated-date { font-size: 12px; color: #999; }

/* 右側分數徽章 */
.score-badge {
  background-color: #1a1e29;
  color: #fff;
  border-bottom: 6px solid #e74c3c;
  border-radius: 4px;
  padding: 16px 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 8px 16px rgba(0,0,0,0.15);
}
.score-label { font-size: 10px; letter-spacing: 1px; color: #aaa; }
.score-value { font-size: 48px; font-weight: bold; line-height: 1.2; margin: 4px 0; }
.score-risk { font-size: 10px; color: #e74c3c; font-weight: bold; letter-spacing: 1px; }

/* 導覽列與按鈕 (套用要求的深色特效) */
.tab-nav {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}
.info-btn {
  width: 38px; height: 38px; border-radius: 50%; border: 1px solid #666;
  background-color: transparent; font-weight: bold; font-size: 18px; cursor: help;
}
.action-btn.tab-btn {
  background-color: #ffffff;
  color: #333;
  border: 1px solid var(--dark-color);
  padding: 8px 32px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 120px;
}
/* 活躍狀態與 Hover 狀態 (深底白字) */
.action-btn.tab-btn.active,
.action-btn.tab-btn:hover {
  background-color: var(--dark-color);
  color: #ffffff;
}
/* 點擊瞬間的微縮特效 */
.action-btn.tab-btn:active {
  opacity: 0.8;
  transform: scale(0.96);
  transition: all 0.1s ease;
}

/* 內容區域公用樣式 */
.content-area {
  background-color: #f8f9fa; /* 極淺灰底襯托白色卡片 */
  padding: 24px;
  border-radius: 8px;
}
.section-subtitle {
  font-size: 12px;
  font-weight: bold;
  color: #888;
  letter-spacing: 1.5px;
  text-transform: uppercase;
}

/* 文字報告視圖 */
.report-view {
  background-color: #fff;
  border: 1px solid #e0e0e0;
  border-left: 4px solid var(--dark-color); /* 左側點綴線 */
  padding: 32px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}
.report-content p {
  line-height: 1.8;
  color: #444;
  font-size: 15px;
  margin-bottom: 16px;
}
.conclusion {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

/* Dashboard 卡片視圖 */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 24px;
}
.model-tag { font-size: 12px; color: #bbb; }

.kcc-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}
.kcc-card {
  background-color: #fff;
  border: 1px solid #eee;
  padding: 16px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 160px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}
.kc-id { font-size: 10px; color: #aaa; font-weight: bold; }
.kc-title { font-size: 12px; font-weight: 800; margin: 4px 0 12px 0; color: #222; }

/* 證據等級標籤 (Badge) */
.evidence-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: bold;
  color: #fff;
  margin-top: auto;
}

/* 底部進度條 */
.card-bottom { margin-top: auto; }
.status-text {
  display: flex;
  justify-content: space-between;
  font-size: 9px;
  font-weight: bold;
  margin-bottom: 4px;
}
.percentage { color: #888; }
.progress-bar {
  height: 3px;
  background-color: #eee;
  border-radius: 2px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
}

/* 動態顏色系統 (High, Moderate, Weak, Inadequate) */
.bg-high { background-color: #ff5252; }
.bg-moderate { background-color: #ffca28; color: #333 !important;} /* 黃底黑字 */
.bg-weak { background-color: #b0bec5; }
.bg-inadequate { background-color: #eeeeee; }

.text-high { color: #ff5252; }
.text-moderate { color: #f57f17; }
.text-weak { color: #78909c; }
.text-inadequate { color: #bdbdbd; }
</style>