<template>
  <main class="review-page">
    <!-- 頂部大標題 (已往上調小間距) -->
    <header class="page-header">
      <h2 class="main-title">
        系統性文獻回顧 <span class="title-en">Systematic Review</span>
      </h2>
    </header>

    <div class="content-layout">
      <!-- 左側：進階篩選面板 -->
      <aside class="sidebar-filter">
        <!-- 說明按鈕與標題完美水平對齊，並具備區塊標題質感 -->
        <div class="section-header-bar">
          <button class="info-btn" title="點擊查看使用說明" @click="isGuideOpen = true">!</button>
          <div class="header-text-group">
            <span class="header-zh">進階篩選</span>
            <span class="header-en">ADVANCED FILTER</span>
          </div>
        </div>
        
        <div class="filter-group">
          <label>資料來源 Source</label>
          <div class="chip-container">
            <button 
              v-for="model in ['cohort', 'in vivo', 'in vitro']" 
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
          <label>適配度 Rerank Score</label>
          <div class="form-row inline-row">
            <span class="input-text">超過</span>
            <input type="number" v-model.number="filters.relevance" class="short-input" placeholder="0">
            <span class="input-text">%</span>
          </div>
        </div>

        <div class="filter-group">
          <label>出版年份 Pub Year</label>
          <div class="form-row inline-row">
            <span class="input-text">從</span>
            <input type="number" v-model.number="filters.startYear" class="short-input" placeholder="YYYY">
            <span class="input-text">至</span>
            <input type="number" v-model.number="filters.endYear" class="short-input" placeholder="YYYY">
            <span class="input-text">年</span>
          </div>
        </div>

        <div class="filter-group">
          <label>引用次數 Citation Count</label>
          <div class="form-row inline-row">
            <span class="input-text">超過</span>
            <input type="number" v-model.number="filters.minCitations" class="short-input" placeholder="0">
            <span class="input-text">次</span>
          </div>
        </div>

        <div class="filter-group">
          <label>期刊排名 Journal Rank</label>
          <div class="form-row inline-row">
            <button 
              v-for="rank in ['Q1', 'Q2', 'Q3', 'Q4']" 
              :key="rank"
              class="chip-btn small"
              :class="{ active: filters.journalRanks.includes(rank) }"
              @click="toggleRank(rank)"
            >
              {{ rank }}
            </button>
          </div>
        </div>
        
        <!-- 底部按鈕區：左邊『重新載入』、右邊『送出篩選』 -->
        <div class="filter-action-row">
          <button 
            class="action-btn reload-btn" 
            :disabled="isProcessingFilter || !isCurrentKccReady" 
            @click="reloadCurrentKCC"
            title="將目前選中的 KC 類別恢復為初始召回的所有文獻"
          >
            重新載入
          </button>
          <button 
            class="action-btn apply-filter" 
            :disabled="isProcessingFilter || !isCurrentKccReady" 
            @click="applyAdvancedFilter"
          >
            送出篩選
          </button>
        </div>
      </aside>

      <!-- 右側：證據池 Evidence Pool 區塊 -->
      <section class="evidence-pool-section">
        <!-- 證據池標題與執行統合分析按鈕 -->
        <div class="pool-header">
          <div class="pool-title-banner">
            <span class="banner-zh">證據池</span>
            <span class="banner-en">KC EVALUATION EVIDENCE</span>
            <!-- 即時檢索進度提示膠囊 -->
            <span v-if="evalStatus === 'RETRIEVING'" class="retrieving-pill">
              <span class="pulse-dot"></span>
              AI 正在逐一檢索與重排證據池 ({{ completedKccCount }} / 10)...
            </span>
            <transition name="badge-pop">
              <span v-if="showAllReadyBanner" class="all-ready-pill">
                ✨ 10 KCC 證據池全數建置完成！
              </span>
            </transition>
          </div>
          <button 
            class="action-btn submit-analysis" 
            :disabled="isRunningAnalysis || evalStatus === 'RETRIEVING'"
            @click="goToMetaAnalysis"
            :title="evalStatus === 'RETRIEVING' ? '請等待 10 個 KC 類別全數檢索完畢後即可執行統合分析' : '點擊執行統合分析'"
          >
            {{ isRunningAnalysis ? '統合算分與生成報告中...' : (evalStatus === 'RETRIEVING' ? `證據池建置中 (${completedKccCount}/10)` : '執行統合分析') }}
          </button>
        </div>

        <!-- 10 KCCs 按鈕區 (支援：反灰未就緒 -> 流光檢索中 -> 資料準備好無到有彈出特效) -->
        <div class="kcc-grid">
          <button 
            v-for="kcc in kccCategories" 
            :key="kcc.name"
            class="kcc-btn"
            :class="{
              active: activeKCC === kcc.name && kcc.is_ready,
              'kcc-pending': !kcc.is_ready && !kcc.is_processing,
              'kcc-processing': !kcc.is_ready && kcc.is_processing,
              'kcc-just-ready': recentlyReadyKccs.includes(kcc.id)
            }"
            :disabled="!kcc.is_ready"
            @click="selectKCC(kcc.name)"
          >
            <!-- 剛完成瞬間浮現的閃耀微標籤 -->
            <span v-if="recentlyReadyKccs.includes(kcc.id)" class="just-ready-badge">✨ READY</span>

            {{ kcc.name }}<br>
            <span v-if="kcc.is_ready" class="kcc-count count-pop">({{ kcc.count }})</span>
            <span v-else-if="kcc.is_processing" class="kcc-status-text processing-text">⏳ 檢索重排中...</span>
            <span v-else class="kcc-status-text pending-text">(待檢索...)</span>
          </button>
        </div>

        <!-- 動態文獻列表區 -->
        <div class="list-container" v-if="activeKCC">
          <div class="list-controls">
            <h4 class="list-title">
              <span class="list-contents">{{ activeKCC }}</span> 相關文獻結果共 <span class="list-contents">{{ currentPapers.length }}</span> 筆：</h4>
            <div class="sort-options">
              <span>排序：</span>
              <button 
                class="chip-btn small" 
                :class="{ active: currentSort === 'source' }"
                :disabled="!isCurrentKccReady"
                @click="changeSort('source')"
              >資料來源</button>
              <button 
                class="chip-btn small" 
                :class="{ active: currentSort === 'quartile' }"
                :disabled="!isCurrentKccReady"
                @click="changeSort('quartile')"
              >期刊排名</button>
              <button 
                class="chip-btn small" 
                :class="{ active: currentSort === 'rerank' }"
                :disabled="!isCurrentKccReady"
                @click="changeSort('rerank')"
              >適配度</button>
            </div>
          </div>

          <!-- 當目前選中的 KC 還在背景檢索中時，顯示質感載入骨架提示 -->
          <div v-if="!isCurrentKccReady" class="retrieving-list-box">
            <div class="spinner-ring"></div>
            <p>正在針對 <strong>{{ activeKCC }}</strong> 執行語意切片向量召回與 Cross-Encoder 重排，完成後將自動呈現文獻...</p>
          </div>

          <!-- 文獻列表 (一頁顯示 ITEMS_PER_PAGE 篇) -->
          <transition-group v-else-if="paginatedPapers.length > 0" name="paper-fade" tag="div" class="paper-list">
            <SystematicReviewList 
              v-for="(paper, index) in paginatedPapers" 
              :key="paper.evidence_id"
              :index="(currentPage - 1) * ITEMS_PER_PAGE + index + 1"
              :paper="paper"
              @view-details="openModal"
              @remove-paper="removePaper"
            />
          </transition-group>
          <div v-else class="empty-list-box">
            目前 {{ activeKCC }} 在此篩選條件下無保留文獻（可點擊左側「重新載入」恢復原始召回文獻）。
          </div>
          
          <!-- 頁碼點擊功能：« 首頁 01 02 03 最後 » (融入系統色系) -->
          <div class="pagination-bar" v-if="isCurrentKccReady && totalPages > 1">
            <button 
              class="page-nav-btn" 
              :disabled="currentPage === 1"
              @click="goToPage(1)"
            >
              « 首頁
            </button>

            <button 
              v-for="page in visiblePages" 
              :key="page"
              class="page-num-btn"
              :class="{ active: currentPage === page }"
              @click="goToPage(page)"
            >
              {{ formatPageNumber(page) }}
            </button>

            <button 
              class="page-nav-btn" 
              :disabled="currentPage === totalPages"
              @click="goToPage(totalPages)"
            >
              最後 »
            </button>
          </div>
        </div>
      </section>
    </div>
    
    <!-- 文獻細節彈出視窗 -->
    <PaperDetailModal 
      v-if="isModalOpen" 
      :paperDetail="selectedPaperDetail" 
      :loading="isLoadingModal"
      @close="closeModal" 
    />
    <InfoGuideModal :isOpen="isGuideOpen" page="review" @close="isGuideOpen = false" />
  </main>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import SystematicReviewList from '../components/SystematicReviewList.vue'
