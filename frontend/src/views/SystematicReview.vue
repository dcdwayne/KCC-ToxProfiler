<template>
  <main class="review-page">
    <!-- 移除了原本的任務說明與右上角按鈕，只保留大標題 -->
    <header class="page-header">
      <h2 class="main-title">系統性文獻回顧 <span style ="color:#e74c3c">Systematic Review</span></h2>
    </header>

    <div class="content-layout">
      <!-- 左側深度篩選面板 -->
      <aside class="sidebar-filter">
        <h3 class="filter-title">深度條件篩選：</h3>
        
        <div class="filter-group">
          <label>出版年份</label>
          <div class="form-row inline-row">
            <span class="input-text">從</span>
            <input type="number" v-model="filters.startYear" class="short-input">
            <span class="input-text">至</span>
            <input type="number" v-model="filters.endYear" class="short-input">
            <span class="input-text">年</span>
          </div>
        </div>

        <div class="filter-group">
          <label>引用次數</label>
          <div class="form-row inline-row">
            <span class="input-text">超過</span>
            <input type="number" v-model="filters.minCitations" class="short-input">
            <span class="input-text">次</span>
          </div>
        </div>

        <div class="filter-group">
          <label>適配度</label>
          <div class="form-row inline-row">
            <span class="input-text">超過</span>
            <input type="number" v-model="filters.relevance" class="short-input">
            <span class="input-text">%</span>
          </div>
        </div>

        <div class="filter-group">
          <label>資料來源</label>
          <div class="chip-container">
            <button 
              v-for="model in ['in vitro', 'in vivo', 'cohort']" 
              :key="model"
              class="chip-btn small"
              :class="{ active: filters.models.includes(model) }"
              @click="toggleModel(model)"
            >
              {{ model }}
            </button>
          </div>
        </div>

        <div class="filter-group">
          <label>樣本數</label>
          <div class="form-row inline-row">
            <span class="input-text">超過</span>
            <input type="number" v-model="filters.sampleSize" class="short-input">
            <span class="input-text">個</span>
          </div>
        </div>

        <button class="action-btn apply-filter">送出深度篩選</button>
      </aside>

      <!-- 右側 Evidence Pool 區塊 -->
      <section class="evidence-pool-section">
        <!-- 將 pool-header 設為左右排版 -->
        <div class="pool-header">
          <div class="pool-title-group">
            <button class="info-btn">!</button>
            <h3 class="pool-title">KCC EVIDENCE POOL：</h3>
          </div>
          <!-- 統合分析按鈕移到這裡，與 Evidence Pool 標題一左一右 -->
          <button class="action-btn submit-analysis" @click="goToMetaAnalysis">執行統合分析</button>
        </div>

        <!-- 10 KCCs 按鈕區 -->
        <div class="kcc-grid">
          <button 
            v-for="kcc in kccCategories" 
            :key="kcc.name"
            class="kcc-btn"
            :class="{ active: activeKCC === kcc.name }"
            @click="selectKCC(kcc.name)"
          >
            {{ kcc.name }}<br>
            <span class="kcc-count">({{ kcc.count }})</span>
          </button>
        </div>

        <!-- 動態文獻列表區 (此處維持原樣) -->
        <div class="list-container" v-if="activeKCC">
          <div class="list-controls">
            <h4 class="list-title">{{ activeKCC }} 相關文獻結果共 {{ currentPapers.length }} 筆：</h4>
            <div class="sort-options">
              <span>排序：</span>
              <button class="chip-btn small active">適配度</button>
              <button class="chip-btn small">資料來源</button>
              <button class="chip-btn small">引用次數</button>
            </div>
          </div>

          <div class="paper-list">
             <SystematicReviewList 
                v-for="(paper, index) in currentPapers" 
                :key="paper.id"
                :index="index + 1"
                :paper="paper"
                @view-details="openModal"
                @remove-paper="removePaper"
             />
          </div>
          
          <div class="pagination">
            <button class="page-btn active">1</button>
            <button class="page-btn">2</button>
            <button class="page-btn">3</button>
          </div>
        </div>
      </section>
    </div>
    
    <PaperDetailModal v-if="isModalOpen" :paper="selectedPaper" @close="closeModal" />
  </main>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
// ... 引入其他組件 ...
import SystematicReviewList from '../components/SystematicReviewList.vue'
import PaperDetailModal from '../components/PaperDetailModal.vue'

const router = useRouter()
// 深度篩選條件狀態
const filters = reactive({
  startYear: null,
  endYear: null,
  minCitations: null,
  relevance: null,
  models: [],
  sampleSize: null
})

const toggleModel = (model) => {
  const index = filters.models.indexOf(model)
  if (index > -1) filters.models.splice(index, 1)
  else filters.models.push(model)
}

// KCC 狀態與假資料
const activeKCC = ref('Electrophilic')
const kccCategories = ref([
  { name: 'Electrophilic', count: 12 },
  { name: 'Genotoxic', count: 45 },
  { name: 'Alters DNA Repair', count: 8 },
  { name: 'Epigenetic Alterations', count: 15 },
  { name: 'Oxidative Stress', count: 32 },
  { name: 'Chronic Inflammation', count: 18 },
  { name: 'Immunosuppressive', count: 6 },
  { name: 'Receptor-Mediated Effects', count: 11 },
  { name: 'Immortalization', count: 3 },
  { name: 'Cell Proliferation/Death', count: 24 }
])

const selectKCC = (name) => {
  activeKCC.value = name
  // 實務上這裡會觸發 API 拉取該 KCC 的論文清單
}

