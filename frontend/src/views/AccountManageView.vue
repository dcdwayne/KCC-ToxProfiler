<template>
  <main class="account-page">
    <!-- 頂部大標題 -->
    <header class="page-header">
      <h2 class="main-title">
        帳號與權限管理 <span class="title-en">Account & RBAC Management</span>
      </h2>
    </header>

    <!-- 頂部子頁面切換導覽列 (預設在『權限核准』) -->
    <nav class="sub-tab-nav">
      <button class="info-btn" title="點擊查看帳號管理使用說明" @click="isGuideOpen = true">!</button>

      <button
        class="action-btn tab-btn"
        :class="{ active: activeTab === 'approval' }"
        @click="switchSubTab('approval')"
      >
        權限核准
        <span v-if="pendingTotalCount > 0" class="pending-count-pill">
          待審 {{ pendingTotalCount }}
        </span>
      </button>

      <button
        class="action-btn tab-btn"
        :class="{ active: activeTab === 'logs' }"
        @click="switchSubTab('logs')"
      >
        使用者登入紀錄
      </button>
    </nav>

    <!-- ======================================================================= -->
    <!-- 子頁面 1：權限核准頁面 (Permission Approval)                             -->
    <!-- ======================================================================= -->
    <section v-if="activeTab === 'approval'" class="panel-container">
      <!-- 基本篩選條件區塊 -->
      <div class="filter-card">
        <div class="filter-card-header">
          <div class="pool-title-banner">
            <span class="banner-zh">基本篩選條件</span>
            <span class="banner-en">APPROVAL FILTER</span>
          </div>
          <div class="filter-btn-group">
            <button class="btn-outline" @click="resetApprovalFilters">重置條件</button>
            <button class="btn-solid" @click="fetchUsers">執行篩選</button>
          </div>
        </div>

        <div class="filter-grid">
          <!-- 關鍵字搜尋 -->
          <div class="filter-item">
            <label>關鍵字查詢（信箱 / 姓名 / 單位）</label>
            <input
              type="text"
              v-model.trim="approvalFilters.keyword"
              placeholder="輸入信箱、姓名或單位名稱..."
              class="text-input"
              @keyup.enter="fetchUsers"
            />
          </div>

          <!-- 權限角色篩選 -->
          <div class="filter-item">
            <label>權限角色 Role</label>
            <select v-model="approvalFilters.role" class="select-input" @change="fetchUsers">
              <option value="ALL">全部角色 (All Roles)</option>
              <option value="系統管理者">系統管理者 (Admin)</option>
              <option value="專家">專家 (Expert)</option>
              <option value="會員">會員 (Member)</option>
            </select>
          </div>

          <!-- 確認狀態 (審核狀態) 篩選 -->
          <div class="filter-item">
            <label>確認狀態 Approval Status</label>
            <select v-model="approvalFilters.approval_status" class="select-input" @change="fetchUsers">
              <option value="ALL">全部狀態 (All)</option>
              <option value="PENDING">待審核 (Pending)</option>
              <option value="APPROVED">已審核：通過 (Approved)</option>
              <option value="REJECTED">已審核：未通過 (Rejected)</option>
            </select>
          </div>

          <!-- 帳號狀態篩選 -->
          <div class="filter-item">
            <label>帳號狀態 Account Status</label>
            <select v-model="approvalFilters.account_status" class="select-input" @change="fetchUsers">
              <option value="ALL">全部狀態 (All)</option>
              <option value="ACTIVE">啟用中 (Active)</option>
              <option value="DISABLED">已停用 (Disabled)</option>
            </select>
          </div>
        </div>
      </div>

      <!-- 資料筆數與總頁數統計列 -->
      <div class="summary-bar">
        <div class="summary-left">
          <span class="summary-title">
            權限申請與帳號清單：共 <strong class="highlight-num">{{ userList.length }}</strong> 筆資料
            （共 <strong class="highlight-num">{{ approvalTotalPages }}</strong> 頁，目前位於第 <strong>{{ approvalPage }}</strong> 頁）
          </span>
        </div>
        <div class="summary-right">
          <span class="legend-hint">💡 提示：變更「權限角色」或點擊「通過／不通過」將立即同步生效</span>
        </div>
      </div>

      <!-- 帳號核准表格 -->
      <div v-if="isLoadingUsers" class="empty-box">正在載入帳號與權限核准資料...</div>

      <div v-else-if="paginatedUsers.length > 0" class="table-wrapper">
        <table class="tox-table">
          <thead>
            <tr>
              <th style="width: 48px;">#</th>
              <th style="min-width: 220px;">基本帳號資料 (信箱 / 姓名 / 單位職稱 / 電話)</th>
              <th style="width: 110px; text-align: center;">帳號狀態</th>
              <th style="width: 85px; text-align: center;">登入次數</th>
              <th style="width: 135px; text-align: center;">權限角色</th>
              <th style="width: 155px; text-align: center;">確認狀態</th>
              <th style="width: 155px; text-align: center;">核定時間 (台灣時區)</th>
              <th style="width: 175px; text-align: center;">審核操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(u, idx) in paginatedUsers"
              :key="u.id"
              :class="{ 'pending-row': u.approval_status === 'PENDING' }"
            >
              <!-- 1. 序號 -->
              <td class="cell-index">
                {{ (approvalPage - 1) * APPROVAL_ITEMS_PER_PAGE + idx + 1 }}.
              </td>

              <!-- 2. 基本帳號資料 -->
              <td>
                <div class="user-main-info">
                  <span class="user-email">{{ u.email }}</span>
                  <span v-if="u.is_self" class="self-tag">當前登入</span>
                </div>
                <div class="user-sub-info">
                  <span>👤 姓名：<strong>{{ u.name }}</strong></span>
                  <span>🏢 單位：{{ u.organization }}</span>
                  <span>💼 職稱：{{ u.job_title }}</span>
                  <span>📞 電話：{{ u.phone }}</span>
                </div>
                <div class="user-reg-time">申請時間：{{ u.created_at_tw }}</div>
              </td>

              <!-- 3. 帳號狀態 (ACTIVE 啟用 / DISABLED 停用) -->
              <td class="text-center">
                <button
                  class="status-toggle-btn"
                  :class="u.account_status === 'ACTIVE' ? 'acc-active' : 'acc-disabled'"
                  :disabled="u.is_self || updatingUserId === u.id"
                  @click="handleToggleAccountStatus(u)"
                  :title="u.is_self ? '無法停用自己目前登入的帳號' : '點擊切換啟用 / 停用狀態'"
                >
                  {{ u.account_status === 'ACTIVE' ? '● 啟用中' : '○ 已停用' }}
                </button>
              </td>

              <!-- 4. 登入次數 -->
              <td class="text-center">
                <span class="login-count-badge">{{ u.login_count }} 次</span>
              </td>

              <!-- 5. 權限角色 (支援直接下拉變更) -->
              <td class="text-center">
                <select
                  :value="u.role"
                  class="role-select"
                  :class="getRoleSelectClass(u.role)"
                  :disabled="u.is_self || updatingUserId === u.id"
                  @change="handleChangeUserRole(u, $event.target.value)"
                >
                  <option value="系統管理者">系統管理者</option>
                  <option value="專家">專家</option>
                  <option value="會員">會員</option>
                </select>
              </td>

              <!-- 6. 確認狀態 (待審核 vs 已審核：通過 / 未通過) -->
              <td class="text-center">
                <span class="approval-badge" :class="getApprovalBadgeClass(u.approval_status)">
                  {{ formatApprovalLabel(u.approval_status) }}
                </span>
              </td>

              <!-- 7. 核定時間 (已審核的才會有時間) -->
              <td class="text-center time-cell">
                <span v-if="u.approved_at_tw" class="approved-time-text">
                  {{ u.approved_at_tw }}
                </span>
                <span v-else class="unapproved-dash">-- (待審核)</span>
              </td>

              <!-- 8. 審核操作按鈕 -->
              <td class="text-center">
                <div class="audit-btn-group">
                  <button
                    class="audit-btn approve"
                    :class="{ 'is-current': u.approval_status === 'APPROVED' }"
                    :disabled="u.is_self || updatingUserId === u.id || u.approval_status === 'APPROVED'"
                    @click="handleAuditUser(u, 'APPROVED')"
                    title="核准通過此帳號申請"
                  >
                    ✓ 通過
                  </button>
                  <button
                    class="audit-btn reject"
                    :class="{ 'is-current': u.approval_status === 'REJECTED' }"
                    :disabled="u.is_self || updatingUserId === u.id || u.approval_status === 'REJECTED'"
                    @click="handleAuditUser(u, 'REJECTED')"
                    title="駁回此帳號申請"
                  >
                    ✕ 未通過
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else class="empty-box">
        目前篩選條件下無符合的帳號申請紀錄。
      </div>

      <!-- 權限核准頁碼列 (« 首頁 01 02 03 最後 ») -->
      <div class="pagination-bar" v-if="approvalTotalPages > 1">
        <button class="page-nav-btn" :disabled="approvalPage === 1" @click="approvalPage = 1">
          « 首頁
        </button>
        <button
          v-for="p in visibleApprovalPages"
          :key="p"
          class="page-num-btn"
          :class="{ active: approvalPage === p }"
          @click="approvalPage = p"
        >
          {{ formatPageNumber(p) }}
        </button>
        <button class="page-nav-btn" :disabled="approvalPage === approvalTotalPages" @click="approvalPage = approvalTotalPages">
          最後 »
        </button>
      </div>
    </section>

    <!-- ======================================================================= -->
    <!-- 子頁面 2：使用者登入紀錄 Log 頁面 (含時間區間查詢)                        -->
    <!-- ======================================================================= -->
    <section v-else class="panel-container">
      <!-- 登入紀錄篩選條件區塊 (含時間區間查詢) -->
      <div class="filter-card">
        <div class="filter-card-header">
          <div class="pool-title-banner">
            <span class="banner-zh">登入稽核篩選與時間區間查詢</span>
            <span class="banner-en">LOGIN LOGS & TIME RANGE FILTER</span>
          </div>
          <div class="filter-btn-group">
            <button class="btn-outline" @click="resetLogFilters">重置區間與條件</button>
            <button class="btn-solid" @click="fetchLoginLogs">查詢紀錄</button>
          </div>
        </div>

        <!-- 第一列：時間區間查詢 + 快速範圍按鈕 -->
        <div class="time-range-row">
          <span class="range-label">📅 登入時間區間（台灣時區）：</span>
          <span class="range-sub">從</span>
          <input type="date" v-model="logFilters.start_date" class="date-input" />
          <span class="range-sub">至</span>
          <input type="date" v-model="logFilters.end_date" class="date-input" />

          <div class="quick-date-btns">
            <button type="button" class="quick-chip" @click="setQuickDateRange(0)">今日</button>
            <button type="button" class="quick-chip" @click="setQuickDateRange(7)">近 7 天</button>
            <button type="button" class="quick-chip" @click="setQuickDateRange(30)">近 30 天</button>
            <button type="button" class="quick-chip" @click="clearDateRange">全部時間</button>
          </div>
        </div>

        <!-- 第二列：關鍵字 / 角色 / 登入結果 -->
        <div class="filter-grid log-grid-3">
          <div class="filter-item">
            <label>關鍵字搜尋（帳號信箱 / 姓名 / IP 位址）</label>
            <input
              type="text"
              v-model.trim="logFilters.keyword"
              placeholder="輸入信箱、姓名或 IP..."
              class="text-input"
              @keyup.enter="fetchLoginLogs"
            />
          </div>

          <div class="filter-item">
            <label>登入角色 Role</label>
            <select v-model="logFilters.role" class="select-input" @change="fetchLoginLogs">
              <option value="ALL">全部角色 (All)</option>
              <option value="系統管理者">系統管理者</option>
              <option value="專家">專家</option>
              <option value="會員">會員</option>
              <option value="訪客">訪客 (Guest)</option>
            </select>
          </div>

          <div class="filter-item">
            <label>登入結果狀態 Login Result</label>
            <select v-model="logFilters.login_result" class="select-input" @change="fetchLoginLogs">
              <option value="ALL">全部結果 (All Results)</option>
              <option value="SUCCESS">登入成功 (SUCCESS)</option>
              <option value="GUEST">訪客進入 (GUEST)</option>
              <option value="FAILED_PWD">密碼或帳號錯誤 (FAILED_PWD)</option>
              <option value="FAILED_PENDING">待審核攔截 (FAILED_PENDING)</option>
              <option value="FAILED_REJECTED">審核未通過攔截 (FAILED_REJECTED)</option>
              <option value="FAILED_DISABLED">停用帳號攔截 (FAILED_DISABLED)</option>
            </select>
          </div>
        </div>
      </div>

      <!-- 登入紀錄筆數與頁數統計列 -->
      <div class="summary-bar">
        <div class="summary-left">
          <span class="summary-title">
            使用者登入稽核紀錄：共 <strong class="highlight-num">{{ logList.length }}</strong> 筆資料
            （共 <strong class="highlight-num">{{ logTotalPages }}</strong> 頁，目前位於第 <strong>{{ logPage }}</strong> 頁）
          </span>
        </div>
      </div>

      <!-- 登入紀錄表格 -->
      <div v-if="isLoadingLogs" class="empty-box">正在載入使用者登入稽核紀錄...</div>

      <div v-else-if="paginatedLogs.length > 0" class="table-wrapper">
        <table class="tox-table">
          <thead>
            <tr>
              <th style="width: 56px;">#</th>
              <th style="width: 185px;">登入時間 (台灣時區)</th>
              <th>登入帳號 (Email)</th>
              <th style="width: 140px;">使用者姓名</th>
              <th style="width: 130px; text-align: center;">權限角色</th>
              <th style="width: 150px; text-align: center;">來源 IP 位址</th>
              <th style="width: 195px; text-align: center;">登入驗證結果</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(lg, idx) in paginatedLogs" :key="lg.id">
              <td class="cell-index">
                {{ (logPage - 1) * LOG_ITEMS_PER_PAGE + idx + 1 }}.
              </td>
              <td class="time-cell">
                <strong>{{ lg.login_at_tw }}</strong>
              </td>
              <td>
                <span class="user-email">{{ lg.email }}</span>
              </td>
              <td>{{ lg.name }}</td>
              <td class="text-center">
                <span class="role-pill" :class="getRoleSelectClass(lg.role)">
                  {{ lg.role }}
                </span>
              </td>
              <td class="text-center">
                <code class="ip-code">{{ lg.ip_address }}</code>
              </td>
              <td class="text-center">
                <span class="log-result-badge" :class="getLogResultClass(lg.login_result)">
                  {{ formatLogResultText(lg.login_result) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else class="empty-box">
        此時間區間與篩選條件下無任何登入紀錄。
      </div>

      <!-- 登入紀錄頁碼列 (« 首頁 01 02 03 最後 ») -->
      <div class="pagination-bar" v-if="logTotalPages > 1">
        <button class="page-nav-btn" :disabled="logPage === 1" @click="logPage = 1">
          « 首頁
        </button>
        <button
          v-for="p in visibleLogPages"
          :key="p"
          class="page-num-btn"
          :class="{ active: logPage === p }"
          @click="logPage = p"
        >
          {{ formatPageNumber(p) }}
        </button>
        <button class="page-nav-btn" :disabled="logPage === logTotalPages" @click="logPage = logTotalPages">
          最後 »
        </button>
      </div>
    </section>

    <!-- 使用說明彈出視窗 -->
    <InfoGuideModal :isOpen="isGuideOpen" page="account" @close="isGuideOpen = false" />
  </main>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import InfoGuideModal from '../components/InfoGuideModal.vue'

const API_BASE_URL = window.location.port === '5173'
  ? `http://${window.location.hostname}:8000/api`
  : '/api'

// =====================================================================
// 👇👇👇 【每頁顯示筆數手動調整區】可在此自由修改每頁顯示幾個 Row 👇👇👇
// =====================================================================
const APPROVAL_ITEMS_PER_PAGE = 6   // 『權限核准』每頁顯示幾筆帳號
const LOG_ITEMS_PER_PAGE = 8        // 『使用者登入紀錄』每頁顯示幾筆 Log

const isGuideOpen = ref(false)

// 預設先在『權限核准』頁面 ('approval' | 'logs')
const activeTab = ref('approval')

// --- 子頁面 1：權限核准狀態 ---
const userList = ref([])
const pendingTotalCount = ref(0)
const isLoadingUsers = ref(false)
const updatingUserId = ref(null)
const approvalPage = ref(1)

const approvalFilters = reactive({
  keyword: '',
  role: 'ALL',
  approval_status: 'ALL',
  account_status: 'ALL'
})

// --- 子頁面 2：使用者登入紀錄狀態 ---
const logList = ref([])
const isLoadingLogs = ref(false)
const logPage = ref(1)

const logFilters = reactive({
  start_date: '',
  end_date: '',
  keyword: '',
  role: 'ALL',
  login_result: 'ALL'
})

// --- 分頁計算邏輯：權限核准 ---
const approvalTotalPages = computed(() => {
  return Math.max(1, Math.ceil(userList.value.length / APPROVAL_ITEMS_PER_PAGE))
})

const paginatedUsers = computed(() => {
  const start = (approvalPage.value - 1) * APPROVAL_ITEMS_PER_PAGE
  return userList.value.slice(start, start + APPROVAL_ITEMS_PER_PAGE)
})

const visibleApprovalPages = computed(() => {
  const total = approvalTotalPages.value
  const current = approvalPage.value
  let start = Math.max(1, current - 2)
  let end = Math.min(total, start + 4)
  if (end - start < 4) start = Math.max(1, end - 4)
  const pages = []
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

// --- 分頁計算邏輯：登入紀錄 ---
const logTotalPages = computed(() => {
  return Math.max(1, Math.ceil(logList.value.length / LOG_ITEMS_PER_PAGE))
})

const paginatedLogs = computed(() => {
  const start = (logPage.value - 1) * LOG_ITEMS_PER_PAGE
  return logList.value.slice(start, start + LOG_ITEMS_PER_PAGE)
})

const visibleLogPages = computed(() => {
  const total = logTotalPages.value
  const current = logPage.value
  let start = Math.max(1, current - 2)
  let end = Math.min(total, start + 4)
  if (end - start < 4) start = Math.max(1, end - 4)
  const pages = []
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

const formatPageNumber = (num) => String(num).padStart(2, '0')

// 切換頂部子頁籤
const switchSubTab = async (tabName) => {
  activeTab.value = tabName
  if (tabName === 'approval') {
    await fetchUsers()
  } else {
    await fetchLoginLogs()
  }
}

// =====================================================================
// API 呼叫：權限核准管理
// =====================================================================
const fetchUsers = async () => {
  isLoadingUsers.value = true
  try {
    const params = new URLSearchParams({
      keyword: approvalFilters.keyword,
      role: approvalFilters.role,
      approval_status: approvalFilters.approval_status,
      account_status: approvalFilters.account_status
    })
    const res = await fetch(`${API_BASE_URL}/admin/users?${params.toString()}`, {
      credentials: 'include'
    })
    if (!res.ok) throw new Error('無法取得帳號核准列表')
    const data = await res.json()
    userList.value = data.users || []
    pendingTotalCount.value = data.pending_total ?? 0
    approvalPage.value = 1
  } catch (err) {
    console.error('載入帳號清單失敗:', err)
  } finally {
    isLoadingUsers.value = false
  }
}

const resetApprovalFilters = async () => {
  approvalFilters.keyword = ''
  approvalFilters.role = 'ALL'
  approvalFilters.approval_status = 'ALL'
  approvalFilters.account_status = 'ALL'
  await fetchUsers()
}

// 審核帳號 (通過 APPROVED / 未通過 REJECTED)
const handleAuditUser = async (user, newStatus) => {
  updatingUserId.value = user.id
  try {
    const res = await fetch(`${API_BASE_URL}/admin/users/${user.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ approval_status: newStatus })
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || '更新審核狀態失敗')

    user.approval_status = data.user.approval_status
    user.approved_at_tw = data.user.approved_at_tw
    await fetchUsers()
  } catch (err) {
    alert(err.message)
  } finally {
    updatingUserId.value = null
  }
}

// 變更使用者權限角色
const handleChangeUserRole = async (user, newRole) => {
  updatingUserId.value = user.id
  try {
    const res = await fetch(`${API_BASE_URL}/admin/users/${user.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ role: newRole })
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || '更新角色失敗')
    user.role = data.user.role
  } catch (err) {
    alert(err.message)
    await fetchUsers()
  } finally {
    updatingUserId.value = null
  }
}

// 切換帳號啟用 / 停用狀態
const handleToggleAccountStatus = async (user) => {
  const nextStatus = user.account_status === 'ACTIVE' ? 'DISABLED' : 'ACTIVE'
  updatingUserId.value = user.id
  try {
    const res = await fetch(`${API_BASE_URL}/admin/users/${user.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ account_status: nextStatus })
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || '切換帳號狀態失敗')
    user.account_status = data.user.account_status
  } catch (err) {
    alert(err.message)
  } finally {
    updatingUserId.value = null
  }
}

// =====================================================================
// API 呼叫：使用者登入紀錄與時間區間查詢
// =====================================================================
const fetchLoginLogs = async () => {
  isLoadingLogs.value = true
  try {
    const params = new URLSearchParams({
      start_date: logFilters.start_date,
      end_date: logFilters.end_date,
      keyword: logFilters.keyword,
      role: logFilters.role,
      login_result: logFilters.login_result
    })
    const res = await fetch(`${API_BASE_URL}/admin/logs?${params.toString()}`, {
      credentials: 'include'
    })
    if (!res.ok) throw new Error('無法取得登入稽核紀錄')
    const data = await res.json()
    logList.value = data.logs || []
    logPage.value = 1
  } catch (err) {
    console.error('載入登入紀錄失敗:', err)
  } finally {
    isLoadingLogs.value = false
  }
}

// 快速設定台灣日期區間 (今日 / 近 7 天 / 近 30 天)
const formatDateYMD = (dateObj) => {
  const y = dateObj.getFullYear()
  const m = String(dateObj.getMonth() + 1).padStart(2, '0')
  const d = String(dateObj.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

const setQuickDateRange = async (daysAgo) => {
  const end = new Date()
  const start = new Date()
  start.setDate(end.getDate() - daysAgo)
  logFilters.start_date = formatDateYMD(start)
  logFilters.end_date = formatDateYMD(end)
  await fetchLoginLogs()
}

const clearDateRange = async () => {
  logFilters.start_date = ''
  logFilters.end_date = ''
  await fetchLoginLogs()
}

const resetLogFilters = async () => {
  logFilters.start_date = ''
  logFilters.end_date = ''
  logFilters.keyword = ''
  logFilters.role = 'ALL'
  logFilters.login_result = 'ALL'
  await fetchLoginLogs()
}

// --- 狀態文字與樣式輔助函式 ---
const formatApprovalLabel = (status) => {
  if (status === 'APPROVED') return '已審核 (通過)'
  if (status === 'REJECTED') return '已審核 (未通過)'
  return '待審核 (Pending)'
}

const getApprovalBadgeClass = (status) => {
  if (status === 'APPROVED') return 'badge-approved'
  if (status === 'REJECTED') return 'badge-rejected'
  return 'badge-pending'
}

const getRoleSelectClass = (role) => {
  if (role === '系統管理者') return 'role-admin'
  if (role === '專家') return 'role-expert'
  if (role === '會員') return 'role-member'
  return 'role-guest'
}

const formatLogResultText = (res) => {
  const map = {
    SUCCESS: '✓ 登入成功',
    GUEST: '👤 訪客進入',
    FAILED_PWD: '✕ 帳密錯誤',
    FAILED_PENDING: '⏳ 待審核攔截',
    FAILED_REJECTED: '🚫 未通過攔截',
    FAILED_DISABLED: '🔒 帳號停用攔截'
  }
  return map[res] || res
}

const getLogResultClass = (res) => {
  if (res === 'SUCCESS') return 'log-success'
  if (res === 'GUEST') return 'log-guest'
  if (res === 'FAILED_PENDING') return 'log-pending'
  return 'log-failed'
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.account-page {
  max-width: 1220px;
  margin: 20px auto 40px auto;
  padding: 0 20px;
}

.page-header {
  margin-bottom: 16px;
}

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

/* 頂部雙按鈕頁籤列 (對齊 MetaAnalysis.vue) */
.sub-tab-nav {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}

.info-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1.5px solid var(--dark-color);
  background-color: var(--light-color);
  color: var(--dark-color);
  font-weight: 900;
  font-size: 15px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.info-btn:hover {
  background-color: var(--dark-color);
  color: #ffffff;
}

.action-btn.tab-btn {
  background-color: #ffffff;
  color: #333;
  border: 1.5px solid var(--dark-color);
  padding: 10px 28px;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.action-btn.tab-btn.active,
.action-btn.tab-btn:hover {
  background-color: var(--dark-color);
  color: #ffffff;
}

.pending-count-pill {
  background-color: #ef5327;
  color: #ffffff;
  font-size: 12px;
  font-weight: 900;
  padding: 2px 8px;
  border-radius: 12px;
}

/* 篩選卡片區塊 */
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

.banner-zh {
  font-size: 19px;
  font-weight: 900;
  color: #2c3e50;
}

.banner-en {
  font-size: 13px;
  font-weight: 800;
  color: var(--dark-color);
  letter-spacing: 1px;
}

.filter-btn-group {
  display: flex;
  gap: 10px;
}

.btn-outline {
  background-color: #ffffff;
  color: var(--dark-color);
  border: 1.5px solid var(--dark-color);
  padding: 7px 18px;
  border-radius: 8px;
  font-weight: 800;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-outline:hover {
  background-color: var(--light-color);
}

.btn-solid {
  background-color: #1b1e29;
  color: #ffffff;
  border: 1.5px solid #1b1e29;
  padding: 7px 22px;
  border-radius: 8px;
  font-weight: 800;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-solid:hover {
  background-color: var(--dark-color);
  border-color: var(--dark-color);
}

.filter-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr 1fr 1fr;
  gap: 14px;
}

.filter-grid.log-grid-3 {
  grid-template-columns: 1.5fr 1fr 1.2fr;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-item label {
  font-size: 13px;
  font-weight: 800;
  color: #475569;
}

.text-input,
.select-input,
.date-input {
  padding: 8px 12px;
  border: 1.5px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
  background-color: #f8fafc;
  outline: none;
  transition: all 0.2s;
}

.text-input:focus,
.select-input:focus,
.date-input:focus {
  border-color: var(--dark-color);
  background-color: #ffffff;
}

/* 登入紀錄：時間區間查詢列 */
.time-range-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  background-color: #f8fafc;
  border: 1px dashed #cbd5e1;
  padding: 12px 16px;
  border-radius: 10px;
  margin-bottom: 14px;
}

.range-label {
  font-size: 14px;
  font-weight: 800;
  color: #1b1e29;
}

.range-sub {
  font-size: 13.5px;
  font-weight: 700;
  color: #475569;
}

.quick-date-btns {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.quick-chip {
  background-color: #ffffff;
  color: var(--dark-color);
  border: 1px solid var(--dark-color);
  padding: 5px 12px;
  border-radius: 6px;
  font-size: 12.5px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-chip:hover {
  background-color: var(--dark-color);
  color: #ffffff;
}

/* 統計資訊列 */
.summary-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 0 4px;
  flex-wrap: wrap;
  gap: 8px;
}

.summary-title {
  font-size: 17px;
  font-weight: 800;
  color: #2c3e50;
}

.highlight-num {
  color: var(--dark-color);
  font-size: 19px;
  font-weight: 900;
}

.legend-hint {
  font-size: 13px;
  font-weight: 700;
  color: #475569;
}

/* 表格樣式 */
.table-wrapper {
  background-color: #ffffff;
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
  overflow-x: auto;
  border: 1px solid #e2e8f0;
}

.tox-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.tox-table thead tr {
  background-color: #1b1e29;
  color: #ffffff;
}

.tox-table th {
  padding: 13px 14px;
  font-size: 13.5px;
  font-weight: 800;
  letter-spacing: 0.4px;
  white-space: nowrap;
}

.tox-table tbody tr {
  border-bottom: 1px solid #edf2f7;
  transition: background-color 0.15s;
}

.tox-table tbody tr:hover {
  background-color: #f8fafc;
}

.tox-table tbody tr.pending-row {
  background-color: #fffaf0;
}

.tox-table td {
  padding: 13px 14px;
  vertical-align: middle;
  font-size: 14px;
  color: #334155;
}

.text-center {
  text-align: center;
}

.cell-index {
  font-weight: 800;
  color: #475569;
}

.user-main-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.user-email {
  font-weight: 900;
  color: #1b1e29;
  font-size: 15px;
}

.self-tag {
  background-color: #1b1e29;
  color: #f6d32d;
  font-size: 11px;
  font-weight: 800;
  padding: 1px 7px;
  border-radius: 6px;
}

.user-sub-info {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12.5px;
  color: #475569;
  font-weight: 600;
  margin-bottom: 3px;
}

.user-reg-time {
  font-size: 11.5px;
  color: #94a3b8;
  font-weight: 600;
}

/* 帳號狀態按鈕 */
.status-toggle-btn {
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 12.5px;
  font-weight: 800;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
}

.status-toggle-btn.acc-active {
  background-color: #dcfce7;
  color: #166534;
  border-color: #86efac;
}

.status-toggle-btn.acc-disabled {
  background-color: #fee2e2;
  color: #991b1b;
  border-color: #fca5a5;
}

.status-toggle-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.login-count-badge {
  background-color: #f1f5f9;
  color: #1e293b;
  font-weight: 800;
  font-size: 13px;
  padding: 4px 10px;
  border-radius: 8px;
}

/* 角色下拉與徽章 */
.role-select,
.role-pill {
  padding: 5px 10px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 800;
  border: 1.5px solid transparent;
}

.role-admin {
  background-color: #fef3c7;
  color: #92400e;
  border-color: #f59e0b;
}

.role-expert {
  background-color: #e0f2fe;
  color: #075985;
  border-color: #38bdf8;
}

.role-member {
  background-color: #dcfce7;
  color: #166534;
  border-color: #4ade80;
}

.role-guest {
  background-color: #f1f5f9;
  color: #64748b;
  border-color: #cbd5e1;
}

/* 確認狀態徽章 (仿照系統紅/黃/深青色系) */
.approval-badge {
  display: inline-block;
  padding: 5px 12px;
  border-radius: 6px;
  font-size: 12.5px;
  font-weight: 800;
  white-space: nowrap;
}

.badge-pending {
  background-color: #ffca28;
  color: #1b1e29;
}

.badge-approved {
  background-color: var(--dark-color);
  color: #ffffff;
}

.badge-rejected {
  background-color: #ef5327;
  color: #ffffff;
}

.time-cell {
  font-variant-numeric: tabular-nums;
  font-size: 13.5px;
}

.approved-time-text {
  color: #1b1e29;
  font-weight: 700;
}

.unapproved-dash {
  color: #94a3b8;
  font-weight: 600;
  font-size: 12.5px;
}

/* 審核操作按鈕群 */
.audit-btn-group {
  display: inline-flex;
  gap: 6px;
}

.audit-btn {
  padding: 5px 10px;
  border-radius: 6px;
  font-size: 12.5px;
  font-weight: 800;
  cursor: pointer;
  border: 1.5px solid #cbd5e1;
  background-color: #ffffff;
  transition: all 0.2s;
}

.audit-btn.approve:hover:not(:disabled) {
  background-color: var(--dark-color);
  color: #ffffff;
  border-color: var(--dark-color);
}

.audit-btn.reject:hover:not(:disabled) {
  background-color: #ef5327;
  color: #ffffff;
  border-color: #ef5327;
}

.audit-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

/* 登入紀錄專用バッジ */
.ip-code {
  background-color: #f1f5f9;
  color: #334155;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 700;
}

.log-result-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 12.5px;
  font-weight: 800;
}

.log-success {
  background-color: var(--dark-color);
  color: #ffffff;
}

.log-guest {
  background-color: #e0f2f1;
  color: var(--dark-color);
  border: 1px solid var(--primary-color);
}

.log-pending {
  background-color: #ffca28;
  color: #1b1e29;
}

.log-failed {
  background-color: #ef5327;
  color: #ffffff;
}

.empty-box {
  background-color: rgba(255, 255, 255, 0.75);
  border: 1.5px dashed var(--dark-color);
  border-radius: 14px;
  padding: 40px 20px;
  text-align: center;
  color: #475569;
  font-weight: 800;
}

/* 頁碼列 (與 Review 及 History 頁面完全一致) */
.pagination-bar {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  margin-top: 24px;
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