import PaperDetailModal from '../components/PaperDetailModal.vue'
import InfoGuideModal from '../components/InfoGuideModal.vue'

const isGuideOpen = ref(false)
const router = useRouter()
const route = useRoute()

const API_BASE_URL = `http://${window.location.hostname}:8000/api`

// =====================================================================
// 👇👇👇 【每頁顯示文獻篇數設定】預設為 5 篇，可隨時在此調整 👇👇👇
// =====================================================================
const ITEMS_PER_PAGE = 5

// 取得當前評估單 ID (優先從網址 query 讀取，若無則從 localStorage 讀取，預設為 1)
const evaluationId = ref(Number(route.query.eval_id || localStorage.getItem('current_evaluation_id') || 1))

// 左側進階篩選條件狀態
const filters = reactive({
  startYear: null,
  endYear: null,
  minCitations: null,
  relevance: null,
  models: [],
  journalRanks: []
})

// 評估單目前狀態 ('RETRIEVING' | 'REVIEWING' | 'COMPLETED') 與完成進度
const evalStatus = ref('RETRIEVING')
const completedKccCount = ref(0)
const showAllReadyBanner = ref(false)

// 紀錄剛從「未完成 (false)」變成「準備完成 (true)」的 KCC ID，用來觸發無到有的閃耀彈出特效
const recentlyReadyKccs = ref([])

