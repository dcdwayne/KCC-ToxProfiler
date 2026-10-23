<template>
  <main class="home-view">
    <!-- 標題區 -->
    <header class="header-section">
      <h2 class="main-title">毒理學文獻條件檢索與危害辨識評估系統</h2>
      <div class="sub-title-banner">
        <!--<span class="step-pill">STEP 01</span>-->
        <h3 class="sub-title">依據科學文獻資料，系統化致癌物之危害辨識評估流程</h3>
      </div>
    </header>

    <!-- 搜尋面板 -->
    <section class="search-panel">
      <!-- 化學物質選擇 (單選，共五個) -->
      <div class="form-group">
        <!-- 對齊 SystematicReview.vue 左側標題列設計 (! 按鈕 + 中英雙語上下標題) -->
        <div class="section-header-bar">
          <button 
            class="info-btn" 
            title="點擊查看本頁使用說明"
            @click="isGuideOpen = true"
          >!</button>
          <div class="header-text-group">
            <span class="header-zh">化學物質名稱</span>
            <span class="header-en">TARGET CHEMICALS</span>
          </div>
        </div>

        <div class="chip-container chem-grid">
          <button 
            v-for="chem in chemicalOptions" 
            :key="chem"
            class="chip-btn chem-btn"
            :class="{ active: selectedChemical === chem }"
            @click="selectChemical(chem)"
          >
            {{ chem }}
          </button>
        </div>
      </div>

      <!-- 條件搜尋 -->
      <div class="condition-section">
        <!-- 對齊 SystematicReview.vue 證據池的左側垂直飾條標題風格 -->
        <div class="pool-title-banner">
          <span class="banner-zh">初步條件搜尋</span>
          <span class="banner-en">PRELIMINARY FILTER</span>
        </div>
        
        <div class="filter-box">
          <div class="form-row">
            <div class="row-label">
              <span class="label-zh">出版年份</span>
              <span class="label-en">Pub Year</span>
            </div>
            <div class="row-control">
              <span class="ctrl-text">從</span>
              <input type="number" v-model.number="searchForm.startYear" placeholder="YYYY" class="year-input">
              <span class="ctrl-text">至</span>
              <input type="number" v-model.number="searchForm.endYear" placeholder="YYYY" class="year-input">
              <span class="ctrl-text">年</span>
            </div>
          </div>

          <!-- 修正為單選：綁定 searchForm.minCitations -->
          <div class="form-row">
            <div class="row-label">
              <span class="label-zh">引用次數</span>
              <span class="label-en">Citation Count</span>
            </div>
            <div class="row-control">
              <span class="ctrl-text">被引用至少</span>
              <button 
                v-for="cite in [1, 3, 10, 20]" 
                :key="cite"
                class="chip-btn small"
                :class="{ active: searchForm.minCitations === cite }"
                @click="searchForm.minCitations = cite"
              >
                {{ cite }}
              </button>
              <span class="ctrl-text">次以上</span>
            </div>
          </div>

          <div class="form-row">
            <div class="row-label">
              <span class="label-zh">文獻類型</span>
              <span class="label-en">Document Type</span>
            </div>
            <div class="row-control radio-group">
              <label class="radio-label" :class="{ selected: searchForm.docType === 'Original Research' }">
                <input type="radio" value="Original Research" v-model="searchForm.docType">
                Original Research
              </label>
              <label class="radio-label" :class="{ selected: searchForm.docType === 'Review' }">
                <input type="radio" value="Review" v-model="searchForm.docType">
                Review
              </label>
              <label class="radio-label" :class="{ selected: searchForm.docType === 'All' }">
                <input type="radio" value="All" v-model="searchForm.docType">
                All
              </label>
            </div>
          </div>

          <!-- 期刊排名：支援多選與 All 切換 -->
          <div class="form-row">
            <div class="row-label">
              <span class="label-zh">期刊排名</span>
              <span class="label-en">Journal Rank</span>
            </div>
            <div class="row-control">
              <div class="chip-container inline">
                <button 
                  v-for="rank in ['Q1', 'Q2', 'Q3', 'Q4', 'All']" 
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
        </div>
      </div>

      <!-- 初步篩選成果區 -->
      <div class="preview-section">
        <button class="action-btn preview" :disabled="isLoadingPreview" @click="checkPreviewCount">
          {{ isLoadingPreview ? '檢索計算中...' : '初步篩選成果' }}
        </button>
        
        <div class="result-box" :class="{ 'has-data': previewCount !== null }">
          <span v-if="previewCount === null">點擊上方按鈕預估符合條件之文獻數量</span>
          <span v-else>
            目前條件共篩選出 <strong class="count-highlight">{{ previewCount }}</strong> 篇相關文獻
          </span>
        </div>
      </div>
    </section>

    <!-- 確定送出 (維持指定的深色 #1a1e29 跳轉按鈕風格) -->
    <div class="submit-section">
      <button 
        class="action-btn submit" 
        :disabled="isSubmitting" 
        @click="submitFilter"
      >
        {{ isSubmitting ? '正在啟動證據池檢索...' : '確定送出篩選' }}
      </button>
    </div>

    <!-- 共用使用說明彈出視窗 (傳入 page="home") -->
    <InfoGuideModal 
      :isOpen="isGuideOpen" 
      page="home" 
      @close="isGuideOpen = false" 
    />
  </main>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import InfoGuideModal from '../components/InfoGuideModal.vue'

const router = useRouter()

// 若在本地 npm run dev (Port 5173) 則連 8000，若在 Nginx 正式環境 (Port 80) 則直接走相對路徑 '/api'
const API_BASE_URL = window.location.port === '5173'
  ? `http://${window.location.hostname}:8000/api`
  : '/api'

// 控制使用說明視窗開關
const isGuideOpen = ref(false)

const chemicalOptions = ref(['苯駢芘', '丙烯醯胺', '塑化劑', '戴奧辛', '全氟辛酸'])
const selectedChemical = ref('苯駢芘')

// 搜尋表單狀態 (預設單選引用次數為 3)
const searchForm = reactive({
  startYear: 2000,
  endYear: 2026,
  minCitations: 3,
  docType: 'Original Research',
  journalRanks: ['Q1', 'Q2']
})

const previewCount = ref(null)
const isLoadingPreview = ref(false)
const isSubmitting = ref(false)

// 切換化學物質時重置預覽數量
const selectChemical = (chem) => {
  selectedChemical.value = chem
  previewCount.value = null
}

// 期刊排名多選邏輯 (點選 All 時互切)
const toggleRank = (rank) => {
  if (rank === 'All') {
    searchForm.journalRanks = ['All']
    return
  }
  // 若原本有選 All，先移除 All
  const allIdx = searchForm.journalRanks.indexOf('All')
  if (allIdx > -1) {
    searchForm.journalRanks.splice(allIdx, 1)
  }

  const index = searchForm.journalRanks.indexOf(rank)
  if (index > -1) {
    if (searchForm.journalRanks.length > 1) {
      searchForm.journalRanks.splice(index, 1)
    }
  } else {
    searchForm.journalRanks.push(rank)
  }
}

// API 1: 點擊『初步篩選成果』(GET /api/search/preview)
const checkPreviewCount = async () => {
  isLoadingPreview.value = true
  try {
    const params = new URLSearchParams({
      chemical: selectedChemical.value,
      start_year: searchForm.startYear,
      end_year: searchForm.endYear,
      min_citations: searchForm.minCitations,
      doc_type: searchForm.docType,
      journal_ranks: searchForm.journalRanks.join(',')
    })

    const res = await fetch(`${API_BASE_URL}/search/preview?${params.toString()}`)
    if (!res.ok) throw new Error('預覽請求失敗')
    const data = await res.json()
    previewCount.value = data.count
  } catch (err) {
    console.error('初步篩選失敗:', err)
    alert('無法取得篩選數量，請確認後端 FastAPI (Port 8000) 是否已啟動！')
  } finally {
    isLoadingPreview.value = false
  }
}

// API 2: 點擊『確定送出篩選』(PUT /api/search/submit)
// 更新 papers.is_selected -> 背景啟動 Chunking & Embedding 與 10 KCC 召回重排 -> 立即跳轉至 SystematicReview.vue
const submitFilter = async () => {
  if (previewCount.value === 0) {
    alert('目前篩選條件下共有 0 篇文獻，請放寬篩選條件後再送出！')
    return
  }

  isSubmitting.value = true
  try {
    const payload = {
      chemical: selectedChemical.value,
      start_year: searchForm.startYear,
      end_year: searchForm.endYear,
      min_citations: searchForm.minCitations,
      doc_type: searchForm.docType,
      journal_ranks: searchForm.journalRanks
    }

    const res = await fetch(`${API_BASE_URL}/search/submit`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    if (!res.ok) {
      const errData = await res.json()
      throw new Error(errData.detail || '送出篩選處理失敗')
    }

    const data = await res.json()
    // 將本次動態產生的 evaluation_id 存入 localStorage 並帶入路由參數立即跳轉至下一頁
    localStorage.setItem('current_evaluation_id', data.evaluation_id)
    router.push({ path: '/review', query: { eval_id: data.evaluation_id } })
  } catch (err) {
    console.error('送出篩選失敗:', err)
    alert(`處理失敗：${err.message}`)
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.home-view {
  max-width: 820px;
  margin: 20px auto 40px auto;
  padding: 0 20px;
}

.header-section {
  text-align: center;
  margin-bottom: 12px;
}

/* 主標題：#1b1e29 字體搭配 #e25740 立體塊狀陰影 */
.main-title {
  color: #1b1e29;
  font-size: 36px;
  margin-top: 2px;
  margin-bottom: 12px;
  font-weight: 900;
  letter-spacing: 1.5px;
  text-shadow: 
    1px 1px 0px #f6d32d,
    2px 2px 0px #f6d32d,
    3px 3px 0px #e25740,
    4px 4px 0px #f6d32d;
}

.sub-title-banner {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background-color: rgba(255, 255, 255, 0.55);
  padding: 6px 18px;
  border-radius: 20px;
}

.step-pill {
  background-color: #1b1e29;
  color: #f6d32d;
  font-size: 11.5px;
  font-weight: 900;
  padding: 3px 10px;
  border-radius: 12px;
  letter-spacing: 1px;
}

.sub-title {
  color: #2c3e50;
  font-size: 17px;
  margin: 0;
  font-weight: 800;
  letter-spacing: 0.5px;
}

/* 搜尋主卡片：對齊 Review 與 Meta 頁面的卡片陰影與邊框層次 */
.search-panel {
  background-color: #ffffff; 
  border-radius: 24px;
  padding: 32px 40px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.05);
  border: 1px solid #ffffff;
}

/* 區塊標題一：對齊 SystematicReview.vue 左側進階篩選標題列 */
.section-header-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 14px;
  margin-bottom: 18px;
  border-bottom: 2px solid var(--light-color);
}

.info-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1.5px solid var(--dark-color);
  background-color: var(--light-color);
  color: var(--dark-color);
  font-weight: 900;
  font-size: 14px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  padding: 0;
  transition: all 0.2s ease;
}

.info-btn:hover {
  background-color: var(--dark-color);
  color: #ffffff;
  transform: scale(1.08);
}

.header-text-group {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.header-zh {
  font-size: 20px;
  font-weight: 900;
  color: #2c3e50;
  letter-spacing: 0.5px;
}

.header-en {
  font-size: 14px;
  font-weight: 800;
  color: var(--dark-color);
  letter-spacing: 1.2px;
}

/* 五大化學物質按鈕網格排列 */
.chip-container {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 28px;
}

.chip-container.chem-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}

.chip-container.inline {
  margin-bottom: 0;
  display: inline-flex;
  gap: 8px;
}

.chip-btn {
  background-color: #ffffff;
  color: #4a5568;
  border: 1.5px solid #cbd5e1;
  padding: 10px 16px;
  border-radius: 10px;
  font-size: 15.5px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 800;
  text-align: center;
}

.chip-btn.chem-btn {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
}

.chip-btn.small {
  padding: 6px 16px;
  font-size: 14px;
  border-radius: 8px;
}

.chip-btn:hover {
  border-color: var(--dark-color);
  color: var(--dark-color);
  transform: translateY(-1px);
}

.chip-btn.active {
  background-color: var(--dark-color);
  color: var(--white);
  border-color: var(--dark-color);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.12);
}

