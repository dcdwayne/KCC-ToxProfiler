<template>
  <main class="home-view">
    <!-- 標題區 -->
    <header class="header-section">
      <h2 class="main-title">毒理學文獻條件檢索與危害辨識系統</h2>
      <h3 class="sub-title">依據科學文獻數據，執行致癌物之危害辨識評估</h3>
    </header>

    <!-- 搜尋面板 -->
    <section class="search-panel">
      <!-- 化學物質選擇 -->
      <div class="form-group">
        <div class="label-with-icon">
          <button class="info-btn" title="請選擇要進行文獻回顧的化學物質">!</button>
          <label>化學物質名稱：</label>
        </div>
        <div class="chip-container">
          <button 
            v-for="chem in chemicalOptions" 
            :key="chem"
            class="chip-btn"
            :class="{ active: selectedChemical === chem }"
            @click="selectedChemical = chem"
          >
            {{ chem }}
          </button>
        </div>
      </div>

      <!-- 條件搜尋 -->
      <div class="condition-section">
        <label class="section-label">條件搜尋：</label>
        
        <div class="form-row">
          <span>出版年份：</span>
          <span>從</span>
          <input type="number" v-model="searchForm.startYear" placeholder="YYYY" class="year-input">
          <span>至</span>
          <input type="number" v-model="searchForm.endYear" placeholder="YYYY" class="year-input">
          <span>年</span>
        </div>

        <div class="form-row">
          <span>引用次數： 被引用至少</span>
          <input type="number" v-model="searchForm.minCitations" class="cite-input">
          <span>次數以上</span>
        </div>

        <div class="form-row">
          <span>文獻類型：</span>
          <label class="radio-label">
            <input type="radio" value="Journal Article" v-model="searchForm.docType">
            Journal Article
          </label>
          <label class="radio-label">
            <input type="radio" value="Review" v-model="searchForm.docType">
            Review
          </label>
        </div>

        <div class="form-row">
          <span>期刊排名：</span>
          <div class="chip-container inline">
            <button 
              v-for="rank in ['Q1', 'Q2', 'Q3', 'Q4']" 
              :key="rank"
              class="chip-btn small"
              :class="{ active: searchForm.journalRanks.includes(rank) }"
              @click="toggleRank(rank)"
            >
              {{ rank }}
            </button>
          </div>
        </div>
      </div>

      <!-- 初步篩選成果區 -->
      <div class="preview-section">
        <button class="action-btn preview" @click="checkPreviewCount">初步篩選成果</button>
        
        <!-- 優化後的顯示框：有資料時才顯示具體文字 -->
        <div class="result-box" :class="{ 'has-data': previewCount !== null }">
          <span v-if="previewCount === null">點擊上方按鈕預估文獻數量</span>
          <span v-else>目前條件共篩選出 <strong>{{ previewCount }}</strong> 篇相關文獻</span>
        </div>
      </div>
    </section>

    <!-- 確定送出 -->
    <div class="submit-section">
      <button class="action-btn submit" @click="submitFilter">確定送出篩選</button>
    </div>
  </main>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router' // 1. 引入 useRouter

const router = useRouter() // 2. 宣告 router
// 化學物質清單 (未來可自 API 載入擴充)
const chemicalOptions = ref(['苯駢芘', '丙烯醯胺', '異環胺', 'PFOA'])
const selectedChemical = ref('丙烯醯胺')

// 搜尋表單狀態
const searchForm = reactive({
  startYear: 2020,
  endYear: 2026,
  minCitations: 10,
  docType: 'Journal Article',
  journalRanks: ['Q1', 'Q2']
})

// 期刊排名多選切換邏輯
const toggleRank = (rank) => {
  const index = searchForm.journalRanks.indexOf(rank)
  if (index > -1) {
    searchForm.journalRanks.splice(index, 1)
  } else {
    searchForm.journalRanks.push(rank)
  }
}

// 初步篩選成果數量
const previewCount = ref(null)
const checkPreviewCount = () => {
  // 模擬打 API 取得預估數量
  previewCount.value = Math.floor(Math.random() * 500) + 50 
}