// 10 KCC 狀態與當前選中的 KCC (預設初始為反灰未就緒 is_ready: false)
const activeKCC = ref('ELECTROPHILIC')
const kccCategories = ref([
  { id: '01', name: 'ELECTROPHILIC', count: 0, is_ready: false, is_processing: true },
  { id: '02', name: 'GENOTOXIC', count: 0, is_ready: false, is_processing: false },
  { id: '03', name: 'ALTERS DNA REPAIR', count: 0, is_ready: false, is_processing: false },
  { id: '04', name: 'EPIGENETIC ALTERATIONS', count: 0, is_ready: false, is_processing: false },
  { id: '05', name: 'OXIDATIVE STRESS', count: 0, is_ready: false, is_processing: false },
  { id: '06', name: 'CHRONIC INFLAMMATION', count: 0, is_ready: false, is_processing: false },
  { id: '07', name: 'IMMUNOSUPPRESSIVE', count: 0, is_ready: false, is_processing: false },
  { id: '08', name: 'RECEPTOR-MEDIATED EFFECTS', count: 0, is_ready: false, is_processing: false },
  { id: '09', name: 'IMMORTALIZATION', count: 0, is_ready: false, is_processing: false },
  { id: '10', name: 'CELL PROLIFERATION/DEATH', count: 0, is_ready: false, is_processing: false }
])

const currentPapers = ref([])
const currentSort = ref('source') // 'source' | 'quartile' | 'rerank'
const currentPage = ref(1)

const isProcessingFilter = ref(false)
const isRunningAnalysis = ref(false)

// 彈出視窗狀態
const isModalOpen = ref(false)
const isLoadingModal = ref(false)
const selectedPaperDetail = ref(null)

let summaryPollTimer = null

// 判斷目前選中的 KCC 是否已經準備完成
const isCurrentKccReady = computed(() => {
  const found = kccCategories.value.find(k => k.name === activeKCC.value)
  return found ? Boolean(found.is_ready) : false
})

