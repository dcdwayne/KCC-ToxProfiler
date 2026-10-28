<template>
  <main class="history-page">
    <!-- 頂部大標題 -->
    <header class="page-header">
      <h2 class="main-title">
        歷史紀錄管理 <span class="title-en">Historical Records</span>
      </h2>
    </header>

    <!-- 標題與多選排序控制列 -->
    <section class="history-section">
      <div class="list-controls">
        <div class="pool-title-banner">
          <span class="list-title">
            危害辨識評估歷史紀錄，共 <strong class="count-num">{{ records.length }}</strong> 筆：
          </span>
        </div>

        <!-- 排序按鈕區：支援多選組合排序 (新增『評估時間』由近到遠) -->
        <div class="sort-options">
          <span>排序：</span>
          <button 
            v-for="opt in sortOptions" 
            :key="opt.key"
            class="chip-btn small"
            :class="{ active: activeSorts.includes(opt.key) }"
            @click="toggleSort(opt.key)"
            title="可多選組合排序（依點選先後決定主次順序）"
          >
            {{ opt.label }}
            <span v-if="activeSorts.includes(opt.key)" class="sort-order-num">
              {{ activeSorts.indexOf(opt.key) + 1 }}
            </span>
          </button>
        </div>
      </div>

      <!-- 歷史紀錄列表 -->
      <div v-if="isLoading" class="empty-list-box">
        正在載入歷史評估紀錄...
      </div>

      <div v-else-if="paginatedRecords.length > 0" class="record-list">
        <HistoryRecordRow
          v-for="(rec, idx) in paginatedRecords"
          :key="rec.id"
          :index="(currentPage - 1) * ITEMS_PER_PAGE + idx + 1"
          :record="rec"
          @toggle-select="handleToggleSelect"
          @go-meta="handleGoToMeta"
          @delete-record="openDeleteModal"
        />
      </div>

      <div v-else class="empty-list-box">
        目前尚無任何危害辨識評估歷史紀錄。
      </div>

      <!-- 頁碼點擊功能：« 首頁 01 02 03 最後 » -->
      <div class="pagination-bar" v-if="totalPages > 1">
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
                <span class="warn-subtitle">DELETION WARNING / 刪除確認</span>
                <h3 class="warn-title">確定要永久刪除此筆評估紀錄嗎？</h3>
              </div>
            </div>
            <button class="close-btn" @click="closeDeleteModal" title="取消並關閉">✕</button>
          </header>

          <!-- 警告內容說明區 -->
          <div class="warn-body">
            <!-- 欲刪除的目標摘要卡 -->
            <div class="target-summary-card">
              <div class="summary-item">
                <span class="s-label">目標化學物質：</span>
                <strong class="s-value">{{ recordToDelete.chemical_name }} (Evaluation #{{ recordToDelete.id }})</strong>
              </div>
              <div class="summary-item">
                <span class="s-label">危害評級與時間：</span>
                <span class="s-value">
                  {{ recordToDelete.hazard_score !== null ? `${recordToDelete.risk_level} (${recordToDelete.hazard_score}分)` : 'UNSCORED' }}
                  ｜ {{ recordToDelete.created_at_tw }}
                </span>
              </div>
            </div>

            <!-- 若該筆紀錄已被勾選為 FastMCP 資料源，顯示特別提醒 -->
            <div v-if="recordToDelete.is_selected" class="mcp-active-alert">
              ⚠️ <strong>特別注意：</strong>此筆紀錄目前已勾選為 <strong>FastMCP 外部問答知識庫</strong> 之代表資料，刪除後 AI 助手將無法再引用此評估結果回答問題！
            </div>

            <p class="consequence-lead">執行刪除將會連帶執行以下操作，且<strong>無法復原</strong>：</p>
            <ul class="consequence-list">
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
          </div>

          <!-- 底部操作按鈕 -->
          <footer class="warn-footer">
            <button class="cancel-btn" :disabled="isDeleting" @click="closeDeleteModal">
              取消保留
            </button>
            <button class="confirm-delete-btn" :disabled="isDeleting" @click="confirmDeleteRecord">
              {{ isDeleting ? '正在刪除紀錄...' : '確認永久刪除' }}
            </button>
          </footer>
        </div>
      </div>
    </transition>
  </main>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import HistoryRecordRow from '../components/HistoryRecordRow.vue'

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

// 多選排序狀態陣列 (依點擊順序存放 'chemical' | 'hazard' | 'status' | 'time')
const activeSorts = ref([])
const sortOptions = [
  { key: 'chemical', label: '化學物質名稱' },
  { key: 'hazard', label: '危害等級' },
  { key: 'status', label: '狀態' },
  { key: 'time', label: '評估時間' }
]

// 刪除警告視窗狀態
const isDeleteModalOpen = ref(false)
const recordToDelete = ref(null)
const isDeleting = ref(false)

// --- 分頁計算邏輯 ---
const totalPages = computed(() => {
  return Math.max(1, Math.ceil(records.value.length / ITEMS_PER_PAGE))
})

const paginatedRecords = computed(() => {
  const start = (currentPage.value - 1) * ITEMS_PER_PAGE
  return records.value.slice(start, start + ITEMS_PER_PAGE)
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
    alert('無法更新勾選狀態，請確認後端連線！')
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
    alert('刪除失敗，請稍後再試！')
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
  max-width: 1100px;
  margin: 24px auto 40px auto;
  padding: 0 20px;
}

.page-header {
  margin-bottom: 22px;
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
  font-weight: 900;
}

/* 標題與排序列 */
.list-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
  flex-wrap: wrap;
  gap: 12px;
}

.pool-title-banner {
  display: flex;
  align-items: center;
  border-left: 5px solid var(--dark-color);
  padding-left: 14px;
}

.list-title {
  font-size: 20px;
  font-weight: 900;
  color: #2c3e50;
  letter-spacing: 0.5px;
}

.count-num {
  font-size: 18px;
  font-weight: 800;
  color: var(--dark-color);
  letter-spacing: 1px;
}

.sort-options {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #2c3e50;
  font-weight: 800;
  font-size: 18x;
}

.chip-btn {
  background-color: #ffffff;
  color : #555;
  border: 1.5px solid #ccc;
  padding: 6px 18px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 800;
  font-size: 14.5px;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}


.chip-btn:hover {
  background-color: #ffffff;
}

.chip-btn.active {
  background-color: var(--dark-color);
  color: #ffffff;
}

.sort-order-num {
  background-color: rgba(255, 255, 255, 0.25);
  color: #ffffff;
  font-size: 11px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty-list-box {
  background-color: rgba(255, 255, 255, 0.7);
  border: 1px dashed var(--dark-color);
  border-radius: 12px;
  padding: 40px 20px;
  text-align: center;
  color: #555;
  font-weight: bold;
}

/* 融合 Review 版面配色的頁碼列 (« 首頁 01 02 03 最後 ») */
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

/* ================= 刪除確認警告彈出視窗樣式 ================= */
.warn-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background-color: rgba(27, 30, 41, 0.65);
  backdrop-filter: blur(3px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2600;
  padding: 20px;
}

.warn-modal {
  background-color: #ffffff;
  width: 95%;
  max-width: 580px;
  border-radius: 18px;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.28);
  overflow: hidden;
  border: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
}

.warn-header {
  background-color: #1b1e29;
  color: #ffffff;
  padding: 18px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 4px solid #e74c3c;
}

.warn-title-group {
  display: flex;
  align-items: center;
  gap: 14px;
}

.warn-icon {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background-color: #e74c3c;
  color: #ffffff;
  font-weight: 900;
  font-size: 19px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.warn-subtitle {
  font-size: 11px;
  letter-spacing: 1.2px;
  color: #fca5a5;
  font-weight: 800;
  display: block;
}

.warn-title {
  margin: 2px 0 0 0;
  font-size: 19px;
  font-weight: 800;
  color: #ffffff;
}

.close-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: #cbd5e1;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  font-size: 17px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background-color: #e74c3c;
  color: #ffffff;
}

.warn-body {
  padding: 22px 26px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.target-summary-card {
  background-color: #f8fafc;
  border: 1px solid #cbd5e1;
  border-left: 4px solid var(--dark-color);
  border-radius: 10px;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.summary-item {
  font-size: 14.5px;
  color: #334155;
}

.s-label {
  color: #64748b;
  font-weight: 700;
}

.s-value {
  color: #1b1e29;
  font-weight: 800;
}

.mcp-active-alert {
  background-color: #fff5f5;
  border: 1.5px solid #feb2b2;
  color: #c53030;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13.5px;
  line-height: 1.5;
}

.consequence-lead {
  margin: 2px 0 0 0;
  font-size: 14.5px;
  color: #334155;
}

.consequence-list {
  margin: 0;
  padding-left: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 14px;
  line-height: 1.6;
  color: #475569;
}

.consequence-list code {
  background-color: #f1f5f9;
  color: #0f172a;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 700;
}

.warn-footer {
  padding: 14px 26px;
  background-color: #f8fafc;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.cancel-btn {
  background-color: #ffffff;
  color: #475569;
  border: 1.5px solid #cbd5e1;
  padding: 9px 22px;
  border-radius: 8px;
  font-size: 14.5px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn:hover:not(:disabled) {
  background-color: #f1f5f9;
  color: #1e293b;
}

.confirm-delete-btn {
  background-color: #e74c3c;
  color: #ffffff;
  border: none;
  padding: 9px 24px;
  border-radius: 8px;
  font-size: 14.5px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 10px rgba(231, 76, 60, 0.25);
}

.confirm-delete-btn:hover:not(:disabled) {
  background-color: #c0392b;
}

.confirm-delete-btn:disabled,
.cancel-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>