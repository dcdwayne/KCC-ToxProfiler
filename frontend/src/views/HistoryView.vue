<template>
  <main class="history-page">
    <!-- 頂部大標題 -->
    <header class="page-header">
      <h2 class="main-title">
        {{ isEn ? 'Historical Records' : '歷史紀錄管理' }}
        <span v-if="!isEn" class="title-en">Historical Records</span>
      </h2>
    </header>

    <section class="panel-container">
      <!-- 1. 基本篩選條件區塊 (與帳號管理頁面風格完全同步) -->
      <div class="filter-card">
        <div class="filter-card-header">
          <div class="pool-title-banner">
            <span class="banner-zh">{{ t('基本篩選條件', 'History Filter') }}</span>
            <span v-if="!isEn" class="banner-en">HISTORY FILTER</span>
          </div>
          <div class="filter-btn-group">
            <button class="btn-outline" @click="resetFilters">{{ t('重置條件', 'Reset') }}</button>
            <button class="btn-solid" @click="applyFilters">{{ t('執行篩選', 'Apply Filter') }}</button>
          </div>
        </div>

        <div class="filter-grid">
          <!-- 化學物質名稱或 CAS 搜尋 -->
          <div class="filter-item">
            <label>{{ t('化學物質名稱 / CAS 號碼', 'Chemical Name / CAS RN') }}</label>
            <input
              type="text"
              v-model.trim="filters.keyword"
              :placeholder="t('輸入如 DEHP、PFOA 或 CAS 號碼...', 'e.g., DEHP, PFOA, or CAS RN...')"
              class="text-input"
              @keyup.enter="applyFilters"
            />
          </div>

          <!-- 危害等級篩選 -->
          <div class="filter-item">
            <label>{{ t('危害等級 Hazard Level', 'Hazard Level') }}</label>
            <select v-model="filters.risk_level" class="select-input" @change="applyFilters">
              <option value="ALL">{{ t('全部等級 (All Levels)', 'All Levels') }}</option>
              <option value="HIGH RISK">{{ t('高危害 HIGH RISK (≥70)', 'HIGH RISK (≥70)') }}</option>
              <option value="MODERATE RISK">{{ t('中度危害 MODERATE RISK (40~69)', 'MODERATE RISK (40~69)') }}</option>
              <option value="LOW RISK">{{ t('低度危害 LOW RISK (<40)', 'LOW RISK (<40)') }}</option>
              <option value="UNSCORED">{{ t('尚未算分 UNSCORED', 'UNSCORED') }}</option>
            </select>
          </div>

          <!-- 評估狀態篩選 -->
          <div class="filter-item">
            <label>{{ t('評估狀態 Evaluation Status', 'Evaluation Status') }}</label>
            <select v-model="filters.status" class="select-input" @change="applyFilters">
              <option value="ALL">{{ t('全部狀態 (All Status)', 'All Status') }}</option>
              <option value="COMPLETED">{{ t('已完成 (COMPLETED)', 'COMPLETED') }}</option>
              <option value="GENERATING">{{ t('報告生成中 (GENERATING_*)', 'GENERATING_*') }}</option>
              <option value="REVIEWING">{{ t('文獻回顧中 (REVIEWING)', 'REVIEWING') }}</option>
              <option value="RETRIEVING">{{ t('檢索配對中 (RETRIEVING)', 'RETRIEVING') }}</option>
            </select>
          </div>

          <!-- FastMCP 知識庫勾選狀態篩選 -->
          <div class="filter-item">
            <label>{{ t('AI 知識庫綁定 (FastMCP)', 'AI Knowledge Binding (FastMCP)') }}</label>
            <select v-model="filters.mcp_selected" class="select-input" @change="applyFilters">
              <option value="ALL">{{ t('全部紀錄 (All Records)', 'All Records') }}</option>
              <option value="SELECTED">{{ t('✓ 已勾選綁定 (Selected)', '✓ Bound (Selected)') }}</option>
              <option value="UNSELECTED">{{ t('○ 未勾選 (Unselected)', '○ Unbound (Unselected)') }}</option>
            </select>
          </div>
        </div>
      </div>

      <!-- 2. 資料筆數統計列 & 多選組合排序控制列 -->
      <div class="summary-bar">
        <div class="summary-left">
          <button class="info-btn" :title="t('點擊查看使用說明', 'Click to view user guide')" @click="isGuideOpen = true">!</button>
          <span v-if="!isEn" class="summary-title">
            危害辨識評估歷史紀錄：共 <strong class="highlight-num">{{ filteredRecords.length }}</strong> 筆資料
            （共 <strong class="highlight-num">{{ totalPages }}</strong> 頁，目前位於第 <strong>{{ currentPage }}</strong> 頁）
          </span>
          <span v-else class="summary-title">
            Historical Evaluations: <strong class="highlight-num">{{ filteredRecords.length }}</strong> records
            (Page <strong>{{ currentPage }}</strong> of <strong class="highlight-num">{{ totalPages }}</strong>)
          </span>
        </div>

        <!-- 排序按鈕區：支援多選組合排序 (新增『評估時間』由近到遠) -->
        <div class="sort-options">
          <span>{{ t('排序：', 'Sort by:') }}</span>
          <button 
            v-for="opt in sortOptions" 
            :key="opt.key"
            class="chip-btn small"
            :class="{ active: activeSorts.includes(opt.key) }"
            @click="toggleSort(opt.key)"
            :title="t('可多選組合排序（依點選先後決定主次順序）', 'Multi-sort supported (in order of selection)')"
          >
            {{ isEn ? opt.labelEn : opt.label }}
            <span v-if="activeSorts.includes(opt.key)" class="sort-order-num">
              {{ activeSorts.indexOf(opt.key) + 1 }}
            </span>
          </button>
        </div>
      </div>

      <!-- 3. 歷史紀錄表格 (具明確欄位名稱，與帳號管理頁面一致) -->
      <div v-if="isLoading" class="empty-box">
        {{ t('正在載入歷史評估紀錄...', 'Loading historical evaluation records...') }}
      </div>

      <div v-else-if="paginatedRecords.length > 0" class="table-wrapper">
        <table class="tox-table">
          <thead>
            <tr>
              <th style="width: 130px; text-align: center;">{{ t('AI 知識庫綁定', 'FastMCP Bind') }}</th>
              <th style="width: 56px; text-align: center;">#</th>
              <th style="min-width: 210px;">{{ t('化學物質名稱 (CAS 號碼)', 'Chemical Name (CAS RN)') }}</th>
              <th style="width: 185px; text-align: center;">{{ t('危害等級 (危害分數)', 'Hazard Level (Score)') }}</th>
              <th style="width: 175px; text-align: center;">{{ t('評估狀態', 'Status') }}</th>
              <th style="width: 185px; text-align: center;">{{ t('評估時間 (台灣時區)', 'Created Time (UTC+8)') }}</th>
              <th style="width: 145px; text-align: center;">{{ t('操作 (成果 / 刪除)', 'Actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(rec, idx) in paginatedRecords"
              :key="rec.id"
              :class="{ 'selected-row': rec.is_selected }"
            >
              <!-- 1. 勾選綁定按鈕 (單一化學物質互斥勾選) -->
              <td class="text-center">
                <label
                  class="checkbox-wrapper"
                  :title="t('勾選作為 Dr. Manhattan (FastMCP) 回答此化學物質之代表紀錄（每種化學物質限選一筆）', 'Bind as representative record for Dr. Manhattan (1 per chemical)')"
                >
                  <input
                    type="checkbox"
                    :checked="rec.is_selected"
                    @change="handleToggleSelect(rec)"
                  />
                  <span class="mcp-tag" :class="{ active: rec.is_selected }">
                    {{ rec.is_selected ? t('已綁定', 'Bound') : t('未選', 'Unbound') }}
                  </span>
                </label>
              </td>

              <!-- 2. 序號 -->
              <td class="text-center cell-index">
                {{ (currentPage - 1) * ITEMS_PER_PAGE + idx + 1 }}.
              </td>

              <!-- 3. 化學物質名稱與 CAS 編號 -->
              <td>
                <div class="chem-main-info">
                  <span class="chem-name">{{ rec.chemical_name }}</span>
                </div>
                <div class="chem-sub-info">
                  <span>CAS RN: <code>{{ rec.cas_number || '--' }}</code></span>
                  <span>｜ {{ t('評估單號:', 'Eval ID:') }} #{{ rec.id }}</span>
                </div>
              </td>

              <!-- 4. 危害等級 (危害分數)：仿照 Meta 儀表板 紅/黃/灰 設計 -->
              <td class="text-center">
                <span class="hazard-badge" :class="getHazardClass(rec.risk_level, rec.hazard_score)">
                  <template v-if="rec.hazard_score !== null && rec.hazard_score !== undefined">
                    {{ rec.risk_level }} ({{ rec.hazard_score }})
                  </template>
                  <template v-else>
                    UNSCORED (--)
                  </template>
                </span>
              </td>

              <!-- 5. 評估狀態：仿照 Review 頁面 期刊排名 (Q1/Q2/Q3) 設計 -->
              <td class="text-center">
                <span class="status-badge" :class="getStatusClass(rec.status)">
                  {{ rec.status }}
                </span>
              </td>

              <!-- 6. 製作時間 (已轉換為台灣時區 UTC+8) -->
              <td class="text-center time-cell">
                <strong>{{ rec.created_at_tw }}</strong>
              </td>

              <!-- 7. 操作：導向 Meta 評估成果頁按鈕 + 刪除叉叉按鈕 -->
              <td class="text-center">
                <div class="action-icon-group">
                  <button
                    class="meta-link-btn"
                    @click="handleGoToMeta(rec)"
                    :title="t('前往 Meta-analysis 頁面查看評估成果與報告', 'Open Meta-analysis dashboard & reports')"
                  >
                    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                      <polyline points="15 3 21 3 21 9" />
                      <line x1="10" y1="14" x2="21" y2="3" />
                    </svg>
                  </button>

                  <button
                    class="delete-btn"
                    @click="openDeleteModal(rec)"
                    :title="t('刪除此筆評估紀錄與相關證據資料', 'Delete this evaluation record and linked evidence')"
                  >
                    X
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else class="empty-box">
        {{ t('目前篩選條件下尚無符合的危害辨識評估歷史紀錄。', 'No historical evaluation records match the current filter criteria.') }}
      </div>

      <!-- 4. 頁碼點擊功能：« 首頁 01 02 03 最後 » -->
      <div class="pagination-bar" v-if="totalPages > 1">
        <button 
          class="page-nav-btn" 
          :disabled="currentPage === 1"
          @click="goToPage(1)"
        >
          {{ t('« 首頁', '« First') }}
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
          {{ t('最後 »', 'Last »') }}
        </button>
      </div>
    </section>

    <!-- ================= 刪除確認警告彈出視窗 ================= -->
    <transition name="modal-fade">
      <div v-if="isDeleteModalOpen && recordToDelete" class="warn-overlay" @click.self="closeDeleteModal">
        <div class="warn-modal">
          <!-- 頂部警示標題列 -->
          <header class="warn-header">
            <div class="warn-title-group">
              <span class="warn-icon">!</span>
              <div>
                <span class="warn-subtitle">{{ t('DELETION WARNING / 刪除確認', 'DELETION WARNING') }}</span>
                <h3 class="warn-title">{{ t('確定要永久刪除此筆評估紀錄嗎？', 'Permanently delete this evaluation record?') }}</h3>
              </div>
            </div>
            <button class="close-btn" @click="closeDeleteModal" :title="t('取消並關閉', 'Cancel & Close')">✕</button>
          </header>

          <!-- 警告內容說明區 -->
          <div class="warn-body">
            <!-- 欲刪除的目標摘要卡 -->
            <div class="target-summary-card">
              <div class="summary-item">
                <span class="s-label">{{ t('目標化學物質：', 'Target Chemical: ') }}</span>
                <strong class="s-value">{{ recordToDelete.chemical_name }} (Evaluation #{{ recordToDelete.id }})</strong>
              </div>
              <div class="summary-item">
                <span class="s-label">{{ t('危害評級與時間：', 'Hazard Level & Time: ') }}</span>
                <span class="s-value">
                  {{ recordToDelete.hazard_score !== null ? `${recordToDelete.risk_level} (${recordToDelete.hazard_score})` : 'UNSCORED' }}
                  ｜ {{ recordToDelete.created_at_tw }}
                </span>
              </div>
            </div>

            <!-- 若該筆紀錄已被勾選為 FastMCP 資料源，顯示特別提醒 -->
            <div v-if="recordToDelete.is_selected" class="mcp-active-alert">
              <template v-if="!isEn">
                ⚠️ <strong>特別注意：</strong>此筆紀錄目前已勾選為 <strong>FastMCP 外部問答知識庫</strong> 之代表資料，刪除後 AI 助手將無法再引用此評估結果回答問題！
              </template>
              <template v-else>
                ⚠️ <strong>Warning:</strong> This record is currently bound to the <strong>FastMCP AI Knowledge Base</strong>. Deleting it will remove it from Dr. Manhattan's active knowledge source!
              </template>
            </div>

            <p class="consequence-lead">
              {{ t('執行刪除將會連帶執行以下操作，且無法復原：', 'Deleting this record will permanently perform the following actions:') }}
            </p>
            <ul v-if="!isEn" class="consequence-list">
              <li>
                <strong>刪除統合分析成果 (<code>evaluations</code> 資料表)</strong>：永久移除此紀錄的 10 KCC 證據權重分數、總體危害分數以及 AI 生成之「民眾版」與「專家版」報告。
              </li>
              <li>
                <strong>清除關聯文獻證據池 (<code>evaluation_evidence</code> 資料表)</strong>：同步清除此評估單號下所有經由 RAG 召回、Cross-Encoder 重排與專家人工精鍊保留的文獻配對紀錄。
              </li>
              <li>
                <strong>不影響原始文獻庫</strong>：<code>papers</code> 與 <code>chunks</code> 資料表中的 PubMed 原始文獻與向量索引仍會保留，未來可隨時重新發起評估。
              </li>
            </ul>
            <ul v-else class="consequence-list">
              <li>
                <strong>Delete Meta-Analysis Results (<code>evaluations</code> table)</strong>: Permanently removes the 10 KCC scores, Hazard Score, and AI-generated Public & Expert reports.
              </li>
              <li>
                <strong>Clear Linked Evidence Pool (<code>evaluation_evidence</code> table)</strong>: Removes all RAG-recalled and curated paper matches associated with this evaluation ID.
              </li>
              <li>
                <strong>Preserves Raw Literature</strong>: Original PubMed papers and vector embeddings in <code>papers</code> and <code>chunks</code> remain intact for future evaluations.
              </li>
            </ul>
          </div>

          <!-- 底部操作按鈕 -->
          <footer class="warn-footer">
            <button class="cancel-btn" :disabled="isDeleting" @click="closeDeleteModal">
              {{ t('取消保留', 'Cancel') }}
            </button>
            <button class="confirm-delete-btn" :disabled="isDeleting" @click="confirmDeleteRecord">
              {{ isDeleting ? t('正在刪除紀錄...', 'Deleting...') : t('確認永久刪除', 'Confirm Delete') }}
            </button>
          </footer>
        </div>
      </div>
    </transition>

    <!-- 共用使用說明彈出視窗 (傳入 page="history") -->
    <InfoGuideModal 
      :isOpen="isGuideOpen" 
      page="history" 
      @close="isGuideOpen = false" 
    />
  </main>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import InfoGuideModal from '../components/InfoGuideModal.vue'
import { isEn, t } from '../utils/i18nStore'

const isGuideOpen = ref(false)
const router = useRouter()

// 若在本地 npm run dev (Port 5173) 則連 8000，若在 Nginx 正式環境 (Port 80) 則走相對路徑 '/api'
const API_BASE_URL = window.location.port === '5173'
  ? `http://${window.location.hostname}:8000/api`
  : '/api'

// =====================================================================
// 👇👇👇 【每頁顯示歷史紀錄筆數設定】預設為 8 筆，可隨時在此手動調整 👇👇👇
// =====================================================================
const ITEMS_PER_PAGE = 8

const records = ref([])
const isLoading = ref(false)
const currentPage = ref(1)

// 基本篩選條件狀態
const filters = reactive({
  keyword: '',
  risk_level: 'ALL',
  status: 'ALL',
  mcp_selected: 'ALL'
})

// 多選排序狀態陣列 (依點擊順序存放 'chemical' | 'hazard' | 'status' | 'time')
const activeSorts = ref([])
const sortOptions = [
  { key: 'chemical', label: '化學物質名稱', labelEn: 'Chemical' },
  { key: 'hazard', label: '危害等級', labelEn: 'Hazard Level' },
  { key: 'status', label: '狀態', labelEn: 'Status' },
  { key: 'time', label: '評估時間', labelEn: 'Eval Time' }
]

// 刪除警告視窗狀態
const isDeleteModalOpen = ref(false)
const recordToDelete = ref(null)
const isDeleting = ref(false)

// --- 依據基本篩選條件過濾紀錄 ---
const filteredRecords = computed(() => {
  return records.value.filter(rec => {
    // 1. 關鍵字過濾 (化學物質名稱或 CAS 號碼)
    const kw = filters.keyword.toLowerCase()
    if (kw) {
      const matchName = (rec.chemical_name || '').toLowerCase().includes(kw)
      const matchCas = (rec.cas_number || '').toLowerCase().includes(kw)
      if (!matchName && !matchCas) return false
    }

    // 2. 危害等級過濾
    if (filters.risk_level !== 'ALL') {
      if (filters.risk_level === 'UNSCORED') {
        if (rec.hazard_score !== null && rec.hazard_score !== undefined) return false
      } else {
        if (rec.risk_level !== filters.risk_level || rec.hazard_score === null) return false
      }
    }

    // 3. 評估狀態過濾
    if (filters.status !== 'ALL') {
      if (filters.status === 'GENERATING') {
        if (!rec.status || !rec.status.startsWith('GENERATING')) return false
      } else {
        if (rec.status !== filters.status) return false
      }
    }

    // 4. FastMCP 勾選綁定狀態過濾
    if (filters.mcp_selected === 'SELECTED' && !rec.is_selected) return false
    if (filters.mcp_selected === 'UNSELECTED' && rec.is_selected) return false

    return true
  })
})

// --- 分頁計算邏輯 ---
const totalPages = computed(() => {
  return Math.max(1, Math.ceil(filteredRecords.value.length / ITEMS_PER_PAGE))
})

const paginatedRecords = computed(() => {
  const start = (currentPage.value - 1) * ITEMS_PER_PAGE
  return filteredRecords.value.slice(start, start + ITEMS_PER_PAGE)
})

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

// 觸發篩選與重置篩選
const applyFilters = () => {
  currentPage.value = 1
}

const resetFilters = () => {
  filters.keyword = ''
  filters.risk_level = 'ALL'
  filters.status = 'ALL'
  filters.mcp_selected = 'ALL'
  currentPage.value = 1
}

// --- 標籤配色輔助函式 ---
const getHazardClass = (riskLevel, score) => {
  if (score === null || score === undefined) return 'hazard-unscored'
  if (riskLevel === 'HIGH RISK') return 'hazard-high'
  if (riskLevel === 'MODERATE RISK') return 'hazard-moderate'
  return 'hazard-low'
}

const getStatusClass = (status) => {
  if (status === 'COMPLETED') return 'status-completed'
  if (status && status.startsWith('GENERATING')) return 'status-generating'
  if (status === 'REVIEWING') return 'status-reviewing'
  return 'status-retrieving'
}

// --- API 1: 取得歷史紀錄列表 (支援多選排序) ---
const fetchHistoryRecords = async () => {
  isLoading.value = true
  try {
    const params = new URLSearchParams()
    if (activeSorts.value.length > 0) {
      params.set('sort_by', activeSorts.value.join(','))
    }
    const queryStr = params.toString() ? `?${params.toString()}` : ''
    const res = await fetch(`${API_BASE_URL}/history${queryStr}`)
    if (!res.ok) throw new Error('無法取得歷史紀錄')
    const data = await res.json()
    records.value = data.records || []
  } catch (err) {
    console.error('載入歷史紀錄失敗:', err)
  } finally {
    isLoading.value = false
  }
}

// 點擊多選排序按鈕
const toggleSort = async (sortKey) => {
  const idx = activeSorts.value.indexOf(sortKey)
  if (idx > -1) {
    activeSorts.value.splice(idx, 1)
  } else {
    activeSorts.value.push(sortKey)
  }
  currentPage.value = 1
  await fetchHistoryRecords()
}

// --- API 2: 勾選/取消勾選紀錄 (同一個化學物質僅限勾選一筆) ---
const handleToggleSelect = async (record) => {
  const newSelectedState = !record.is_selected
  try {
    const res = await fetch(`${API_BASE_URL}/history/${record.id}/select`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_selected: newSelectedState })
    })
    if (!res.ok) throw new Error('更新勾選狀態失敗')

    // 前端即時同步：若勾選為 True，將同一個 cas_number 的其他紀錄自動取消勾選
    records.value.forEach(item => {
      if (item.id === record.id) {
        item.is_selected = newSelectedState
      } else if (newSelectedState && item.cas_number === record.cas_number) {
        item.is_selected = false
      }
    })
  } catch (err) {
    console.error('切換勾選失敗:', err)
    alert(t('無法更新勾選狀態，請確認後端連線！', 'Failed to update selection state!'))
  }
}

// --- 導向該筆評估紀錄的 Meta-analysis 頁面 ---
const handleGoToMeta = (record) => {
  localStorage.setItem('current_evaluation_id', record.id)
  router.push({ path: '/meta', query: { eval_id: record.id } })
}

// --- 開啟 / 關閉刪除確認警告視窗 ---
const openDeleteModal = (record) => {
  recordToDelete.value = record
  isDeleteModalOpen.value = true
}

const closeDeleteModal = () => {
  if (isDeleting.value) return
  isDeleteModalOpen.value = false
  recordToDelete.value = null
}

// --- API 3: 確認執行刪除單筆紀錄 (同步刪除 evaluations 與 evaluation_evidence) ---
const confirmDeleteRecord = async () => {
  if (!recordToDelete.value) return
  isDeleting.value = true
  const targetId = recordToDelete.value.id

  try {
    const res = await fetch(`${API_BASE_URL}/history/${targetId}`, {
      method: 'DELETE'
    })
    if (!res.ok) throw new Error('刪除紀錄失敗')

    records.value = records.value.filter(r => r.id !== targetId)

    // 若刪除後當前頁已空且不在第一頁，自動退回上一頁
    if (paginatedRecords.value.length === 0 && currentPage.value > 1) {
      currentPage.value--
    }
    isDeleteModalOpen.value = false
    recordToDelete.value = null
  } catch (err) {
    console.error('刪除評估紀錄失敗:', err)
    alert(t('刪除失敗，請稍後再試！', 'Failed to delete record. Please try again later!'))
  } finally {
    isDeleting.value = false
  }
}

onMounted(() => {
  fetchHistoryRecords()
})
</script>

<style scoped>
.history-page {
  width: 100%;
  max-width: 1220px;
  margin: 20px auto 40px auto;
  padding: 0 20px;
}

.page-header {
  margin-bottom: 18px;
}

/* 保留你設定的白字黑邊立體標題風格 */
.main-title {
  color: white;
  font-size: 36px;
  margin-top: 0px;
  margin-bottom: 0px;
  font-weight: 900;
  letter-spacing: 1.5px;
  text-shadow: 
    -2px -2px 0 #000,  /* 左上 */
    0   -2px 0 #000,  /* 正上 */
    2px -2px 0 #000,  /* 右上 */
    2px  0   0 #000,  /* 正右 */
    2px  2px 0 #000,  /* 右下 */
    0    2px 0 #000,  /* 正下 */
    -2px  2px 0 #000,  /* 左下 */
    -2px  0   0 #000;  /* 正左 */
}

.title-en {
  color: white;
  font-weight: 900;
}

/* ================= 1. 基本篩選條件卡片 (同步帳號管理頁面風格) ================= */
.filter-card {
  background-color: #ffffff;
  border-radius: 18px;
  padding: 20px 24px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04);
  margin-bottom: 18px;
  border: 1px solid #ffffff;
}