// --- 分頁計算邏輯 ---
const totalPages = computed(() => {
  return Math.max(1, Math.ceil(currentPapers.value.length / ITEMS_PER_PAGE))
})

const paginatedPapers = computed(() => {
  const start = (currentPage.value - 1) * ITEMS_PER_PAGE
  return currentPapers.value.slice(start, start + ITEMS_PER_PAGE)
})

// 每次最多顯示 5 個頁碼按鈕 (如 01 02 03 04 05)
const visiblePages = computed(() => {
  const total = totalPages.value
  const current = currentPage.value
  let start = Math.max(1, current - 2)
  let end = Math.min(total, start + 4)
  if (end - start < 4) {
    start = Math.max(1, end - 4)
  }
  const pages = []
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
})

const formatPageNumber = (num) => {
  return String(num).padStart(2, '0')
}

const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

// --- 篩選器按鈕切換邏輯 ---
const toggleModel = (model) => {
  const index = filters.models.indexOf(model)
  if (index > -1) filters.models.splice(index, 1)
  else filters.models.push(model)
}

const toggleRank = (rank) => {
  const index = filters.journalRanks.indexOf(rank)
  if (index > -1) filters.journalRanks.splice(index, 1)
  else filters.journalRanks.push(rank)
}

const resetFilterInputs = () => {
  filters.startYear = null
  filters.endYear = null
  filters.minCitations = null
  filters.relevance = null
  filters.models = []
  filters.journalRanks = []
}

// 觸發單一 KC 按鈕「從反灰無資料 -> 資料準備好」的閃耀特效 (持續 1.6 秒)
const triggerJustReadyEffect = (kccId) => {
  if (!recentlyReadyKccs.value.includes(kccId)) {
    recentlyReadyKccs.value.push(kccId)
    setTimeout(() => {
      recentlyReadyKccs.value = recentlyReadyKccs.value.filter(id => id !== kccId)
    }, 1600)
  }
}

// --- API 呼叫函式 ---

// 1. 載入 10 個 KCC 的文獻數量與各別就緒狀態 (支援逐一點亮特效)
const fetchKccSummary = async (isInitialLoad = false) => {
  try {
    const res = await fetch(`${API_BASE_URL}/review/${evaluationId.value}/summary`)
    if (!res.ok) throw new Error('無法取得 10 KCC 統計摘要')
    const data = await res.json()

    // 比對哪些 KCC 是剛剛從「未就緒 (false)」變成「就緒 (true)」
    const oldReadyMap = {}
    kccCategories.value.forEach(k => {
      oldReadyMap[k.id] = k.is_ready
    })

    let activeKccJustBecameReady = false

    data.kcc_categories.forEach(newKcc => {
      const wasReady = oldReadyMap[newKcc.id]
      if (!wasReady && newKcc.is_ready && !isInitialLoad) {
        triggerJustReadyEffect(newKcc.id)
        if (newKcc.name === activeKCC.value) {
          activeKccJustBecameReady = true
        }
      }
    })

    const prevStatus = evalStatus.value
    evalStatus.value = data.status
    completedKccCount.value = data.completed_kcc_count ?? 10
    kccCategories.value = data.kcc_categories

    // 若當前選中的 KC 剛完成檢索，立即自動載入它的文獻列表！
    if (activeKccJustBecameReady) {
      await fetchKccPapers()
    }

    // 若全部 10 個 KCC 都剛檢索完成，停止輪詢並顯示完成提示
    if (data.status !== 'RETRIEVING') {
      if (summaryPollTimer) {
        clearInterval(summaryPollTimer)
        summaryPollTimer = null
      }
      if (prevStatus === 'RETRIEVING' && !isInitialLoad) {
        showAllReadyBanner.value = true
        setTimeout(() => {
          showAllReadyBanner.value = false
        }, 4000)
      }
    }
  } catch (err) {
    console.error('載入 KCC 摘要失敗:', err)
  }
}

