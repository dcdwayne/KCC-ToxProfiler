<template>
  <transition name="modal-fade">
    <div v-if="authState.isAuthModalOpen" class="auth-overlay" @click.self="closeAuthModal">
      <div class="auth-modal">
        <!-- 頂部深色標題列 -->
        <header class="auth-header">
          <div class="header-title-group">
            <span class="auth-icon">{{ isLoginMode ? '🔐' : '📝' }}</span>
            <div>
              <span class="auth-subtitle">
                {{ isLoginMode ? 'USER AUTHENTICATION / 系統登入' : 'ACCOUNT APPLICATION / 權限註冊申請' }}
              </span>
              <h3 class="auth-title">
                {{ isLoginMode ? '登入 KCC ToxProfiler 評估平臺' : '申請註冊與預選權限角色' }}
              </h3>
            </div>
          </div>
          <button class="close-btn" @click="closeAuthModal" title="關閉視窗">✕</button>
        </header>

        <!-- ================= 模式 A：登入表單 ================= -->
        <form v-if="isLoginMode" class="auth-body" @submit.prevent="handleLoginSubmit">
          <div class="field-group">
            <label>帳號（電子信箱 Email）<span class="req">*</span></label>
            <input
              type="email"
              v-model.trim="loginForm.email"
              placeholder="請輸入您的電子信箱，如 user@example.com"
              class="auth-input"
              required
            />
          </div>

          <div class="field-group">
            <label>密碼（Password）<span class="req">*</span></label>
            <div class="pwd-input-wrapper">
              <input
                :type="showLoginPwd ? 'text' : 'password'"
                v-model="loginForm.password"
                placeholder="請輸入密碼"
                class="auth-input pwd-input"
                required
              />
              <!-- 顯示/隱藏密碼的眼睛圖示按鈕 -->
              <button
                type="button"
                class="eye-btn"
                @click="showLoginPwd = !showLoginPwd"
                :title="showLoginPwd ? '隱藏密碼' : '顯示密碼'"
              >
                <svg v-if="!showLoginPwd" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
                <svg v-else viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                  <line x1="1" y1="1" x2="23" y2="23" />
                </svg>
              </button>
            </div>
          </div>

          <button type="submit" class="submit-auth-btn" :disabled="isSubmitting">
            {{ isSubmitting ? '驗證登入中...' : '確認登入系統' }}
          </button>

          <!-- 下方備註區 (1. 訪客進入 / 2. 登入失敗或狀態訊息 / 3. 還沒有註冊嗎？) -->
          <div class="auth-notes-box">
            <!-- 備註 2：若登入失敗或有系統提示，於此處醒目顯示 -->
            <div v-if="feedbackMsg" class="feedback-banner" :class="feedbackType">
              <span>{{ feedbackType === 'error' ? '⚠️' : '✅' }}</span>
              <span>{{ feedbackMsg }}</span>
            </div>

            <div class="notes-links-row">
              <!-- 備註 1：以『訪客』身份進入 -->
              <button type="button" class="note-link-btn guest-btn" @click="handleEnterAsGuest">
                👤 1. 以『訪客』身份進入（僅瀏覽 AI 導覽按鈕）
              </button>

              <!-- 備註 3：還沒有註冊嗎？ -->
              <button type="button" class="note-link-btn switch-btn" @click="switchMode('register')">
                ✨ 還沒有註冊嗎？點此申請帳號 →
              </button>
            </div>
          </div>
        </form>

        <!-- ================= 模式 B：註冊申請表單 ================= -->
        <form v-else class="auth-body" @submit.prevent="handleRegisterSubmit">
          <!-- 必填區塊 -->
          <div class="form-grid-2">
            <div class="field-group">
              <label>申請帳號（電子信箱）<span class="req">*</span></label>
              <input
                type="email"
                v-model.trim="regForm.email"
                placeholder="example@domain.com"
                class="auth-input"
                required
              />
            </div>

            <div class="field-group">
              <label>設定密碼（至少 6 碼）<span class="req">*</span></label>
              <div class="pwd-input-wrapper">
                <input
                  :type="showRegPwd ? 'text' : 'password'"
                  v-model="regForm.password"
                  placeholder="請輸入 6 碼以上密碼"
                  class="auth-input pwd-input"
                  required
                />
                <button
                  type="button"
                  class="eye-btn"
                  @click="showRegPwd = !showRegPwd"
                  :title="showRegPwd ? '隱藏密碼' : '顯示密碼'"
                >
                  <svg v-if="!showRegPwd" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                  <svg v-else viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <!-- 點選預申請的權限角色 -->
          <div class="field-group">
            <label>點選預申請之權限角色 <span class="req">*</span></label>
            <div class="role-selector-grid">
              <button
                type="button"
                class="role-option-card"
                :class="{ active: regForm.role === '會員' }"
                @click="regForm.role = '會員'"
              >
                <div class="role-card-head">
                  <span class="role-dot"></span>
                  <strong>會員 (Member)</strong>
                </div>
                <span class="role-desc">可使用 Dr. Manhattan 智能助理按鈕導覽與自由輸入提問功能</span>
              </button>

              <button
                type="button"
                class="role-option-card"
                :class="{ active: regForm.role === '專家' }"
                @click="regForm.role = '專家'"
              >
                <div class="role-card-head">
                  <span class="role-dot"></span>
                  <strong>專家 (Expert)</strong>
                </div>
                <span class="role-desc">開放完整文獻檢索、10 KCC 系統回顧、統合分析與歷史紀錄管理</span>
              </button>
            </div>
          </div>

          <!-- 選填基本資料區塊 (單位、姓名、職稱、電話 預設非必填) -->
          <div class="optional-divider">
            <span>申請人基本資料（選填 Optional）</span>
          </div>

          <div class="form-grid-2">
            <div class="field-group">
              <label>服務單位（Organization）</label>
              <input
                type="text"
                v-model.trim="regForm.organization"
                placeholder="例如：國家環境研究院 / 大學系所"
                maxlength="50"
                class="auth-input"
              />
            </div>

            <div class="field-group">
              <label>真實姓名（Name）</label>
              <input
                type="text"
                v-model.trim="regForm.name"
                placeholder="請輸入您的姓名"
                maxlength="30"
                class="auth-input"
              />
            </div>

            <div class="field-group">
              <label>職稱（Job Title）</label>
              <input
                type="text"
                v-model.trim="regForm.job_title"
                placeholder="例如：研究員 / 毒理學分析師"
                maxlength="40"
                class="auth-input"
              />
            </div>

            <div class="field-group">
              <label>聯絡電話（Phone）</label>
              <input
                type="tel"
                v-model.trim="regForm.phone"
                placeholder="例如：02-23456789 或手機"
                maxlength="20"
                class="auth-input"
              />
            </div>
          </div>

          <button type="submit" class="submit-auth-btn" :disabled="isSubmitting">
            {{ isSubmitting ? '正在送出申請...' : '送出註冊與權限申請' }}
          </button>

          <!-- 底部訊息與切換回登入 -->
          <div class="auth-notes-box">
            <div v-if="feedbackMsg" class="feedback-banner" :class="feedbackType">
              <span>{{ feedbackType === 'error' ? '⚠️' : '✅' }}</span>
              <span>{{ feedbackMsg }}</span>
            </div>

            <div class="notes-links-row">
              <button type="button" class="note-link-btn guest-btn" @click="handleEnterAsGuest">
                👤 先以『訪客』身份進入體驗
              </button>
              <button type="button" class="note-link-btn switch-btn" @click="switchMode('login')">
                ← 已經有帳號了？返回登入頁面
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { authState, closeAuthModal } from '../utils/authStore'