.filter-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid var(--light-color);
  flex-wrap: wrap;
  gap: 10px;
}

.pool-title-banner {
  display: flex;
  align-items: baseline;
  gap: 10px;
  border-left: 5px solid var(--dark-color);
  padding-left: 12px;
}

.banner-zh { font-size: 19px; font-weight: 900; color: #2c3e50; }
.banner-en { font-size: 13px; font-weight: 800; color: var(--dark-color); letter-spacing: 1px; }

.filter-btn-group { display: flex; gap: 10px; }

.btn-outline {
  background-color: #ffffff; color: var(--dark-color);
  border: 1.5px solid var(--dark-color); padding: 7px 18px;
  border-radius: 8px; font-weight: 800; font-size: 14px;
  cursor: pointer; transition: all 0.2s;
}
.btn-outline:hover { background-color: var(--light-color); }

.btn-solid {
  background-color: #1b1e29; color: #ffffff;
  border: 1.5px solid #1b1e29; padding: 7px 22px;
  border-radius: 8px; font-weight: 800; font-size: 14px;
  cursor: pointer; transition: all 0.2s;
}
.btn-solid:hover { background-color: var(--dark-color); border-color: var(--dark-color); }

.filter-grid { display: grid; grid-template-columns: 1.3fr 1fr 1fr 1fr; gap: 14px; }
.filter-item { display: flex; flex-direction: column; gap: 6px; }
.filter-item label { font-size: 13px; font-weight: 800; color: #475569; }

.text-input, .select-input {
  padding: 8px 12px; border: 1.5px solid #cbd5e1;
  border-radius: 8px; font-size: 14px; font-weight: 700;
  color: #1e293b; background-color: #f8fafc;
  outline: none; transition: all 0.2s;
}
.text-input:focus, .select-input:focus { border-color: var(--dark-color); background-color: #ffffff; }

/* ================= 2. 統計資訊與多選排序列 ================= */
.summary-bar {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 14px; padding: 0 4px; flex-wrap: wrap; gap: 12px;
}
.summary-left { display: flex; align-items: center; gap: 10px; }

.info-btn {
  width: 30px; height: 30px; border-radius: 50%;
  border: 1.5px solid var(--dark-color); background-color: var(--light-color);
  color: var(--dark-color); font-weight: 900; font-size: 14px;
  cursor: pointer; display: inline-flex; align-items: center;
  justify-content: center; flex-shrink: 0; padding: 0; transition: all 0.2s ease;
}
.info-btn:hover { background-color: var(--dark-color); color: #ffffff; transform: scale(1.08); }

.summary-title { font-size: 17px; font-weight: 800; color: #2c3e50; }
.highlight-num { color: var(--dark-color); font-size: 19px; font-weight: 900; }

.sort-options { display: flex; align-items: center; gap: 8px; color: #2c3e50; font-weight: 800; font-size: 15px; flex-wrap: wrap; }

.chip-btn {
  background-color: #ffffff; color: #475569;
  border: 1.5px solid #cbd5e1; padding: 6px 14px;
  border-radius: 8px; cursor: pointer; font-weight: 800;
  font-size: 13.5px; transition: all 0.2s ease;
  display: inline-flex; align-items: center; gap: 6px;
}
.chip-btn:hover { border-color: var(--dark-color); color: var(--dark-color); }
.chip-btn.active { background-color: var(--dark-color); border-color: var(--dark-color); color: #ffffff; }

.sort-order-num {
  background-color: rgba(255, 255, 255, 0.25); color: #ffffff;
  font-size: 11px; width: 18px; height: 18px; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
}

/* ================= 3. 表格樣式 (與帳號管理頁面一致) ================= */
.table-wrapper {
  background-color: #ffffff; border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
  overflow-x: auto; border: 1px solid #e2e8f0;
}
.tox-table { width: 100%; border-collapse: collapse; text-align: left; }
.tox-table thead tr { background-color: #1b1e29; color: #ffffff; }
.tox-table th { padding: 13px 16px; font-size: 13.5px; font-weight: 800; letter-spacing: 0.4px; white-space: nowrap; }
.tox-table tbody tr { border-bottom: 1px solid #edf2f7; transition: background-color 0.15s; }
.tox-table tbody tr:hover { background-color: #f8fafc; }
.tox-table tbody tr.selected-row { background-color: #f0fdfa; }
.tox-table td { padding: 13px 16px; vertical-align: middle; font-size: 14px; color: #334155; }
.text-center { text-align: center; }
.cell-index { font-weight: 800; color: #475569; font-size: 15px; }

.checkbox-wrapper { display: inline-flex; align-items: center; gap: 8px; cursor: pointer; user-select: none; white-space: nowrap; }
.checkbox-wrapper input[type="checkbox"] { width: 18px; height: 18px; cursor: pointer; accent-color: var(--dark-color); margin: 0; }
.mcp-tag { font-size: 12px; font-weight: 800; padding: 2px 8px; border-radius: 10px; background-color: #f1f5f9; color: #94a3b8; }
.mcp-tag.active { background-color: #ccfbf1; color: #0f766e; border: 1px solid #5eead4; }

.chem-main-info { margin-bottom: 3px; }
.chem-name { font-size: 16px; font-weight: 900; color: #1b1e29; letter-spacing: 0.4px; }
.chem-sub-info { font-size: 12px; color: #64748b; font-weight: 600; }
.chem-sub-info code { background-color: #f1f5f9; color: #334155; padding: 1px 5px; border-radius: 4px; font-weight: 700; }

.hazard-badge { display: inline-block; padding: 5px 14px; border-radius: 6px; font-size: 13px; font-weight: 800; letter-spacing: 0.4px; min-width: 136px; text-align: center; white-space: nowrap; }
.hazard-high { background-color: #ef5327; color: #ffffff; }
.hazard-moderate { background-color: #ffca28; color: #1b1e29; }
.hazard-low { background-color: #b0bec5; color: #ffffff; }
.hazard-unscored { background-color: #e2e8f0; color: #64748b; }

.status-badge { display: inline-block; padding: 5px 14px; border-radius: 6px; font-size: 12.5px; font-weight: 800; letter-spacing: 0.5px; min-width: 125px; text-align: center; border: 1px solid var(--dark-color); white-space: nowrap; }
.status-completed { background-color: var(--dark-color); color: #ffffff; border-color: var(--dark-color); }
.status-reviewing, .status-generating { background-color: #e0f2f1; color: var(--dark-color); border-color: var(--primary-color); }
.status-retrieving { background-color: #f5f5f5; color: #666666; border-color: #cccccc; }

.time-cell { font-variant-numeric: tabular-nums; font-size: 14px; color: #1b1e29; white-space: nowrap; }
.action-icon-group { display: inline-flex; align-items: center; justify-content: center; gap: 10px; }

.meta-link-btn, .delete-btn {
  width: 32px; height: 32px; border-radius: 50%;
  border: 1.5px solid #64748b; background-color: #ffffff;
  color: #334155; cursor: pointer; display: inline-flex;
  align-items: center; justify-content: center; padding: 0;
  font-weight: 900; font-size: 13px; transition: all 0.2s ease;
}
.meta-link-btn:hover { background-color: var(--dark-color); color: #ffffff; border-color: var(--dark-color); transform: scale(1.08); }
.delete-btn:hover { background-color: #ffebee; color: #c62828; border-color: #c62828; transform: scale(1.08); }

.empty-box { background-color: rgba(255, 255, 255, 0.75); border: 1.5px dashed var(--dark-color); border-radius: 14px; padding: 40px 20px; text-align: center; color: #475569; font-weight: 800; }

/* 融合 Review 版面配色的頁碼列 (« 首頁 01 02 03 最後 ») */
.pagination-bar {
  display: flex; justify-content: center; align-items: center; gap: 8px;
  margin-top: 24px; padding: 10px 20px; background-color: rgba(255, 255, 255, 0.65);
  border-radius: 14px; width: fit-content; margin-left: auto; margin-right: auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}
.page-nav-btn, .page-num-btn { background-color: transparent; border: none; color: #4a5568; font-size: 14.5px; font-weight: 800; padding: 6px 12px; border-radius: 8px; cursor: pointer; transition: all 0.2s ease; }
.page-nav-btn:hover:not(:disabled), .page-num-btn:hover:not(.active) { background-color: var(--light-color); color: var(--dark-color); }
.page-num-btn.active { background-color: var(--dark-color); color: #ffffff; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15); }
.page-nav-btn:disabled { color: #b0bec5; cursor: not-allowed; }

/* ================= 刪除確認警告彈出視窗樣式 ================= */
.warn-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(27, 30, 41, 0.65); backdrop-filter: blur(3px); display: flex; justify-content: center; align-items: center; z-index: 2600; padding: 20px; }
.warn-modal { background-color: #ffffff; width: 95%; max-width: 580px; border-radius: 18px; box-shadow: 0 18px 40px rgba(0, 0, 0, 0.28); overflow: hidden; border: 1px solid #e2e8f0; display: flex; flex-direction: column; }
.warn-header { background-color: #1b1e29; color: #ffffff; padding: 18px 24px; display: flex; justify-content: space-between; align-items: center; border-bottom: 4px solid #e74c3c; }
.warn-title-group { display: flex; align-items: center; gap: 14px; }
.warn-icon { width: 34px; height: 34px; border-radius: 50%; background-color: #e74c3c; color: #ffffff; font-weight: 900; font-size: 19px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.warn-subtitle { font-size: 11px; letter-spacing: 1.2px; color: #fca5a5; font-weight: 800; display: block; }
.warn-title { margin: 2px 0 0 0; font-size: 19px; font-weight: 800; color: #ffffff; }
.close-btn { background: rgba(255, 255, 255, 0.1); border: none; color: #cbd5e1; width: 32px; height: 32px; border-radius: 8px; font-size: 17px; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; justify-content: center; }
.close-btn:hover { background-color: #e74c3c; color: #ffffff; }
.warn-body { padding: 22px 26px; display: flex; flex-direction: column; gap: 14px; }
.target-summary-card { background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 4px solid var(--dark-color); border-radius: 10px; padding: 12px 16px; display: flex; flex-direction: column; gap: 6px; }
.summary-item { font-size: 14.5px; color: #334155; }
.s-label { color: #64748b; font-weight: 700; }
.s-value { color: #1b1e29; font-weight: 800; }
.mcp-active-alert { background-color: #fff5f5; border: 1.5px solid #feb2b2; color: #c53030; padding: 10px 14px; border-radius: 8px; font-size: 13.5px; line-height: 1.5; }
.consequence-lead { margin: 2px 0 0 0; font-size: 14.5px; color: #334155; }
.consequence-list { margin: 0; padding-left: 20px; display: flex; flex-direction: column; gap: 8px; font-size: 14px; line-height: 1.6; color: #475569; }
.consequence-list code { background-color: #f1f5f9; color: #0f172a; padding: 1px 6px; border-radius: 4px; font-weight: 700; }
.warn-footer { padding: 14px 26px; background-color: #f8fafc; border-top: 1px solid #e2e8f0; display: flex; justify-content: flex-end; gap: 12px; }
.cancel-btn { background-color: #ffffff; color: #475569; border: 1.5px solid #cbd5e1; padding: 9px 22px; border-radius: 8px; font-size: 14.5px; font-weight: 800; cursor: pointer; transition: all 0.2s; }
.cancel-btn:hover:not(:disabled) { background-color: #f1f5f9; color: #1e293b; }
.confirm-delete-btn { background-color: #e74c3c; color: #ffffff; border: none; padding: 9px 24px; border-radius: 8px; font-size: 14.5px; font-weight: 800; cursor: pointer; transition: all 0.2s; box-shadow: 0 4px 10px rgba(231, 76, 60, 0.25); }
.confirm-delete-btn:hover:not(:disabled) { background-color: #c0392b; }
.confirm-delete-btn:disabled, .cancel-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity 0.2s ease; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }

/* ================= RWD 響應式設計 ================= */

/* 平板版 (600px ~ 1200px) */
@media screen and (max-width: 1200px) {
  .history-page {
    padding: 0 16px;
  }

  .main-title {
    font-size: 30px;
  }

  .filter-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .summary-bar {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}

/* 手機版 (360px ~ 600px) */
@media screen and (max-width: 600px) {
  .history-page {
    margin: 12px auto 28px auto;
    padding: 0 12px;
  }

  .main-title {
    font-size: 24px;
  }

  .filter-card {
    padding: 16px 14px;
    border-radius: 14px;
  }

  .filter-card-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .filter-btn-group {
    width: 100%;
  }

  .btn-outline,
  .btn-solid {
    flex: 1;
    text-align: center;
  }

  .filter-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .summary-title {
    font-size: 14.5px;
    line-height: 1.45;
  }

  .sort-options {
    font-size: 13.5px;
    gap: 6px;
  }

  .chip-btn {
    padding: 5px 10px;
    font-size: 12.5px;
  }

  .table-wrapper {
    -webkit-overflow-scrolling: touch;
  }

  .warn-body {
    padding: 16px 16px;
  }

  .warn-footer {
    padding: 12px 16px;
  }

  .cancel-btn,
  .confirm-delete-btn {
    flex: 1;
    padding: 9px 12px;
  }
}
</style>