/* 區塊標題二：對齊 SystematicReview.vue 右側證據池垂直飾條風格 */
.condition-section {
  margin-top: 8px;
}

.pool-title-banner {
  display: flex;
  align-items: baseline;
  gap: 12px;
  border-left: 5px solid var(--dark-color);
  padding-left: 14px;
  margin-bottom: 16px;
}

.banner-zh {
  font-size: 20px;
  font-weight: 900;
  color: #2c3e50;
  letter-spacing: 0.5px;
}

.banner-en {
  font-size: 14px;
  font-weight: 800;
  color: var(--dark-color);
  letter-spacing: 1.2px;
}

/* 內部條件表單盒：採用與 MetaAnalysis.vue 相同的 #f8f9fa 淺灰底色襯托白色控制項 */
.filter-box {
  background-color: #f8f9fa;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 20px 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row {
  display: flex;
  align-items: center;
  padding-bottom: 14px;
  border-bottom: 1px dashed #e2e8f0;
}

.form-row:last-child {
  padding-bottom: 0;
  border-bottom: none;
}

/* 左側固定寬度雙語標籤欄 */
.row-label {
  width: 155px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.label-zh {
  font-size: 15.5px;
  font-weight: 800;
  color: #2c3e50;
}

.label-en {
  font-size: 11.5px;
  font-weight: 800;
  color: var(--dark-color);
  letter-spacing: 0.5px;
}

/* 右側控制項欄 */
.row-control {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  flex: 1;
}

.ctrl-text {
  color: #4a5568;
  font-weight: 700;
  font-size: 14.5px;
}

input[type="number"] {
  border: 1.5px solid var(--dark-color);
  border-radius: 6px;
  padding: 6px 10px;
  outline: none;
  background-color: #ffffff;
}

/* 修改點 3：提高選擇器權重至 input[type="number"].year-input，確保 dark-color 邊框生效 */
input[type="number"].year-input {
  width: 78px;
  font-weight: 800;
  font-size: 14.5px;
  color: #2c3e50;
  border: 1.5px solid var(--dark-color);
  text-align: center;
}

input[type="number"].year-input:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.05);
}