const router = useRouter()

const API_BASE_URL = window.location.port === '5173'
  ? `http://${window.location.hostname}:8000/api`
  : '/api'

const EMAIL_PATTERN = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/

const isLoginMode = computed(() => authState.authModalMode === 'login')

const showLoginPwd = ref(false)
const showRegPwd = ref(false)
const isSubmitting = ref(false)

const feedbackMsg = ref('')
const feedbackType = ref('error') // 'error' | 'success'

const loginForm = reactive({
  email: '',
  password: ''
})

const regForm = reactive({
  email: '',
  password: '',
  role: '會員',
  organization: '',
  name: '',
  job_title: '',
  phone: ''
})

watch(
  () => authState.authModalMessage,
  (newMsg) => {
    if (newMsg) {
      feedbackMsg.value = newMsg
      feedbackType.value = 'error'
    }
  },
  { immediate: true }
)

const switchMode = (targetMode) => {
  feedbackMsg.value = ''
  authState.authModalMode = targetMode
}

// 1. 執行登入
const handleLoginSubmit = async () => {
  feedbackMsg.value = ''
  if (!EMAIL_PATTERN.test(loginForm.email)) {
    feedbackType.value = 'error'
    feedbackMsg.value = '帳號格式不正確：請輸入有效的電子信箱（如 example@domain.com）！'
    return
  }

  isSubmitting.value = true
  try {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(loginForm)
    })
    const data = await res.json()
    if (!res.ok) {
      feedbackType.value = 'error'
      feedbackMsg.value = data.detail || '登入失敗，請檢查帳號與密碼。'
      return
    }

    // 登入成功，更新全域狀態並依角色導向適合頁面
    authState.isAuthenticated = true
    authState.isGuest = false
    authState.user = data.user
    loginForm.password = ''
    closeAuthModal()

    if (data.user.role === '會員') {
      router.push('/chat')
    } else {
      router.push('/')
    }
  } catch (err) {
    feedbackType.value = 'error'
    feedbackMsg.value = '無法連線至後端驗證伺服器，請稍後再試。'
  } finally {
    isSubmitting.value = false
  }
}