// 最終送出篩選 (保留空函式供後續串接)
const submitFilter = async () => {
  const payload = {
    chemical: selectedChemical.value,
    ...searchForm
  }
  console.log('準備送出的篩選條件:', payload)
  
  // 3. 執行跳轉至深度篩選頁面
  router.push('/review') 
}

</script>

<style scoped>
.home-view {
  max-width: 800px;
  margin: 40px auto;
  padding: 0 20px;
}

.header-section {
  text-align: center;
  margin-bottom: 30px;
}

.main-title {
  color: #343434;
  font-size: 32px;
  margin-bottom: 8px;
  font-weight:bold;
}

.sub-title {
  color:#555;
  font-size: 20px;
  font-weight:bold;
}

.search-panel {
  background-color: #ffffff; 
  border-radius: 24px;
  padding: 30px 40px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  border: 1px solid #d9d9d9;
}

.label-with-icon {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 12px;
  color: #333;
}

.info-btn {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 1px solid var(--dark-color);
  background-color: transparent;
  color: var(--dark-color);
  font-weight: bold;
  cursor: help;
}

.chip-container {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}

.chip-container.inline {
  margin-bottom: 0;
  display: inline-flex;
}

/* 按鈕點擊變色邏輯實作 */
.chip-btn {
  background-color: #ffffff;
  color: #555;
  border: 1px solid var(--dark-color);
  padding: 8px 24px;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: bold;
}

.chip-btn.small {
  padding: 4px 16px;
  font-size: 14px;
}

.chip-btn:hover {
  background-color: var(--primary-color);
  color: var(--white);
}

.chip-btn.active {
  background-color: var(--dark-color);
  color: var(--white);
  border: 1px solid var(--dark-color);
}

.condition-section {
  margin-left: 32px;
}

.section-label {
  font-size: 18px;
  font-weight: bold;
  display: block;
  margin-bottom: 16px;
}

.form-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-left: 24px;
  color: #444;
}

.form-row span { 
  display: block; 
  margin-bottom: 8px; 
  color: #555; 
  font-weight: bold;}

input[type="number"] {
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 6px 8px;
  outline: none;
}

input[type="number"]:focus {
  border-color: var(--primary-color);
}

.year-input {
  width: 60px;
  font-weight: bold;
  color:#555;
}

.cite-input {
  width: 50px;
  font-weight:bold;
  color:#555;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #555; 
  font-weight: bold;
}

.preview-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  margin-top: 32px;
}

.result-box {
  width: 100%;
  max-width: 400px;
  min-height: 48px;
  background-color: #fff;
  border: 1px solid #ccc;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 16px;
  transition: all 0.3s ease;
  font-weight:bold;
}

.result-box.has-data {
  background-color: var(--light-color);
  color: var(--dark-color);
  border-color: var(--primary-color);
  font-size: 16px;
  font-weight: bold;
}

.submit-section {
  display: flex;
  justify-content: center;
  margin-top: 24px;
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

.action-btn.preview {
  background-color: var(--dark-color);
  color: var(--white);
  padding: 12px 64px;
}

.action-btn.preview:active {
  opacity: 0.6;
  transform: scale(0.96); /* 稍微縮小創造點擊下壓的物理感 */
  transition: all 0.1s ease; /* 極短的轉場時間創造閃擊感 */
}

.action-btn.submit {
  background-color: #1a1e29; /* 換成指定的深色 */
  color: var(--white);
  border-color: #1a1e29;
  padding: 12px 64px;
}

/* 確保滑鼠移過去時，也是保持這個質感深色 (或微微調亮一點點) */
.action-btn.submit:hover {
  background-color: #1a1e29; 
  color: var(--white);
}

.action-btn.submit:active {
  opacity: 0.6;
  transform: scale(0.96); /* 稍微縮小創造點擊下壓的物理感 */
  transition: all 0.1s ease; /* 極短的轉場時間創造閃擊感 */
}
</style>