// 2. 載入當前選中 KCC 的文獻列表
const fetchKccPapers = async () => {
  if (!isCurrentKccReady.value) {
    currentPapers.value = []
    return
  }
  try {
    const params = new URLSearchParams({
      kcc_name: activeKCC.value,
      sort_by: currentSort.value
    })
    const res = await fetch(`${API_BASE_URL}/review/${evaluationId.value}/papers?${params.toString()}`)
    if (!res.ok) throw new Error('無法取得文獻列表')
    const data = await res.json()
    currentPapers.value = data.papers
    currentPage.value = 1

    // 同步更新按鈕上的數字
    const kccObj = kccCategories.value.find(k => k.name === activeKCC.value)
    if (kccObj) kccObj.count = data.total
  } catch (err) {
    console.error('載入文獻列表失敗:', err)
  }
}

// 點擊切換 KCC 類別按鈕 (僅已準備完成的 KC 可點擊)
const selectKCC = async (name) => {
  const target = kccCategories.value.find(k => k.name === name)
  if (!target || !target.is_ready) return
  activeKCC.value = name
  await fetchKccPapers()
}

// 點擊切換排序方式 (資料來源 / 期刊排名 / 適配度)
const changeSort = async (sortField) => {
  currentSort.value = sortField
  await fetchKccPapers()
}

// 3. 點擊『送出篩選』：針對當前 KC 過濾並將淘汰文獻設為 is_selected = False
const applyAdvancedFilter = async () => {
  isProcessingFilter.value = true
  try {
    const payload = {
      kcc_name: activeKCC.value,
      models: filters.models,
      min_relevance_pct: filters.relevance !== '' && filters.relevance !== null ? Number(filters.relevance) : null,
      start_year: filters.startYear !== '' && filters.startYear !== null ? Number(filters.startYear) : null,
      end_year: filters.endYear !== '' && filters.endYear !== null ? Number(filters.endYear) : null,
      min_citations: filters.minCitations !== '' && filters.minCitations !== null ? Number(filters.minCitations) : null,
      journal_ranks: filters.journalRanks
    }

    const res = await fetch(`${API_BASE_URL}/review/${evaluationId.value}/filter`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (!res.ok) throw new Error('進階篩選失敗')

    // 重新拉取該 KC 篩選後的文獻列表與按鈕數量
    await fetchKccPapers()
  } catch (err) {
    console.error('送出進階篩選失敗:', err)
    alert('進階篩選執行失敗，請檢查後端連線！')
  } finally {
    isProcessingFilter.value = false
  }
}

// 4. 點擊『重新載入』：將當前 KC 所有文獻恢復為 is_selected = True
const reloadCurrentKCC = async () => {
  isProcessingFilter.value = true
  try {
    const res = await fetch(`${API_BASE_URL}/review/${evaluationId.value}/reset`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ kcc_name: activeKCC.value })
    })
    if (!res.ok) throw new Error('重新載入失敗')

    resetFilterInputs()
    await fetchKccPapers()
  } catch (err) {
    console.error('重新載入失敗:', err)
    alert('重新載入失敗，請檢查後端連線！')
  } finally {
    isProcessingFilter.value = false
  }
}

// 5. 點擊文獻右側『X』刪除單篇文獻 (更新 is_selected = False)
const removePaper = async (paper) => {
  try {
    const res = await fetch(
      `${API_BASE_URL}/review/${evaluationId.value}/evidence/${paper.evidence_id}/remove`,
      { method: 'PUT' }
    )
    if (!res.ok) throw new Error('刪除文獻失敗')

    // 從前端列表移除並同步更新 KC 按鈕數量
    currentPapers.value = currentPapers.value.filter(p => p.evidence_id !== paper.evidence_id)
    const kcc = kccCategories.value.find(k => k.name === activeKCC.value)
    if (kcc && kcc.count > 0) kcc.count--

    // 若刪除後當前頁已無文獻且不在第一頁，自動退回上一頁
    if (paginatedPapers.value.length === 0 && currentPage.value > 1) {
      currentPage.value--
    }
  } catch (err) {
    console.error('移除文獻失敗:', err)
    alert('刪除失敗，請稍後再試！')
  }
}