/* 文獻類型 Radio 升級為質感膠囊選項，消除瀏覽器預設亮藍圓點 */
.radio-group {
  gap: 10px;
}

.radio-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #4a5568; 
  font-weight: 800;
  font-size: 14px;
  background-color: #ffffff;
  border: 1.5px solid #cbd5e1;
  padding: 6px 14px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.radio-label:hover {
  border-color: var(--dark-color);
}

.radio-label.selected {
  border-color: var(--dark-color);
  background-color: var(--light-color);
  color: var(--dark-color);
}

.radio-label input[type="radio"] {
  accent-color: var(--dark-color);
  cursor: pointer;
  margin: 0;
}

/* 初步篩選成果區 */
.preview-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  margin-top: 26px;
}

.result-box {
  width: 100%;
  max-width: 460px;
  min-height: 52px;
  background-color: #f8f9fa;
  border: 1.5px dashed #cbd5e1;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-size: 15px;
  transition: all 0.3s ease;
  font-weight: 800;
}

.result-box.has-data {
  background-color: var(--light-color);
  color: #2c3e50;
  border: 1.5px solid var(--primary-color);
  border-left: 5px solid var(--dark-color);
  font-size: 16px;
  font-weight: 800;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.04);
}

.count-highlight {
  font-size: 20px;
  font-weight: 900;
  color: var(--dark-color);
  margin: 0 4px;
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
  border-radius: 10px;
  font-size: 16px;
  font-weight: 800;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: all 0.25s ease;
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.action-btn.preview {
  background-color: var(--dark-color);
  color: var(--white);
  padding: 11px 64px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.action-btn.preview:active {
  opacity: 0.6;
  transform: scale(0.96);
  transition: all 0.1s ease;
}

/* 維持你指定的深色 #1a1e29 作為跨頁跳轉按鈕 */
.action-btn.submit {
  background-color: #1a1e29;
  color: var(--white);
  border-color: #1a1e29;
  padding: 13px 68px;
  box-shadow: 0 6px 16px rgba(26, 30, 41, 0.2);
}

.action-btn.submit:hover {
  background-color: #1a1e29; 
  color: var(--white);
  transform: translateY(-1px);
}

.action-btn.submit:active {
  opacity: 0.6;
  transform: scale(0.96);
  transition: all 0.1s ease;
}
</style>