// 2. 以『訪客』身份進入
const handleEnterAsGuest = async () => {
  isSubmitting.value = true
  try {
    const res = await fetch(`${API_BASE_URL}/auth/guest`, {
      method: 'POST',
      credentials: 'include'
    })
    const data = await res.json()
    if (res.ok) {
      authState.isAuthenticated = false
      authState.isGuest = true
      authState.user = data.user
      closeAuthModal()
      router.push('/chat')
    }
  } catch (err) {
    console.error('切換訪客失敗:', err)
  } finally {
    isSubmitting.value = false
  }
}

// 3. 執行註冊申請
const handleRegisterSubmit = async () => {
  feedbackMsg.value = ''
  if (!EMAIL_PATTERN.test(regForm.email)) {
    feedbackType.value = 'error'
    feedbackMsg.value = '申請帳號必須為有效的電子信箱格式（如 name@domain.com）！'
    return
  }
  if (regForm.password.length < 6) {
    feedbackType.value = 'error'
    feedbackMsg.value = '密碼長度至少需 6 個字元以上！'
    return
  }

  isSubmitting.value = true
  try {
    const res = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(regForm)
    })
    const data = await res.json()
    if (!res.ok) {
      feedbackType.value = 'error'
      feedbackMsg.value = data.detail || '註冊申請失敗，請檢查輸入欄位。'
      return
    }

    // 註冊成功，切換回登入模式並顯示成功提示於下方備註區
    loginForm.email = regForm.email
    loginForm.password = ''
    regForm.password = ''
    authState.authModalMode = 'login'
    feedbackType.value = 'success'
    feedbackMsg.value = data.message
  } catch (err) {
    feedbackType.value = 'error'
    feedbackMsg.value = '伺服器連線異常，請稍後再試。'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.auth-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background-color: rgba(27, 30, 41, 0.65);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2800;
  padding: 20px;
}