// 6. 點擊文獻標題打開彈出視窗 (取得完整標題、前三作者、單位與 Hover 切片)
const openModal = async (paper) => {
  isModalOpen.value = true
  isLoadingModal.value = true
  selectedPaperDetail.value = null

  try {
    const params = new URLSearchParams({ kcc_name: activeKCC.value })
    const res = await fetch(
      `${API_BASE_URL}/review/${evaluationId.value}/papers/${paper.paper_id}/detail?${params.toString()}`
    )
    if (!res.ok) throw new Error('無法取得文獻詳情')
    selectedPaperDetail.value = await res.json()
  } catch (err) {
    console.error('讀取文獻細節失敗:', err)
    alert('無法讀取文獻詳細內容')
    isModalOpen.value = false
  } finally {
    isLoadingModal.value = false
  }
}

const closeModal = () => {
  isModalOpen.value = false
  selectedPaperDetail.value = null
}

// 7. 點擊『執行統合分析』-> 算分 + LLM 生成報告 -> 跳轉至 MetaAnalysis 頁面
const goToMetaAnalysis = async () => {
  isRunningAnalysis.value = true
  try {
    const res = await fetch(`${API_BASE_URL}/review/${evaluationId.value}/analyze`, {
      method: 'POST'
    })
    if (!res.ok) throw new Error('統合分析執行失敗')
    router.push({ path: '/meta', query: { eval_id: evaluationId.value } })
  } catch (err) {
    console.error('執行統合分析失敗:', err)
    alert('執行統合分析失敗，請確認後端服務與 GEMINI_API_KEY 設定！')
  } finally {
    isRunningAnalysis.value = false
  }
}

// 頁面初始化載入：若發現評估單尚在 RETRIEVING 狀態，啟動每 1.5 秒輪詢一次，逐一點亮 KCC！
onMounted(async () => {
  await fetchKccSummary(true)
  if (isCurrentKccReady.value) {
    await fetchKccPapers()
  }
  if (evalStatus.value === 'RETRIEVING') {
    summaryPollTimer = setInterval(() => {
      fetchKccSummary(false)
    }, 1500)
  }
})

onUnmounted(() => {
  if (summaryPollTimer) clearInterval(summaryPollTimer)
})
</script>

<style scoped>
/* 1. 調小上方 margin (從 40px 改為 20px)，讓大標題更靠近導覽列 */
.review-page {
  max-width: 1200px;
  margin: 20px auto 40px auto;
  padding: 0 20px;
}

.page-header {
  margin-bottom: 18px;
}

.main-title {
  color: #1b1e29;
  font-size: 38px;
  margin-top: 4px;
  margin-bottom: 20px;
  font-weight: 900;
  letter-spacing: 1.5px;
  text-shadow: 
    1px 1px 0px #f6d32d,
    2px 2px 0px #f6d32d,
    3px 3px 0px #e25740,
    4px 4px 0px #f6d32d;
}

.title-en {
  color: #e74c3c;
}

.content-layout {
  display: flex;
  gap: 32px;
  align-items: flex-start;
}

/* 左側面板樣式 */
.sidebar-filter {
  width: 265px;
  background-color: #ffffff;
  border: 1px solid #ffffff;
  border-radius: 24px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04);
  flex-shrink: 0;
}

/* 2 & 3. 進階篩選標題重新設計，並與前方「!」按鈕完美水平對齊 */
.section-header-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 14px;
  border-bottom: 2px solid var(--light-color);
}

.info-btn {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: 1.5px solid var(--dark-color);
  background-color: var(--light-color);
  color: var(--dark-color);
  font-weight: 900;
  font-size: 14px;
  cursor: help;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  padding: 0;
}

.header-text-group {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.header-zh {
  font-size: 20px;
  font-weight: 800;
  color: #2c3e50;
  letter-spacing: 0.5px;
  padding: 3px;
}

.header-en {
  font-size: 14px;
  font-weight: 800;
  color: var(--dark-color);
  letter-spacing: 1px;
}

.filter-group label {
  display: block;
  margin-bottom: 8px;
  color: #444;
  font-weight: bold;
  font-size: 14.5px;
  padding: 4px;
}

.inline-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
}

.input-text {
  font-size: 14px;
  color: #555;
  white-space: nowrap;
}

