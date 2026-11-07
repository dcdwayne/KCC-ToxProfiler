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
            <label>關鍵字查詢（姓名 / 信箱 / 單位）</label>
            <input
              type="text"
              v-model.trim="approvalFilters.keyword"
              placeholder="輸入申請人姓名、信箱或單位..."
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
          <span class="legend-hint">💡 點擊「申請人姓名」可檢視完整基本資料 ｜ 今日額度統計：{{ quotaDateTw || '今日' }}</span>
        </div>
      </div>

      <!-- 帳號核准表格 (重新調配各欄舒適寬度，防止換行擠壓) -->
      <div v-if="isLoadingUsers" class="empty-box">正在載入帳號與權限核准資料...</div>

      <div v-else-if="paginatedUsers.length > 0" class="table-wrapper">
        <table class="tox-table">
          <thead>
            <tr>
              <th style="width: 44px; text-align: center;">#</th>
              <th style="min-width: 225px;">基本帳號資料 (姓名)</th>
              <th style="width: 96px; text-align: center;">帳號狀態</th>
              <th style="width: 78px; text-align: center;">登入次數</th>
              <th style="width: 185px; text-align: center;">今日 AI 額度 (次數 / Tokens)</th>
              <th style="width: 120px; text-align: center;">權限角色</th>
              <th style="width: 125px; text-align: center;">確認狀態</th>
              <th style="width: 160px; text-align: center;">核定時間 (台灣)</th>
              <th style="width: 185px; text-align: center;">審核操作 / 刪除</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(u, idx) in paginatedUsers"
              :key="u.id"
              :class="{ 'pending-row': u.approval_status === 'PENDING' }"
            >
              <!-- 1. 序號 -->
              <td class="text-center cell-index">
                {{ (approvalPage - 1) * APPROVAL_ITEMS_PER_PAGE + idx + 1 }}.
              </td>

              <!-- 2. 基本帳號資料：單行不換行顯示『申請人姓名』與『當前登入』標籤 -->
              <td>
                <div class="name-cell-wrap">
                  <button
                    type="button"
                    class="applicant-name-btn"
                    @click="openUserDetailModal(u)"
                    title="點擊檢視此申請人之詳細基本帳號資料"
                  >
                    <span class="name-avatar-dot">👤</span>
                    <span class="name-text">{{ getDisplayName(u) }}</span>
                  </button>
                  <span v-if="u.is_self" class="self-tag">當前登入</span>
                </div>
              </td>

              <!-- 3. 帳號狀態 -->
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

              <!-- 5. 今日 AI 額度消耗 (次數 / Tokens + 一鍵重置) -->
              <td class="text-center">
                <!-- 專家與系統管理者：無上限 -->
                <div v-if="u.is_unlimited_quota" class="quota-cell-box unlimited">
                  <div class="q-top-line">
                    <span class="unlim-pill">∞ 無上限</span>
                    <span class="q-count-text">{{ u.today_questions }} 次</span>
                  </div>
                  <div class="q-token-text">
                    今日消耗 {{ (u.today_tokens || 0).toLocaleString() }} Tokens
                  </div>
                </div>

                <!-- 會員：顯示每日 10 次 / 50,000 Tokens 與進度條 -->
                <div v-else class="quota-cell-box" :class="getMemberQuotaBoxClass(u)">
                  <div class="q-top-line">
                    <span class="q-count-text">
                      <strong>{{ u.today_questions }}</strong> / {{ u.question_limit }} 次
                    </span>
                    <button
                      v-if="u.today_questions > 0 || u.today_tokens > 0"
                      class="reset-quota-btn"
                      :disabled="updatingUserId === u.id"
                      @click="handleResetUserQuota(u)"
                      title="將此帳號今日已使用的提問次數與 Token 歸零重置"
                    >
                      ↺ 重置
                    </button>
                  </div>

                  <div class="mini-progress-track">
                    <div
                      class="mini-progress-fill"
                      :class="getMemberQuotaBarClass(u)"
                      :style="{ width: getMemberQuotaPercent(u) + '%' }"
                    ></div>
                  </div>

                  <div class="q-token-text">
                    {{ (u.today_tokens || 0).toLocaleString() }} / {{ (u.token_limit || 50000).toLocaleString() }} Tokens
                  </div>
                </div>
              </td>

              <!-- 6. 權限角色 -->
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

              <!-- 7. 確認狀態 -->
              <td class="text-center">
                <span class="approval-badge" :class="getApprovalBadgeClass(u.approval_status)">
                  {{ formatApprovalLabel(u.approval_status) }}
                </span>
              </td>

              <!-- 8. 核定時間 (單行不換行) -->
              <td class="text-center time-cell">
                <span v-if="u.approved_at_tw" class="approved-time-text">
                  {{ u.approved_at_tw }}
                </span>
                <span v-else class="unapproved-dash">-- (待審核)</span>
              </td>

              <!-- 9. 審核操作按鈕 + 刪除申請人按鈕 -->
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
                  <button
                    class="delete-user-btn"
                    :disabled="u.is_self || updatingUserId === u.id"
                    @click="openDeleteUserModal(u)"
                    :title="u.is_self ? '無法刪除自己目前登入的管理員帳號' : '刪除此筆申請人帳號資料'"
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
        目前篩選條件下無符合的帳號申請紀錄。
      </div>

      <!-- 權限核准頁碼列 -->
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
              <th style="width: 56px; text-align: center;">#</th>
              <th style="width: 185px;">登入時間 (台灣時區)</th>
              <th>登入帳號 (Email)</th>
              <th style="width: 150px;">使用者姓名</th>
              <th style="width: 130px; text-align: center;">權限角色</th>
              <th style="width: 150px; text-align: center;">來源 IP 位址</th>
              <th style="width: 195px; text-align: center;">登入驗證結果</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(lg, idx) in paginatedLogs" :key="lg.id">
              <td class="text-center cell-index">
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

    <!-- ================= 彈出視窗 1：點擊姓名查看「詳細基本帳號資料」 ================= -->
    <transition name="modal-fade">
      <div v-if="isDetailModalOpen && selectedUser" class="modal-overlay" @click.self="closeUserDetailModal">
        <div class="detail-modal">
          <header class="detail-header">
            <div class="header-title-group">
              <span class="detail-icon">👤</span>
              <div>
                <span class="detail-subtitle">APPLICANT PROFILE / 基本帳號詳細資料</span>
                <h3 class="detail-title">{{ getDisplayName(selectedUser) }} 的帳號資訊</h3>
              </div>
            </div>
            <button class="close-btn" @click="closeUserDetailModal" title="關閉視窗">✕</button>
          </header>

          <div class="detail-body">
            <div class="profile-grid">
              <div class="profile-item full-row">
                <span class="p-label">📧 申請帳號（電子信箱 Email）</span>
                <strong class="p-value email-highlight">{{ selectedUser.email }}</strong>
              </div>

              <div class="profile-item">
                <span class="p-label">👤 申請人姓名（Name）</span>
                <strong class="p-value">{{ getDisplayName(selectedUser) }}</strong>
              </div>

              <div class="profile-item">
                <span class="p-label">📞 聯絡電話（Phone）</span>
                <span class="p-value">{{ selectedUser.phone && selectedUser.phone !== '--' ? selectedUser.phone : '未填寫' }}</span>
              </div>

              <div class="profile-item">
                <span class="p-label">🏢 服務單位（Organization）</span>
                <span class="p-value">{{ selectedUser.organization && selectedUser.organization !== '--' ? selectedUser.organization : '未填寫' }}</span>
              </div>

              <div class="profile-item">
                <span class="p-label">💼 職稱（Job Title）</span>
                <span class="p-value">{{ selectedUser.job_title && selectedUser.job_title !== '--' ? selectedUser.job_title : '未填寫' }}</span>
              </div>

              <div class="profile-item">
                <span class="p-label">🛡️ 權限角色（Role）</span>
                <span class="p-value">
                  <span class="role-pill" :class="getRoleSelectClass(selectedUser.role)">{{ selectedUser.role }}</span>
                </span>
              </div>

              <div class="profile-item">
                <span class="p-label">📋 確認狀態（Approval）</span>
                <span class="p-value">
                  <span class="approval-badge" :class="getApprovalBadgeClass(selectedUser.approval_status)">
                    {{ formatApprovalLabel(selectedUser.approval_status) }}
                  </span>
                </span>
              </div>

              <div class="profile-item">
                <span class="p-label">🕒 註冊申請時間（台灣時區）</span>
                <span class="p-value">{{ selectedUser.created_at_tw }}</span>
              </div>

              <div class="profile-item">
                <span class="p-label">✅ 審核核定時間（台灣時區）</span>
                <span class="p-value">{{ selectedUser.approved_at_tw || '尚在待審核階段' }}</span>
              </div>
            </div>
          </div>

          <footer class="detail-footer">
            <button class="got-it-btn" @click="closeUserDetailModal">關閉視窗</button>
          </footer>
        </div>
      </div>
    </transition>

    <!-- ================= 彈出視窗 2：刪除申請人帳號確認警告視窗 ================= -->
    <transition name="modal-fade">
      <div v-if="isDeleteModalOpen && userToDelete" class="modal-overlay" @click.self="closeDeleteUserModal">
        <div class="warn-modal">
          <header class="warn-header">
            <div class="header-title-group">
              <span class="warn-icon">!</span>
              <div>
                <span class="warn-subtitle">ACCOUNT DELETION WARNING / 刪除帳號確認</span>
                <h3 class="warn-title">確定要永久刪除此申請人帳號嗎？</h3>
              </div>
            </div>
            <button class="close-btn" @click="closeDeleteUserModal" title="取消並關閉">✕</button>
          </header>

          <div class="warn-body">
            <div class="target-summary-card">
              <div class="summary-item">
                <span class="s-label">申請人姓名：</span>
                <strong class="s-value">{{ getDisplayName(userToDelete) }} (User #{{ userToDelete.id }})</strong>
              </div>
              <div class="summary-item">
                <span class="s-label">帳號信箱與角色：</span>
                <span class="s-value">{{ userToDelete.email }} ｜ {{ userToDelete.role }} ({{ formatApprovalLabel(userToDelete.approval_status) }})</span>
              </div>
            </div>

            <p class="consequence-lead">執行刪除將會連帶執行以下操作，且<strong>無法復原</strong>：</p>
            <ul class="consequence-list">
              <li>
                <strong>永久移除申請人帳號 (<code>users</code> 資料表)</strong>：該帳號將從系統中徹底移除，無法再登入平臺。
              </li>
              <li>
                <strong>清除每日 AI 額度紀錄 (<code>user_daily_quotas</code> 資料表)</strong>：同步清除該帳號關聯之 Token 額度統計資料。
              </li>
              <li>
                <strong>保留歷史安全稽核軌跡 (<code>user_login_logs</code> 資料表)</strong>：過往的登入成功或失敗紀錄仍會保留於登入稽核表中，以利資安追蹤。
              </li>
            </ul>
          </div>

          <footer class="warn-footer">
            <button class="cancel-btn" :disabled="isDeletingUser" @click="closeDeleteUserModal">
              取消保留
            </button>
            <button class="confirm-delete-btn" :disabled="isDeletingUser" @click="confirmDeleteUser">
              {{ isDeletingUser ? '正在刪除帳號...' : '確認永久刪除' }}
            </button>
          </footer>
        </div>
      </div>
    </transition>

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
const quotaDateTw = ref('')
const isLoadingUsers = ref(false)
const updatingUserId = ref(null)
const approvalPage = ref(1)

const approvalFilters = reactive({
  keyword: '',
  role: 'ALL',
  approval_status: 'ALL',
  account_status: 'ALL'
})

// 申請人詳細基本資料彈窗狀態
const isDetailModalOpen = ref(false)
const selectedUser = ref(null)

// 刪除申請人確認警告彈窗狀態
const isDeleteModalOpen = ref(false)
const userToDelete = ref(null)
const isDeletingUser = ref(false)

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

const getDisplayName = (u) => {
  if (u.name && u.name !== '--') return u.name
  return u.email ? u.email.split('@')[0] : '未命名'
}

const openUserDetailModal = (user) => {
  selectedUser.value = user
  isDetailModalOpen.value = true
}

const closeUserDetailModal = () => {
  isDetailModalOpen.value = false
  selectedUser.value = null
}

const openDeleteUserModal = (user) => {
  userToDelete.value = user
  isDeleteModalOpen.value = true
}

const closeDeleteUserModal = () => {
  if (isDeletingUser.value) return
  isDeleteModalOpen.value = false
  userToDelete.value = null
}

const confirmDeleteUser = async () => {
  if (!userToDelete.value) return
  isDeletingUser.value = true
  const targetId = userToDelete.value.id

  try {
    const res = await fetch(`${API_BASE_URL}/admin/users/${targetId}`, {
      method: 'DELETE',
      credentials: 'include'
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || '刪除帳號失敗')

    userList.value = userList.value.filter(u => u.id !== targetId)
    if (paginatedUsers.value.length === 0 && approvalPage.value > 1) {
      approvalPage.value--
    }
    isDeleteModalOpen.value = false
    userToDelete.value = null
    await fetchUsers()
  } catch (err) {
    alert(err.message)
  } finally {
    isDeletingUser.value = false
  }
}

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
// 今日 AI 額度百分比與顏色計算
// =====================================================================
const getMemberQuotaPercent = (u) => {
  const qPct = u.question_limit ? (u.today_questions / u.question_limit) * 100 : 0
  const tPct = u.token_limit ? (u.today_tokens / u.token_limit) * 100 : 0
  return Math.min(100, Math.round(Math.max(qPct, tPct)))
}

const getMemberQuotaBoxClass = (u) => {
  const pct = getMemberQuotaPercent(u)
  if (pct >= 100) return 'q-box-danger'
  if (pct >= 80) return 'q-box-warning'
  return 'q-box-normal'
}

const getMemberQuotaBarClass = (u) => {
  const pct = getMemberQuotaPercent(u)
  if (pct >= 100) return 'bar-danger'
  if (pct >= 80) return 'bar-warning'
  return 'bar-normal'
}

// =====================================================================
// API 呼叫：權限核准管理與重置額度
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
    quotaDateTw.value = data.date_tw || ''
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

// 一鍵重置該名會員今日的 AI 提問次數與 Token 消耗
const handleResetUserQuota = async (user) => {
  updatingUserId.value = user.id
  try {
    const res = await fetch(`${API_BASE_URL}/admin/users/${user.id}/quota`, {
      method: 'DELETE',
      credentials: 'include'
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || '重置額度失敗')

    user.today_questions = 0
    user.today_tokens = 0
  } catch (err) {
    alert(err.message)
  } finally {
    updatingUserId.value = null
  }
}

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
    await fetchUsers()
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
  max-width: 1280px;
  margin: 20px auto 40px auto;
  padding: 0 20px;
}

.page-header {
  margin-bottom: 16px;
}

.main-title {
  color: white;
  font-size: 38px;
  margin-top: 4px;
  margin-bottom: 16px;
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

.btn-outline:hover { background-color: var(--light-color); }

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

.range-label { font-size: 14px; font-weight: 800; color: #1b1e29; }
.range-sub { font-size: 13.5px; font-weight: 700; color: #475569; }
.quick-date-btns { display: flex; gap: 8px; margin-left: auto; }

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

.summary-title { font-size: 17px; font-weight: 800; color: #2c3e50; }
.highlight-num { color: var(--dark-color); font-size: 19px; font-weight: 900; }
.legend-hint { font-size: 13px; font-weight: 700; color: #475569; }

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
  padding: 13px 12px;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.4px;
  white-space: nowrap;
}

.tox-table tbody tr {
  border-bottom: 1px solid #edf2f7;
  transition: background-color 0.15s;
}

.tox-table tbody tr:hover { background-color: #f8fafc; }
.tox-table tbody tr.pending-row { background-color: #fffaf0; }

.tox-table td {
  padding: 13px 12px;
  vertical-align: middle;
  font-size: 13.5px;
  color: #334155;
}

.text-center { text-align: center; }
.cell-index { font-weight: 800; color: #475569; }

/* 強制申請人姓名按鈕與『當前登入』徽章保持單行不換行 */
.name-cell-wrap {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: nowrap;
  white-space: nowrap;
}

.applicant-name-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  background-color: #f8fafc;
  color: #1b1e29;
  border: 1.5px solid #cbd5e1;
  padding: 6px 14px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 900;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  flex-shrink: 0;
}

.applicant-name-btn:hover {
  background-color: var(--light-color);
  border-color: var(--dark-color);
  color: var(--dark-color);
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.06);
}

.name-avatar-dot { font-size: 14px; line-height: 1; }
.name-text { text-decoration: underline; text-underline-offset: 3px; white-space: nowrap; }

.self-tag {
  background-color: #1b1e29;
  color: #f6d32d;
  font-size: 11px;
  font-weight: 800;
  padding: 2px 7px;
  border-radius: 6px;
  white-space: nowrap;
  flex-shrink: 0;
}

.user-email { font-weight: 900; color: #1b1e29; font-size: 14.5px; }

.status-toggle-btn {
  padding: 5px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
  white-space: nowrap;
}

.status-toggle-btn.acc-active { background-color: #dcfce7; color: #166534; border-color: #86efac; }
.status-toggle-btn.acc-disabled { background-color: #fee2e2; color: #991b1b; border-color: #fca5a5; }
.status-toggle-btn:disabled { opacity: 0.65; cursor: not-allowed; }

.login-count-badge {
  background-color: #f1f5f9;
  color: #1e293b;
  font-weight: 800;
  font-size: 12.5px;
  padding: 4px 9px;
  border-radius: 8px;
  white-space: nowrap;
}

/* 今日 AI 額度欄位樣式 */
.quota-cell-box {
  background-color: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 6px 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 158px;
  white-space: nowrap;
}

.quota-cell-box.unlimited { background-color: #f0fdf4; border-color: #86efac; }
.quota-cell-box.q-box-warning { background-color: #fffbeb; border-color: #fcd34d; }
.quota-cell-box.q-box-danger { background-color: #fef2f2; border-color: #fca5a5; }

.q-top-line { display: flex; justify-content: space-between; align-items: center; gap: 6px; }
.unlim-pill { background-color: #dcfce7; color: #166534; font-size: 11.5px; font-weight: 900; padding: 1px 7px; border-radius: 8px; }
.q-count-text { font-size: 12.5px; font-weight: 800; color: #1e293b; }

.reset-quota-btn {
  background-color: #ffffff;
  color: var(--dark-color);
  border: 1px solid var(--dark-color);
  padding: 1px 7px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.15s;
}

.reset-quota-btn:hover:not(:disabled) { background-color: var(--dark-color); color: #ffffff; }

.mini-progress-track { width: 100%; height: 6px; background-color: #e2e8f0; border-radius: 4px; overflow: hidden; }
.mini-progress-fill { height: 100%; border-radius: 4px; transition: width 0.3s ease; }
.bar-normal { background-color: var(--dark-color); }
.bar-warning { background-color: #f59e0b; }
.bar-danger { background-color: #ef4444; }
.q-token-text { font-size: 11px; color: #64748b; font-weight: 700; text-align: left; font-variant-numeric: tabular-nums; }

.role-select, .role-pill { padding: 5px 8px; border-radius: 8px; font-size: 12.5px; font-weight: 800; border: 1.5px solid transparent; white-space: nowrap; }
.role-admin { background-color: #fef3c7; color: #92400e; border-color: #f59e0b; }
.role-expert { background-color: #e0f2fe; color: #075985; border-color: #38bdf8; }
.role-member { background-color: #dcfce7; color: #166534; border-color: #4ade80; }
.role-guest { background-color: #f1f5f9; color: #64748b; border-color: #cbd5e1; }

.approval-badge { display: inline-block; padding: 5px 10px; border-radius: 6px; font-size: 12px; font-weight: 800; white-space: nowrap; }
.badge-pending { background-color: #ffca28; color: #1b1e29; }
.badge-approved { background-color: var(--dark-color); color: #ffffff; }
.badge-rejected { background-color: #ef5327; color: #ffffff; }

/* 核定時間保持單行不換行 */
.time-cell {
  font-variant-numeric: tabular-nums;
  font-size: 13px;
  white-space: nowrap;
}
.approved-time-text { color: #1b1e29; font-weight: 700; white-space: nowrap; }
.unapproved-dash { color: #94a3b8; font-weight: 600; font-size: 12px; white-space: nowrap; }

/* 審核操作按鈕群 + 刪除圓形按鈕 */
.audit-btn-group {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.audit-btn {
  padding: 5px 9px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
  border: 1.5px solid #cbd5e1;
  background-color: #ffffff;
  transition: all 0.2s;
  white-space: nowrap;
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

.audit-btn:disabled { opacity: 0.45; cursor: not-allowed; }

.delete-user-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1.5px solid #64748b;
  background-color: #ffffff;
  color: #334155;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  font-weight: 900;
  font-size: 12px;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.delete-user-btn:hover:not(:disabled) {
  background-color: #ffebee;
  color: #c62828;
  border-color: #c62828;
  transform: scale(1.08);
}

.delete-user-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.ip-code { background-color: #f1f5f9; color: #334155; padding: 3px 8px; border-radius: 6px; font-size: 13px; font-weight: 700; }
.log-result-badge { display: inline-block; padding: 4px 12px; border-radius: 6px; font-size: 12.5px; font-weight: 800; white-space: nowrap; }
.log-success { background-color: var(--dark-color); color: #ffffff; }
.log-guest { background-color: #e0f2f1; color: var(--dark-color); border: 1px solid var(--primary-color); }
.log-pending { background-color: #ffca28; color: #1b1e29; }
.log-failed { background-color: #ef5327; color: #ffffff; }

.empty-box {
  background-color: rgba(255, 255, 255, 0.75);
  border: 1.5px dashed var(--dark-color);
  border-radius: 14px;
  padding: 40px 20px;
  text-align: center;
  color: #475569;
  font-weight: 800;
}

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

.page-nav-btn, .page-num-btn {
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

.page-nav-btn:hover:not(:disabled), .page-num-btn:hover:not(.active) {
  background-color: var(--light-color);
  color: var(--dark-color);
}

.page-num-btn.active {
  background-color: var(--dark-color);
  color: #ffffff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.page-nav-btn:disabled { color: #b0bec5; cursor: not-allowed; }

/* ================= 彈出視窗共用遮罩與申請人詳細資料視窗樣式 ================= */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background-color: rgba(27, 30, 41, 0.65);
  backdrop-filter: blur(3px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2700;
  padding: 20px;
}

.detail-modal, .warn-modal {
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

.detail-header {
  background-color: #1b1e29;
  color: #ffffff;
  padding: 18px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 4px solid var(--dark-color);
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

.header-title-group {
  display: flex;
  align-items: center;
  gap: 14px;
}

.detail-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background-color: rgba(255, 255, 255, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
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
}

.detail-subtitle { font-size: 11px; letter-spacing: 1.2px; color: #94a3b8; font-weight: 800; display: block; }
.warn-subtitle { font-size: 11px; letter-spacing: 1.2px; color: #fca5a5; font-weight: 800; display: block; }
.detail-title, .warn-title { margin: 2px 0 0 0; font-size: 19px; font-weight: 800; color: #ffffff; }

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
}

.close-btn:hover { background-color: #e74c3c; color: #ffffff; }

.detail-body, .warn-body {
  padding: 22px 26px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.profile-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.profile-item {
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 11px 14px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.profile-item.full-row {
  grid-column: span 2;
  border-left: 4px solid var(--dark-color);
}

.p-label {
  font-size: 12px;
  font-weight: 800;
  color: #64748b;
}

.p-value {
  font-size: 14.5px;
  font-weight: 800;
  color: #1e293b;
  word-break: break-all;
}

.email-highlight {
  font-size: 15.5px;
  color: var(--dark-color);
}

.detail-footer, .warn-footer {
  padding: 14px 26px;
  background-color: #f8fafc;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.got-it-btn {
  background-color: #1b1e29;
  color: #ffffff;
  border: none;
  padding: 9px 26px;
  border-radius: 8px;
  font-size: 14.5px;
  font-weight: 800;
  cursor: pointer;
}

.got-it-btn:hover { background-color: var(--dark-color); }

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

.summary-item { font-size: 14.5px; color: #334155; }
.s-label { color: #64748b; font-weight: 700; }
.s-value { color: #1b1e29; font-weight: 800; }
.consequence-lead { margin: 2px 0 0 0; font-size: 14.5px; color: #334155; }

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

.cancel-btn {
  background-color: #ffffff;
  color: #475569;
  border: 1.5px solid #cbd5e1;
  padding: 9px 22px;
  border-radius: 8px;
  font-size: 14.5px;
  font-weight: 800;
  cursor: pointer;
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
  box-shadow: 0 4px 10px rgba(231, 76, 60, 0.25);
}

.confirm-delete-btn:hover:not(:disabled) { background-color: #c0392b; }

.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity 0.2s ease; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
</style>