// 論文清單假資料
const currentPapers = ref([
  { id: '42839924', title: 'Cost-effectiveness analysis of treatments...', model: 'cohort', citations: 15, abstract: 'To evaluate the cost-effectiveness...' },
  { id: '42837440', title: 'Tandem Diels-Alder reactions...', model: 'in vivo', citations: 42, abstract: 'Biomass holds significant promise...' },
  { id: '42832515', title: 'Evaluation of preanalytical errors...', model: 'in vitro', citations: 8, abstract: 'Errors in the preanalytical phase...' }
])

// 移除論文邏輯
const removePaper = (paperId) => {
  currentPapers.value = currentPapers.value.filter(p => p.id !== paperId)
  // 同步更新 KCC 上的數字
  const kcc = kccCategories.value.find(k => k.name === activeKCC.value)
  if(kcc) kcc.count--
}

// 彈出視窗邏輯
const isModalOpen = ref(false)
const selectedPaper = ref(null)

const openModal = (paper) => {
  selectedPaper.value = paper
  isModalOpen.value = true
}

const closeModal = () => {
  isModalOpen.value = false
  selectedPaper.value = null
}

const goToMetaAnalysis = () => {
  // 實務上這裡會呼叫 FastAPI 計算分數，拿到回應後再跳轉
  // DEMO 階段直接跳轉
  router.push('/meta')
}
</script>

<style scoped>
.review-page { max-width: 1200px; margin: 40px auto; padding: 0 20px; }
.page-header { margin-bottom: 24px; }
.main-title { font-family: 'Georgia', serif; font-size: 40px; font-weight: 900; margin: 0 0 12px 0; letter-spacing: -1px;}
.header-actions { display: flex; align-items: flex-start; gap: 24px; }
.task-desc { color: #666; font-size: 14px; margin: 0; }
.highlight-red { color: #e74c3c; font-weight: bold; }

.content-layout { display: flex; gap: 32px; }

/* 篩選輸入框縮短與加入文字排版 */
.inline-row {
  display: flex;
  align-items: center;
  gap: 8px; /* 元素之間的間距 */
}
.input-text {
  font-size: 14px;
  color: #555;
  white-space: nowrap; /* 確保文字不會換行 */
}
.short-input {
  width: 60px; /* 框框縮短 */
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 8px;
  background-color: transparent;
  text-align: center;
}

/* 左側面板樣式 */
.sidebar-filter {
  width: 280px;
  background-color: #ffffff;
  border: 1px solid #ffffff;
  border-radius: 24px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.filter-title { text-align:left; margin: 0 0 12px 0; color: #333; }
.filter-group label { display: block; margin-bottom: 8px; color: #555; font-weight: bold;}
.form-row { display: flex; gap: 8px; font-weight: bold;}
.year-input, .full-input {
  width: 100%;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 8px;
  background-color: transparent;
}
.chip-container { display: flex; flex-wrap: wrap; gap: 8px; }

/* 共用按鈕樣式 */
.chip-btn {
  background-color: #ffffff;
  color: #000;
  border: 1px solid #ccc;
  padding: 6px 16px;
  border-radius: 8px;
  cursor: pointer;
}
.chip-btn.active {
  background-color: var(--dark-color);
  color: var(--white);
}
.action-btn {
  background-color: var(--dark-color);
  color: #ffffff;
  border: 1px solid var(--light-color);
  padding: 12px 32px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-btn:hover {
  background-color: var(--dark-color);
  color: var(--white);
}

/* 送出篩選與統合分析，加上點擊特效 */
.action-btn.apply-filter {
  padding: 12px 24px; /* 可依版面微調寬度 */
}

/* 將原本共用的深色蓋掉，獨立設定這個按鈕為 #1a1e29 */
.action-btn.submit-analysis {
  background-color: #1a1e29;
  color: var(--white);
  border-color: #1a1e29;
  padding: 12px 24px;
}

.action-btn.submit-analysis:hover {
  background-color: #1a1e29;
  color: var(--white);
}

.action-btn:active {
  opacity: 0.6;
  transform: scale(0.96); /* 稍微縮小創造點擊下壓的物理感 */
  transition: all 0.1s ease; /* 極短的轉場時間創造閃擊感 */
}

/* 右側區域樣式 */
.evidence-pool-section { flex: 1; }
/* KCC Evidence Pool 與按鈕左右對齊 */
.pool-header { 
  display: flex; 
  justify-content: space-between; /* 關鍵：一左一右對齊 */
  align-items: center; 
  margin-bottom: 16px; 
}
.pool-title-group {
  display: flex;
  align-items: center;
  gap: 8px;
}
.pool-title { margin: 0; }

.info-btn {
  width: 24px; height: 24px; border-radius: 50%; border: 1px solid var(--dark-color);
  background-color: transparent; color: var(--dark-color); font-weight: bold; cursor: help;
}
.kcc-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 32px;
}
/* 10個機轉按鈕改成白底 */
.kcc-btn {
  background-color: #ffffff; /* 改為白底 */
  border: 1px solid #ffffff;
  border-radius: 8px;
  padding: 8px;
  text-align: center;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: bold;
}
/* 機轉按鈕點選後的狀態維持深色 */
.kcc-btn.active {
  background-color: var(--dark-color);
  color: var(--white);
  border-color: var(--dark-color);
}
.kcc-count { font-size: 12px; }

.list-controls { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.list-title { margin: 0; font-size: 18px; color: #333; }
.sort-options { display: flex; align-items: center; gap: 8px; }

.paper-list { display: flex; flex-direction: column; gap: 12px; }
.pagination { display: flex; justify-content: center; gap: 8px; margin-top: 24px; }
.page-btn { padding: 4px 12px; border: 1px solid #ccc; background: #e5e5e5; cursor: pointer; }
.page-btn.active { background: #fff; font-weight: bold; }
</style>