.short-input {
  width: 56px;
  border: 1px solid var(--dark-color);
  border-radius: 6px;
  padding: 6px 8px;
  background-color: transparent;
  text-align: center;
  font-weight: bold;
  color: #333;
  outline: none;
}

.short-input:focus {
  border-color: var(--primary-color);
}

.chip-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip-btn {
  background-color: #ffffff;
  color: #555;
  border: 1px solid #ccc;
  padding: 6px 14px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.2s;
}

.chip-btn:hover:not(:disabled) {
  border-color: var(--dark-color);
}

.chip-btn.active {
  background-color: var(--dark-color);
  color: var(--white);
  border-color: var(--dark-color);
}

/* 左側底部雙按鈕：左邊『重新載入』、右邊『送出篩選』 */
.filter-action-row {
  display: flex;
  gap: 10px;
  margin-top: 6px;
}

.action-btn {
  background-color: var(--dark-color);
  color: #ffffff;
  border: 1px solid var(--dark-color);
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.action-btn.reload-btn {
  flex: 1;
  background-color: #ffffff;
  color: var(--dark-color);
  border: 1.5px solid var(--dark-color);
}

.action-btn.reload-btn:hover:not(:disabled) {
  background-color: var(--light-color);
}

.action-btn.apply-filter {
  flex: 1.2;
  background-color: var(--dark-color);
  color: #ffffff;
}

.action-btn.submit-analysis {
  background-color: #1a1e29;
  color: var(--white);
  border-color: #1a1e29;
  padding: 12px 28px;
  font-size: 15px;
}

.action-btn.submit-analysis:hover:not(:disabled) {
  background-color: #1a1e29;
}

.action-btn:active:not(:disabled) {
  opacity: 0.75;
  transform: scale(0.96);
  transition: all 0.1s ease;
}

/* 右側區域樣式 */
.evidence-pool-section {
  flex: 1;
  min-width: 0;
}

.pool-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

/* 2. 證據池 KC EVALUATION EVIDENCE 標題視覺升級 */
.pool-title-banner {
  display: flex;
  align-items: baseline;
  gap: 12px;
  border-left: 5px solid var(--dark-color);
  padding-left: 14px; 
  flex-wrap: wrap;
}

.banner-zh {
  font-size: 22px;
  font-weight: 900;
  color: #2c3e50;
  letter-spacing: 0.5px;
}

.banner-en {
  font-size: 18px;
  font-weight: 800;
  color: var(--dark-color);
  letter-spacing: 1.2px;
  text-align:end;
}

/* 頂部進度提示膠囊與全數完成徽章 */
.retrieving-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background-color: #1b1e29;
  color: #f6d32d;
  font-size: 13px;
  font-weight: 700;
  padding: 5px 14px;
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #f6d32d;
  animation: dotPulse 1s infinite ease-in-out;
}

@keyframes dotPulse {
  0%, 100% { transform: scale(0.8); opacity: 0.5; }
  50% { transform: scale(1.3); opacity: 1; }
}

