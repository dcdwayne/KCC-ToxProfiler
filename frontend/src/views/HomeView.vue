<template>
  <main class="home-view">
    <!-- 標題區 -->
    <header class="header-section">
      <h2 class="main-title">毒理學文獻條件檢索與危害辨識評估系統</h2>
      <h3 class="sub-title">依據科學文獻資料，系統化致癌物之危害辨識評估流程</h3>
    </header>

    <!-- 搜尋面板 -->
    <section class="search-panel">
      <!-- 化學物質選擇 (單選，共五個) -->
      <div class="form-group">
        <div class="label-with-icon">
          <button 
            class="info-btn" 
            title="點擊查看本頁使用說明"
            @click="isGuideOpen = true"
          >!</button>
          <label>化學物質名稱 Target Chemicals</label>
        </div>
        <div class="chip-container">
          <button 
            v-for="chem in chemicalOptions" 
            :key="chem"
            class="chip-btn"
            :class="{ active: selectedChemical === chem }"
            @click="selectChemical(chem)"
          >
            {{ chem }}
          </button>
        </div>
      </div>

      <!-- 條件搜尋 -->
      <div class="condition-section">
        <label class="section-label">初步條件搜尋 Preliminary Filter</label>
        
        <div class="form-row">
          <span>出版年份：</span>
          <span>從</span>
          <input type="number" v-model.number="searchForm.startYear" placeholder="YYYY" class="year-input">
          <span>至</span>
          <input type="number" v-model.number="searchForm.endYear" placeholder="YYYY" class="year-input">
          <span>年</span>
        </div>

        <!-- 修正為單選：綁定 searchForm.minCitations -->
        <div class="form-row">
          <span>引用次數：被引用至少</span>
          <button 
            v-for="cite in [1, 3, 10, 20]" 
            :key="cite"
            class="chip-btn small"
            :class="{ active: searchForm.minCitations === cite }"
            @click="searchForm.minCitations = cite"
          >
            {{ cite }}
          </button>
          <span>次以上</span>
        </div>

        <div class="form-row">
          <span>文獻類型：</span>
          <label class="radio-label">
            <input type="radio" value="Original Research" v-model="searchForm.docType">
            Original Research
          </label>
          <label class="radio-label">
            <input type="radio" value="Review" v-model="searchForm.docType">
            Review
          </label>
          <label class="radio-label">
            <input type="radio" value="All" v-model="searchForm.docType">
            All
          </label>
        </div>

        <!-- 期刊排名：支援多選與 All 切換 -->
        <div class="form-row">
          <span>期刊排名：</span>
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

      <!-- 初步篩選成果區 -->
      <div class="preview-section">
        <button class="action-btn preview" :disabled="isLoadingPreview" @click="checkPreviewCount">
          {{ isLoadingPreview ? '檢索計算中...' : '初步篩選成果' }}
        </button>
        
        <div class="result-box" :class="{ 'has-data': previewCount !== null }">
          <span v-if="previewCount === null">點擊上方按鈕預估文獻數量</span>
          <span v-else>目前條件共篩選出 <strong>{{ previewCount }}</strong> 篇相關文獻</span>
        </div>
      </div>
    </section>

    <!-- 確定送出 -->
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
  max-width: 800px;
  margin: 20px auto 40px auto;
  padding: 0 20px;
}

.header-section {
  text-align: center;
  margin-bottom: 30px;
}

/* 主標題：#1b1e29 字體搭配 #e25740 立體塊狀陰影 */
.main-title {
  color: #1b1e29;
  font-size: 36px;
  margin-top: 16px;
  margin-bottom: 20px;
  font-weight: 900;
  letter-spacing: 1.5px;
  text-shadow: 
    1px 1px 0px #f6d32d,
    2px 2px 0px #f6d32d,
    3px 3px 0px #e25740,
    4px 4px 0px #f6d32d;
}

.sub-title {
  color: #555;
  font-size: 20px;
  margin-top: 0;
  font-weight: bold;
}

.search-panel {
  background-color: #ffffff; 
  border-radius: 24px;
  padding: 30px 40px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  border: 1px solid #ffffff;
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
  color: #555; 
  font-weight: bold;
}

input[type="number"] {
  border: 1px solid var(--dark-color);
  border-radius: 4px;
  padding: 6px 8px;
  outline: none;
}

/* 修改點 3：提高選擇器權重至 input[type="number"].year-input，確保 dark-color 邊框生效 */
input[type="number"].year-input {
  width: 72px;
  font-weight: bold;
  color: #555;
  border: 1px solid var(--dark-color);
  text-align: center;
}

input[type="number"].year-input:focus {
  border-color: var(--primary-color);
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
  font-weight: bold;
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

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.action-btn.preview {
  background-color: var(--dark-color);
  color: var(--white);
  padding: 12px 64px;
}

.action-btn.preview:active {
  opacity: 0.6;
  transform: scale(0.96);
  transition: all 0.1s ease;
}

.action-btn.submit {
  background-color: #1a1e29;
  color: var(--white);
  border-color: #1a1e29;
  padding: 12px 64px;
}

.action-btn.submit:hover {
  background-color: #1a1e29; 
  color: var(--white);
}

.action-btn.submit:active {
  opacity: 0.6;
  transform: scale(0.96);
  transition: all 0.1s ease;
}
</style>