.auth-modal {
  background-color: #ffffff;
  width: 95%;
  max-width: 560px;
  max-height: 90vh;
  border-radius: 18px;
  box-shadow: 0 20px 45px rgba(0, 0, 0, 0.28);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

.auth-header {
  background-color: #1b1e29;
  color: #ffffff;
  padding: 18px 26px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 4px solid var(--primary-color);
}

.header-title-group {
  display: flex;
  align-items: center;
  gap: 14px;
}

.auth-icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background-color: rgba(255, 255, 255, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.auth-subtitle {
  font-size: 11px;
  letter-spacing: 1.2px;
  color: #94a3b8;
  font-weight: 800;
  display: block;
}

.auth-title {
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
}

.close-btn:hover {
  background-color: #e74c3c;
  color: #ffffff;
}

.auth-body {
  padding: 24px 28px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-group label {
  font-size: 13.5px;
  font-weight: 800;
  color: #2c3e50;
}

.req {
  color: #e74c3c;
  margin-left: 2px;
}

.auth-input {
  width: 100%;
  box-sizing: border-box;
  padding: 10px 14px;
  border: 1.5px solid #cbd5e1;
  border-radius: 10px;
  font-size: 14.5px;
  font-weight: 600;
  color: #1e293b;
  outline: none;
  transition: all 0.2s;
}

.auth-input:focus {
  border-color: var(--dark-color);
  box-shadow: 0 0 0 3px rgba(45, 114, 127, 0.12);
}

/* 密碼框與眼睛按鈕容器 */
.pwd-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.pwd-input {
  padding-right: 42px;
}

.eye-btn {
  position: absolute;
  right: 10px;
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.eye-btn:hover {
  color: var(--dark-color);
}

/* 預申請角色選擇卡 */
.role-selector-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.role-option-card {
  background-color: #f8fafc;
  border: 1.5px solid #cbd5e1;
  border-radius: 12px;
  padding: 12px 14px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.role-option-card:hover {
  border-color: var(--dark-color);
}

.role-option-card.active {
  background-color: var(--light-color);
  border: 2px solid var(--dark-color);
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.06);
}

.role-card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14.5px;
  color: #1b1e29;
}

.role-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid #94a3b8;
}

.role-option-card.active .role-dot {
  background-color: var(--dark-color);
  border-color: var(--dark-color);
}

.role-desc {
  font-size: 12px;
  color: #475569;
  line-height: 1.45;
  font-weight: 600;
}

.optional-divider {
  display: flex;
  align-items: center;
  text-align: center;
  color: #64748b;
  font-size: 12px;
  font-weight: 800;
  margin: 4px 0 0 0;
}

.optional-divider::before,
.optional-divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px dashed #cbd5e1;
}

.optional-divider span {
  padding: 0 10px;
}

.submit-auth-btn {
  background-color: #1b1e29;
  color: #ffffff;
  border: none;
  padding: 12px 24px;
  border-radius: 10px;
  font-size: 15.5px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 4px;
}

.submit-auth-btn:hover:not(:disabled) {
  background-color: var(--dark-color);
}

.submit-auth-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 下方備註區 */
.auth-notes-box {
  margin-top: 4px;
  padding-top: 14px;
  border-top: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.feedback-banner {
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13.5px;
  font-weight: 700;
  line-height: 1.5;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.feedback-banner.error {
  background-color: #fff5f5;
  border: 1.5px solid #feb2b2;
  color: #c53030;
}

.feedback-banner.success {
  background-color: #e6fcf5;
  border: 1.5px solid #63e6be;
  color: #087f5b;
}

.notes-links-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.note-link-btn {
  background: transparent;
  border: none;
  font-size: 13.5px;
  font-weight: 800;
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 6px;
  transition: all 0.2s;
}

.guest-btn {
  color: #475569;
  background-color: #f1f5f9;
}

.guest-btn:hover {
  background-color: #e2e8f0;
  color: #1b1e29;
}

.switch-btn {
  color: var(--dark-color);
}

.switch-btn:hover {
  background-color: var(--light-color);
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