.all-ready-pill {
  display: inline-flex;
  align-items: center;
  background: linear-gradient(135deg, #e6fcf5 0%, #c3fae8 100%);
  color: #087f5b;
  border: 1px solid #63e6be;
  font-size: 13px;
  font-weight: 800;
  padding: 5px 14px;
  border-radius: 20px;
}

/* 10 KCC 按鈕網格 */
.kcc-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.kcc-btn {
  position: relative;
  background-color: #ffffff;
  border: 1.5px solid #ffffff;
  border-radius: 10px;
  padding: 10px 8px;
  text-align: center;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.28s cubic-bezier(0.25, 0.8, 0.25, 1);
  font-weight: 800;
  color: #555;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
  overflow: hidden;
}

.kcc-btn:hover:not(:disabled) {
  border-color: var(--primary-color);
  transform: translateY(-1px);
}

.kcc-btn.active {
  background-color: var(--dark-color);
  color: var(--white);
  border-color: var(--dark-color);
}

/* 狀態 A：反灰未就緒 (待檢索) */
.kcc-btn.kcc-pending {
  background-color: #e2e8f0;
  border-color: #cbd5e1;
  color: #94a3b8;
  cursor: not-allowed;
  box-shadow: none;
}

/* 狀態 B：目前正輪到該 KC 執行檢索與重排 (流光掃描呼吸特效) */
.kcc-btn.kcc-processing {
  background: linear-gradient(110deg, #e2e8f0 25%, #f8fafc 50%, #e2e8f0 75%);
  background-size: 200% 100%;
  animation: shimmerScan 1.5s infinite linear;
  border: 1.5px dashed var(--dark-color);
  color: #475569;
  cursor: wait;
}

@keyframes shimmerScan {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* 狀態 C：資料準備完成瞬間的「無到有」立體彈跳與光暈擴散特效 */
.kcc-btn.kcc-just-ready {
  animation: kccReadyPop 0.9s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  border-color: #10b981 !important;
}

@keyframes kccReadyPop {
  0% {
    transform: scale(0.88);
    background-color: #d1fae5;
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
  }
  50% {
    transform: scale(1.06);
    box-shadow: 0 0 0 12px rgba(16, 185, 129, 0);
  }
  100% {
    transform: scale(1);
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  }
}

.just-ready-badge {
  position: absolute;
  top: 3px;
  right: 5px;
  font-size: 9.5px;
  font-weight: 900;
  color: #059669;
  background-color: #d1fae5;
  padding: 1px 5px;
  border-radius: 6px;
  letter-spacing: 0.3px;
}

.kcc-count {
  font-size: 12.5px;
  display: inline-block;
  margin-top: 2px;
}

.count-pop {
  animation: numberPopIn 0.35s ease-out;
}

@keyframes numberPopIn {
  0% { opacity: 0; transform: translateY(5px) scale(0.8); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}

.kcc-status-text {
  font-size: 11.5px;
  display: inline-block;
  margin-top: 3px;
  font-weight: 700;
}

.processing-text {
  color: var(--dark-color);
}

.pending-text {
  color: #94a3b8;
}

.list-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.list-title {
  margin: 0;
  font-size: 18px;
  color: #333;
  font-weight: 800;
}

.list-contents {
  font-size: 18px;
  font-weight: 800;
  color: var(--dark-color);
  letter-spacing: 1px;
}

.sort-options {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #555;
  font-weight: bold;
}

.paper-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 文獻列表無到有滑入動畫 */
.paper-fade-enter-active {
  transition: all 0.35s ease-out;
}
.paper-fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.retrieving-list-box {
  background-color: rgba(255, 255, 255, 0.8);
  border: 1.5px dashed var(--dark-color);
  border-radius: 14px;
  padding: 44px 24px;
  text-align: center;
  color: #334155;
  font-weight: bold;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
}

.spinner-ring {
  width: 32px;
  height: 32px;
  border: 3.5px solid #cbd5e1;
  border-top-color: var(--dark-color);
  border-radius: 50%;
  animation: spinRing 0.85s infinite linear;
}

@keyframes spinRing {
  to { transform: rotate(360deg); }
}

.empty-list-box {
  background-color: rgba(255, 255, 255, 0.7);
  border: 1px dashed var(--dark-color);
  border-radius: 12px;
  padding: 36px 20px;
  text-align: center;
  color: #555;
  font-weight: bold;
}

/* 4. 融合版面配色的頁碼列 (« 首頁 01 02 03 最後 ») */
.pagination-bar {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  margin-top: 28px;
  padding: 10px 20px;
  background-color: rgba(255, 255, 255, 0.65);
  border-radius: 14px;
  width: fit-content;
  margin-left: auto;
  margin-right: auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.page-nav-btn,
.page-num-btn {
  background-color: transparent;
  border: none;
  color: #4a5568;
  font-size: 14.5px;
  font-weight: 800;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-nav-btn:hover:not(:disabled),
.page-num-btn:hover:not(.active) {
  background-color: var(--light-color);
  color: var(--dark-color);
}

.page-num-btn.active {
  background-color: var(--dark-color);
  color: #ffffff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.page-nav-btn:disabled {
  color: #b0bec5;
  cursor: not-allowed;
}
</style>