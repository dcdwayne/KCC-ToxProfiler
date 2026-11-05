<template>
  <main class="chat-page">
    <div class="chat-window">
      <!-- 1. 頂部標題列 -->
      <header class="chat-topbar">
        <div class="topbar-left">
          <span class="status-dot"></span>
          <span class="assistant-badge">AI ADVISOR</span>
        </div>
        <h2 class="topbar-title">危害辨識導覽員 Dr. Manhattan</h2>
        <button class="reset-top-btn" @click="restartConversation" title="重新開始對話導覽">
          ↻ 重新導覽
        </button>
      </header>

      <!-- 2. 訊息滾動區 -->
      <div class="chat-Viewport" ref="chatViewportRef" @scroll="handleScroll" @click="isQuotaPopoverOpen = false">
        <div 
          v-for="msg in messages" 
          :key="msg.id" 
          class="message-row"
          :class="msg.sender === 'user' ? 'row-user' : 'row-ai'"
        >
          <!-- ================= AI (Dr. Manhattan) 訊息區塊 ================= -->
          <template v-if="msg.sender === 'ai'">
            <!-- 左側圓形小頭像 (預留 Dr. Manhattan 頭像空間 1) -->
            <div class="ai-avatar-circle">
              <img v-if="DR_MANHATTAN_AVATAR_HEAD" :src="DR_MANHATTAN_AVATAR_HEAD" alt="Dr. Manhattan" class="avatar-img" />
              <span v-else class="avatar-fallback">⚛️</span>
            </div>

            <div class="ai-content-col">
              <!-- 首則歡迎訊息專屬大頭貼立繪預留區 -->
              <div v-if="msg.isHeroGreeting" class="hero-mascot-box">
                <div class="hero-avatar-frame">
                  <span class="hello-tag">HELLO!</span>
                  <img v-if="DR_MANHATTAN_AVATAR" :src="DR_MANHATTAN_AVATAR" alt="Dr. Manhattan Hero" class="hero-img" />
                  <div v-else class="hero-placeholder">
                    <span class="atom-symbol">⚛️</span>
                    <span class="placeholder-hint">Dr. Manhattan</span>
                  </div>
                </div>
                <div class="hero-intro-tag">
                  <strong>Dr. Manhattan 已上線</strong>
                  <span>已連結 FastMCP 實證毒理知識庫</span>
                </div>
              </div>

              <!-- AI 白色文字氣泡 -->
              <div class="ai-bubble">
                <div v-if="msg.chapterTitle" class="bubble-chapter-title">
                  {{ msg.chapterTitle }}
                </div>
                <div class="bubble-html" v-html="msg.html"></div>
              </div>

              <!-- 情境 A：快速按鈕選單 (Step 1 角色選擇 / Step 2 化學物質選擇) -->
              <div v-if="msg.quickButtons && msg.quickButtons.length > 0" class="quick-btn-group">
                <button
                  v-for="btn in msg.quickButtons"
                  :key="btn.label"
                  class="choice-chip-btn"
                  :disabled="isThinking"
                  @click="handleQuickButtonClick(btn)"
                >
                  {{ btn.label }}
                </button>
              </div>

              <!-- 情境 B：多欄式主題卡片選單 (Step 3 主題選擇) -->
              <div v-if="msg.topicCards && msg.topicCards.length > 0" class="alpha-card-deck">
                <div class="alpha-card">
                  <div class="alpha-card-illust">
                    <div class="illust-circle">🔬</div>
                    <h4 class="alpha-card-title">
                      {{ currentRole === '專家' ? '專家版法規毒理核心章節' : '民眾版科普風險核心主題' }}
                    </h4>
                    <span class="alpha-card-sub">
                      目標物質：{{ currentChemical?.chemical_name_zh }} ({{ currentChemical?.hazard_score }}分)
                    </span>
                  </div>
                  <div class="alpha-card-actions">
                    <button
                      v-for="(topic, tIdx) in msg.topicCards"
                      :key="topic"
                      class="alpha-topic-btn"
                      :disabled="isThinking"
                      @click="handleSelectTopic(topic, tIdx)"
                    >
                      {{ topic }}
                    </button>
                  </div>
                </div>

                <!-- 第二張輔助操作卡 -->
                <div class="alpha-card secondary-card">
                  <div class="alpha-card-illust">
                    <div class="illust-circle alt">🧭</div>
                    <h4 class="alpha-card-title">進階探索與切換</h4>
                    <span class="alpha-card-sub">當前視角：{{ currentRole }}</span>
                  </div>
                  <div class="alpha-card-actions">
                    <button class="alpha-topic-btn" :disabled="isThinking" @click="promptSwitchChemical">
                      切換關注化學物質
                    </button>
                    <button class="alpha-topic-btn" :disabled="isThinking" @click="restartConversation">
                      重新選擇角色視角 ({{ currentRole === '專家' ? '改為一般民眾' : '改為專家' }})
                    </button>
                    <!-- 僅專家與系統管理者顯示或允許跳轉歷史紀錄 -->
                    <button v-if="canGoHistory" class="alpha-topic-btn" @click="handleHistoryCardClick">
                      前往歷史紀錄勾選管理
                    </button>
                  </div>
                </div>
              </div>

              <!-- 送出時間戳記与單次 Token 消耗小標記 -->
              <div class="msg-meta-foot">
                <span class="msg-time">{{ msg.time }} 送出</span>
                <span v-if="msg.tokenCost" class="token-cost-pill">⚡ 本次消耗 {{ msg.tokenCost }} Tokens</span>
              </div>
            </div>
          </template>

          <!-- ================= 使用者右側訊息氣泡 ================= -->
          <template v-else>
            <div class="user-content-col">
              <div class="user-bubble">
                {{ msg.text }}
              </div>
              <span class="msg-time user-time">{{ msg.time }}</span>
            </div>
          </template>
        </div>

        <!-- Dr. Manhattan 思考中動態指示器 -->
        <div v-if="isThinking" class="message-row row-ai">
          <div class="ai-avatar-circle">
            <img v-if="DR_MANHATTAN_AVATAR_THINKING" :src="DR_MANHATTAN_AVATAR_THINKING" alt="Dr. Manhattan" class="avatar-img" />
            <span v-else class="avatar-fallback">⚛️</span>
          </div>
          <div class="ai-content-col">
            <div class="ai-bubble thinking-bubble">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="thinking-text">Dr. Manhattan 正在檢索評估報告...</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右下角懸浮「滑至最底」按鈕 -->
      <button 
        v-show="showScrollBottomBtn" 
        class="scroll-bottom-fab" 
        @click="scrollToBottom"
        title="滑動至最新訊息"
      >
        ⌄
      </button>

      <!-- ⚠️ 會員高額度預警 / 額度用盡警示條 (當達 80% 或 100% 時自動浮現於輸入框上方) -->
      <div 
        v-if="quotaInfo.warning_message && (quotaInfo.quota_status === 'WARNING' || quotaInfo.quota_status === 'EXHAUSTED')" 
        class="quota-alert-banner"
        :class="quotaInfo.quota_status === 'EXHAUSTED' ? 'alert-danger' : 'alert-warning'"
      >
        <span>{{ quotaInfo.warning_message }}</span>
        <button class="alert-detail-btn" @click="isQuotaPopoverOpen = true">查看額度明細</button>
      </div>

      <!-- 📊 點擊左下角按鈕彈出的「今日剩餘次數 / 剩餘 Token 數」小視窗 (Quota Popover) -->
      <transition name="popover-fade">
        <div v-if="isQuotaPopoverOpen" class="quota-popover-card">
          <div class="qp-header">
            <div class="qp-title-row">
              <span class="qp-icon">⚡</span>
              <div>
                <h4>今日 AI 問答額度追蹤 (Quota Tracking)</h4>
                <span class="qp-sub">統計日期（台灣時區）：{{ quotaInfo.date_tw || '今日' }}</span>
              </div>
            </div>
            <button class="qp-close" @click="isQuotaPopoverOpen = false">✕</button>
          </div>

          <div class="qp-body">
            <div class="qp-role-row">
              <span>目前帳號身分：</span>
              <strong class="qp-role-badge" :class="getQuotaRoleClass(quotaInfo.role)">
                {{ quotaInfo.role }}
              </strong>
            </div>

            <!-- 情況 A：專家或系統管理者 (無限制) -->
            <div v-if="quotaInfo.is_unlimited" class="qp-unlimited-box">
              <div class="unlim-title">👑 尊榮無限額度權限 (Unlimited)</div>
              <p>您身為<strong>「{{ quotaInfo.role }}」</strong>，享有不限次數與 Token 之自由提問權限。</p>
              <div class="unlim-stats">
                <span>今日已發問：<strong>{{ quotaInfo.question_used }}</strong> 次</span>
                <span>｜</span>
                <span>今日累計消耗：<strong>{{ (quotaInfo.tokens_used || 0).toLocaleString() }}</strong> Tokens</span>
              </div>
            </div>

            <!-- 情況 B：一般會員 (顯示每日 10 次 & 50,000 Tokens 雙進度條) -->
            <div v-else-if="quotaInfo.role === '會員'" class="qp-meters-box">
              <!-- 指標 1：今日剩餘發問次數 -->
              <div class="meter-group">
                <div class="meter-label-row">
                  <span>1. 今日剩餘發問次數</span>
                  <strong>剩餘 <span class="rem-highlight">{{ quotaInfo.question_remaining }}</span> / {{ quotaInfo.question_limit }} 次</strong>
                </div>
                <div class="progress-track">
                  <div 
                    class="progress-fill" 
                    :class="getProgressColorClass(questionUsagePercent)"
                    :style="{ width: questionUsagePercent + '%' }"
                  ></div>
                </div>
                <span class="meter-foot">已發問 {{ quotaInfo.question_used }} 次（每日上限 10 次）</span>
              </div>

              <!-- 指標 2：今日剩餘 Token 數 -->
              <div class="meter-group">
                <div class="meter-label-row">
                  <span>2. 今日剩餘 Token 額度</span>
                  <strong>剩餘 <span class="rem-highlight">{{ (quotaInfo.tokens_remaining || 0).toLocaleString() }}</span> Tokens</strong>
                </div>
                <div class="progress-track">
                  <div 
                    class="progress-fill" 
                    :class="getProgressColorClass(tokenUsagePercent)"
                    :style="{ width: tokenUsagePercent + '%' }"
                  ></div>
                </div>
                <span class="meter-foot">
                  已消耗 {{ (quotaInfo.tokens_used || 0).toLocaleString() }} / {{ (quotaInfo.tokens_limit || 50000).toLocaleString() }} Tokens
                </span>
              </div>
            </div>

            <!-- 情況 C：訪客模式 -->
            <div v-else class="qp-guest-box">
              <p>🔒 <strong>訪客模式未開放自由輸入框提問</strong>（0 Token 消耗保護機制）。</p>
              <p>您可無限次點擊對話視窗中的「預設主題卡片按鈕」瀏覽報告，或點擊下方按鈕登入會員／專家帳號以解鎖自由提問！</p>
              <button class="qp-login-btn" @click="isQuotaPopoverOpen = false; openAuthModal('login')">
                立即登入 / 註冊帳號
              </button>
            </div>

            <!-- 額度規則小說明 -->
            <ul class="qp-rules-list">
              <li>💡 <strong>零消耗技巧</strong>：直接點擊對話框中的「主題卡片按鈕」屬於章節快取調閱，<strong>不計入發問次數且消耗 0 Token</strong>。</li>
              <li>🕛 <strong>重置時間</strong>：會員每日額度（10 次或 50,000 Tokens）於台灣時間 <strong>00:00</strong> 自動重置。</li>
            </ul>
          </div>
        </div>
      </transition>

      <!-- 3. 底部固定輸入列 (左側改造為『額度追蹤按鈕』+ 圓角輸入框 + 右側發送鈕) -->
      <footer class="chat-input-bar">
        <!-- 改造後的左下角按鈕：點擊開啟/關閉今日剩餘次數與 Token 彈出視窗 -->
        <button 
          class="quota-trigger-btn" 
          :class="getQuotaBtnStatusClass()"
          @click="toggleQuotaPopover" 
          title="點擊查看今日剩餘提問次數與 Token 額度"
        >
          <span class="q-dot"></span>
          <span class="q-icon">⚡</span>
          <span class="q-text">
            <template v-if="quotaInfo.is_unlimited">額度 ∞</template>
            <template v-else-if="quotaInfo.role === '會員'">剩 {{ quotaInfo.question_remaining }} 次</template>
            <template v-else>額度說明</template>
          </span>
        </button>

        <input
          type="text"
          v-model="userInput"
          class="chat-text-input"
          :placeholder="getInputPlaceholder()"
          :disabled="isInputDisabled"
          @keyup.enter="handleSendFreeText"
        />

        <button 
          class="send-circle-btn" 
          :disabled="isInputDisabled || !userInput.trim()"
          @click="handleSendFreeText"
          title="送出問題"
        >
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </footer>
    </div>
  </main>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { authState, openAuthModal } from '../utils/authStore'

const router = useRouter()

const API_BASE_URL = window.location.port === '5173'
  ? `http://${window.location.hostname}:8000/api`
  : '/api'

// =====================================================================
// 👇👇👇 【Dr. Manhattan 大頭貼圖片設定區】 👇👇👇
// 之後只要將圖片放入 frontend/public/ 資料夾 (例如命名為 dr-manhattan.png)，
// 並將下方空字串改為 '/dr-manhattan.png'，大頭貼與左側圓形頭像就會自動生效！
// =====================================================================
const DR_MANHATTAN_AVATAR = '/dr-manhattan.png'
const DR_MANHATTAN_AVATAR_HEAD = '/dr-manhattan-head.png'
const DR_MANHATTAN_AVATAR_THINKING = '/dr-manhattan-thinking.png'

const chatViewportRef = ref(null)
const messages = ref([])
const userInput = ref('')
const isThinking = ref(false)
const showScrollBottomBtn = ref(false)

// 左下角額度小彈窗開關與額度資料狀態
const isQuotaPopoverOpen = ref(false)
const quotaInfo = reactive({
  role: '訪客',
  date_tw: '',
  is_unlimited: false,
  can_ask: false,
  question_used: 0,
  question_limit: 10,
  question_remaining: 10,
  tokens_used: 0,
  tokens_limit: 50000,
  tokens_remaining: 50000,
  quota_status: 'GUEST_LOCKED', // 'UNLIMITED' | 'NORMAL' | 'WARNING' | 'EXHAUSTED' | 'GUEST_LOCKED'
  warning_message: null
})

// 當前對話狀態記憶
const currentRole = ref(null)
const currentChemical = ref(null)
const selectedChemicalsList = ref([])

let msgIdCounter = 1

// --- RBAC 與額度計算 ---
const isVisitorMode = computed(() => {
  return !authState.isAuthenticated || authState.user?.role === '訪客'
})

const canGoHistory = computed(() => {
  const r = authState.user?.role
  return r === '系統管理者' || r === '專家'
})

const isQuotaExhausted = computed(() => {
  return quotaInfo.role === '會員' && !quotaInfo.can_ask
})

const isInputDisabled = computed(() => {
  return isVisitorMode.value || isQuotaExhausted.value || !currentChemical.value || isThinking.value
})

const questionUsagePercent = computed(() => {
  if (!quotaInfo.question_limit) return 0
  return Math.min(100, Math.round((quotaInfo.question_used / quotaInfo.question_limit) * 100))
})

const tokenUsagePercent = computed(() => {
  if (!quotaInfo.tokens_limit) return 0
  return Math.min(100, Math.round((quotaInfo.tokens_used / quotaInfo.tokens_limit) * 100))
})

const getInputPlaceholder = () => {
  if (isVisitorMode.value) {
    return '🔒 訪客模式僅開放點選上方主題按鈕（請點右上角「登入」會員或專家帳號以開啟自由提問）'
  }
  if (isQuotaExhausted.value) {
    return '🚫 您今日的會員免費發問額度（10 次或 50,000 Tokens）已用盡，請點擊上方主題按鈕查閱報告'
  }
  if (!currentChemical.value) {
    return '請先點擊上方按鈕選擇您的角色視角與關注化學物質...'
  }
  return `針對「${currentChemical.value.chemical_name_zh}」評估報告向 Dr. Manhattan 提問（單次限 200 字）...`
}

// 取得最新額度狀態 (GET /api/chat/quota)
const fetchQuotaStatus = async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/chat/quota`, {
      credentials: 'include'
    })
    if (res.ok) {
      const data = await res.json()
      Object.assign(quotaInfo, data)
    }
  } catch (err) {
    console.error('載入額度狀態失敗:', err)
  }
}

// 當使用者登入/登出切換身分時，自動重新同步額度
watch(
  () => authState.user,
  () => {
    fetchQuotaStatus()
  },
  { deep: true }
)

const toggleQuotaPopover = async () => {
  if (!isQuotaPopoverOpen.value) {
    await fetchQuotaStatus()
  }
  isQuotaPopoverOpen.value = !isQuotaPopoverOpen.value
}

const getQuotaBtnStatusClass = () => {
  if (quotaInfo.quota_status === 'EXHAUSTED') return 'q-btn-danger'
  if (quotaInfo.quota_status === 'WARNING') return 'q-btn-warning'
  if (quotaInfo.quota_status === 'UNLIMITED') return 'q-btn-unlimited'
  return 'q-btn-normal'
}

const getProgressColorClass = (pct) => {
  if (pct >= 100) return 'fill-danger'
  if (pct >= 80) return 'fill-warning'
  return 'fill-normal'
}

const getQuotaRoleClass = (role) => {
  if (role === '系統管理者') return 'q-role-admin'
  if (role === '專家') return 'q-role-expert'
  if (role === '會員') return 'q-role-member'
  return 'q-role-guest'
}

const handleHistoryCardClick = () => {
  if (canGoHistory.value) {
    router.push('/history')
  } else {
    alert('⚠️ 權限提示：「歷史紀錄勾選管理」僅開放【專家】與【系統管理者】使用！')
  }
}

const getCurrentTimeStr = () => {
  const now = new Date()
  const hours = now.getHours()
  const mins = String(now.getMinutes()).padStart(2, '0')
  const period = hours < 12 ? '上午' : '下午'
  const displayHour = hours % 12 || 12
  return `${period} ${displayHour}:${mins}`
}

const scrollToBottom = async () => {
  await nextTick()
  if (chatViewportRef.value) {
    chatViewportRef.value.scrollTo({
      top: chatViewportRef.value.scrollHeight,
      behavior: 'smooth'
    })
  }
}

const handleScroll = () => {
  if (!chatViewportRef.value) return
  const { scrollTop, scrollHeight, clientHeight } = chatViewportRef.value
  showScrollBottomBtn.value = (scrollHeight - scrollTop - clientHeight) > 120
}

const appendAiMessage = ({ html, isHeroGreeting = false, quickButtons = [], topicCards = [], chapterTitle = null, tokenCost = null }) => {
  messages.value.push({
    id: msgIdCounter++,
    sender: 'ai',
    html,
    isHeroGreeting,
    quickButtons,
    topicCards,
    chapterTitle,
    tokenCost,
    time: getCurrentTimeStr()
  })
  scrollToBottom()
}

const appendUserMessage = (text) => {
  messages.value.push({
    id: msgIdCounter++,
    sender: 'user',
    text,
    time: getCurrentTimeStr()
  })
  scrollToBottom()
}

// =====================================================================
// 階段一：進入頁面時，Dr. Manhattan 主動問候並詢問角色
// =====================================================================
const restartConversation = () => {
  currentRole.value = null
  currentChemical.value = null
  messages.value = []

  appendAiMessage({
    isHeroGreeting: true,
    html: `
      <p class="report-para">※ 歡迎使用 <strong>KCC ToxProfiler 毒理學危害辨識平台</strong>！我是您的專屬評估智能助理 <strong>Dr. Manhattan</strong>。</p>
      <p class="report-para">※ 我將根據「歷史紀錄」中勾選的化學物質評估檔案，為您提供精準的致癌關鍵特徵（10 KCCs）解析與風險問答。</p>
      <p class="report-para" style="margin-bottom:0;"><strong>您好，請問您想以哪種視角查閱報告？</strong></p>
    `,
    quickButtons: [
      { type: 'role', value: '一般民眾', label: '一般民眾' },
      { type: 'role', value: '專家', label: '專家' }
    ]
  })
}

const handleQuickButtonClick = async (btn) => {
  if (btn.type === 'role') {
    await handleSelectRole(btn.value)
  } else if (btn.type === 'chemical') {
    await handleSelectChemical(btn.chemObj)
  } else if (btn.type === 'go-history') {
    handleHistoryCardClick()
  }
}

// =====================================================================
// 階段二：點選『一般民眾』或『專家』-> 撈出 is_selected=True 的化學物質
// =====================================================================
const handleSelectRole = async (roleName) => {
  currentRole.value = roleName
  appendUserMessage(roleName === '一般民眾' ? '我是一般民眾' : '我是專家')

  isThinking.value = true
  try {
    const res = await fetch(`${API_BASE_URL}/chat/chemicals`, {
      credentials: 'include'
    })
    if (!res.ok) throw new Error('無法取得已勾選之化學物質清單')
    const data = await res.json()
    selectedChemicalsList.value = data.chemicals || []

    if (selectedChemicalsList.value.length === 0) {
      appendAiMessage({
        html: `
          <p class="report-para">目前在「歷史紀錄管理」頁面中，尚未勾選任何化學物質（<code>is_selected = True</code>）。</p>
          <p class="report-para" style="margin-bottom:0;">請先由專家或系統管理者於歷史紀錄頁面勾選代表性化學物質評估結果！</p>
        `,
        quickButtons: canGoHistory.value
          ? [{ type: 'go-history', label: '👉 前往歷史紀錄頁面勾選' }]
          : []
      })
      return
    }

    const chemButtons = selectedChemicalsList.value.map(c => ({
      type: 'chemical',
      label: c.chemical_name_zh,
      chemObj: c
    }))

    appendAiMessage({
      html: `<p class="report-para" style="margin-bottom:0;">收到，已切換為<strong>「${roleName}」</strong>視角！<strong>請選擇關注化學物質？</strong></p>`,
      quickButtons: chemButtons
    })
  } catch (err) {
    console.error(err)
    appendAiMessage({
      html: `<p class="report-para">讀取已勾選化學物質失敗，請確認後端服務是否正常運作。</p>`
    })
  } finally {
    isThinking.value = false
  }
}

const promptSwitchChemical = async () => {
  if (!currentRole.value) return
  await handleSelectRole(currentRole.value)
}

// =====================================================================
// 階段三：點選化學物質 -> 列出主題卡片
// =====================================================================
const handleSelectChemical = async (chemObj) => {
  currentChemical.value = chemObj
  appendUserMessage(`我想要了解「${chemObj.chemical_name_zh}」相關的危害辨識評估結果。`)

  isThinking.value = true
  try {
    const res = await fetch(`${API_BASE_URL}/chat/select-chemical`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        chemical_query: chemObj.cas_number,
        role: currentRole.value
      })
    })
    if (!res.ok) throw new Error('載入化學物質評估檔案失敗')
    const data = await res.json()

    appendAiMessage({
      html: `
        <p class="report-para">
          已為您載入<strong>「${data.chemical_name_zh} (${data.chemical_name_en})」</strong>之評估報告（總體危害評級：<strong>${data.hazard_score} / 100｜${data.risk_level}</strong>）。
        </p>
        <p class="report-para" style="margin-bottom:0;">
          <strong>請選擇您想要了解的主題？</strong>（點擊主題按鈕享 0 Token 極速查閱；會員與專家亦可於下方輸入框自由提問）
        </p>
      `,
      topicCards: data.available_topics || []
    })
  } catch (err) {
    console.error(err)
    appendAiMessage({
      html: `<p class="report-para">載入「${chemObj.chemical_name_zh}」評估報告失敗，請確認該筆評估是否已完成報告生成。</p>`
    })
  } finally {
    isThinking.value = false
  }
}

// =====================================================================
// 階段四 A：點擊預設主題按鈕 (0 Token 消耗)
// =====================================================================
const handleSelectTopic = async (topicName, topicIndex) => {
  if (!currentChemical.value) return
  appendUserMessage(`我想了解「${currentChemical.value.chemical_name_zh}」的：${topicName}`)

  isThinking.value = true
  try {
    const res = await fetch(`${API_BASE_URL}/chat/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        chemical_query: currentChemical.value.cas_number,
        role: currentRole.value,
        question: topicName,
        is_topic_click: true,
        topic_index: topicIndex
      })
    })
    if (!res.ok) throw new Error('取得主題內容失敗')
    const data = await res.json()

    if (data.quota) {
      Object.assign(quotaInfo, data.quota)
    }

    appendAiMessage({
      chapterTitle: data.chapter_title || topicName,
      html: data.reply_html,
      topicCards: data.available_topics || []
    })
  } catch (err) {
    console.error(err)
    appendAiMessage({
      html: `<p class="report-para">抱歉，讀取章節內容時發生錯誤，請稍後再試。</p>`
    })
  } finally {
    isThinking.value = false
  }
}

// =====================================================================
// 階段四 B：使用者於下方輸入框「自由輸入問題」(含額度扣抵與即時警示)
// =====================================================================
const handleSendFreeText = async () => {
  const questionText = userInput.value.trim()
  if (!questionText || isInputDisabled.value) return

  userInput.value = ''
  isQuotaPopoverOpen.value = false
  appendUserMessage(questionText)

  isThinking.value = true
  try {
    const res = await fetch(`${API_BASE_URL}/chat/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        chemical_query: currentChemical.value.cas_number,
        role: currentRole.value,
        question: questionText,
        is_topic_click: false
      })
    })

    const data = await res.json()

    if (!res.ok) {
      // 若觸發 429 (冷卻中 / 會員每日額度已滿) 或 403，直接將後端保護訊息顯示於對話框並刷新額度
      await fetchQuotaStatus()
      appendAiMessage({
        html: `<p class="report-para"><strong>${data.detail || '無法處理您的提問，請稍後再試。'}</strong></p>`
      })
      return
    }

    // 即時更新左下角額度與高水位警示狀態
    if (data.quota) {
      Object.assign(quotaInfo, data.quota)
    }

    appendAiMessage({
      html: data.reply_html,
      topicCards: data.available_topics || [],
      tokenCost: data.token_cost || null
    })
  } catch (err) {
    console.error(err)
    appendAiMessage({
      html: `<p class="report-para">抱歉，Dr. Manhattan 暫時無法連線至模型伺服器，請稍後再試。</p>`
    })
  } finally {
    isThinking.value = false
  }
}

onMounted(() => {
  restartConversation()
  fetchQuotaStatus()
})
</script>

<style scoped>
.chat-page {
  max-width: 1060px;
  margin: 16px auto 28px auto;
  padding: 0 20px;
}

.chat-window {
  position: relative;
  background-color: #f4f7f8;
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  border: 1.5px solid #ffffff;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 125px);
  min-height: 620px;
  overflow: hidden;
}

/* 1. 頂部標題列 */
.chat-topbar {
  background-color: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  padding: 14px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background-color: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
}

.assistant-badge {
  font-size: 11.5px;
  font-weight: 900;
  letter-spacing: 1px;
  color: var(--dark-color);
  background-color: var(--light-color);
  padding: 3px 10px;
  border-radius: 12px;
}

.topbar-title {
  margin: 0;
  font-size: 24px;
  font-weight: 900;
  color: white;
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

.reset-top-btn {
  background-color: #f8fafc;
  color: var(--dark-color);
  border: 1.5px solid var(--dark-color);
  padding: 5px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s;
}

.reset-top-btn:hover {
  background-color: var(--dark-color);
  color: #ffffff;
}

/* 2. 訊息滾動視窗 */
.chat-Viewport {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.message-row {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  width: 100%;
}

.row-ai { justify-content: flex-start; }
.row-user { justify-content: flex-end; }

.ai-avatar-circle {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0284c7 0%, #1e3a8a 100%);
  border: 2px solid #38bdf8;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
  box-shadow: 0 3px 10px rgba(2, 132, 199, 0.25);
}

.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.avatar-fallback { font-size: 22px; }

.ai-content-col {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  max-width: 82%;
}

.hero-mascot-box {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 2px;
}

.hero-avatar-frame {
  position: relative;
  width: 86px;
  height: 86px;
  border-radius: 20px;
  background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
  border: 2px solid #0284c7;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 16px rgba(2, 132, 199, 0.15);
}

.hello-tag {
  position: absolute;
  top: -10px;
  left: -8px;
  background-color: #f6d32d;
  color: #1b1e29;
  font-size: 11px;
  font-weight: 900;
  padding: 2px 8px;
  border-radius: 10px;
  transform: rotate(-8deg);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  z-index: 2;
}

.hero-img { width: 100%; height: 100%; object-fit: cover; border-radius: 18px; }
.hero-placeholder { display: flex; flex-direction: column; align-items: center; color: #0369a1; }
.atom-symbol { font-size: 34px; line-height: 1; }
.placeholder-hint { font-size: 9.5px; font-weight: 900; margin-top: 4px; }
.hero-intro-tag { display: flex; flex-direction: column; gap: 4px; }
.hero-intro-tag strong { font-size: 16px; color: #1b1e29; font-weight: 900; }
.hero-intro-tag span { font-size: 12.5px; color: var(--dark-color); font-weight: 700; }

.ai-bubble {
  background-color: #ffffff;
  color: #2d3748;
  padding: 16px 22px;
  border-radius: 4px 16px 16px 16px;
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.04);
  border: 1px solid #edf2f7;
  line-height: 1.75;
  font-size: 15px;
}

.bubble-chapter-title {
  font-size: 16.5px;
  font-weight: 900;
  color: var(--dark-color);
  border-bottom: 2px solid var(--light-color);
  padding-bottom: 8px;
  margin-bottom: 12px;
}

.quick-btn-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 2px;
}

.choice-chip-btn {
  background-color: #ffffff;
  color: var(--dark-color);
  border: 1.5px solid var(--dark-color);
  padding: 9px 22px;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
}

.choice-chip-btn:hover:not(:disabled) {
  background-color: var(--dark-color);
  color: #ffffff;
  transform: translateY(-2px);
}

.alpha-card-deck {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  width: 100%;
  margin-top: 4px;
}

.alpha-card {
  background-color: #ffffff;
  border-radius: 14px;
  width: 280px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.alpha-card-illust {
  padding: 18px 16px 14px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
  border-bottom: 1px solid #edf2f7;
}

.illust-circle {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background-color: var(--light-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin-bottom: 10px;
}

.illust-circle.alt { background-color: #e0f2fe; }
.alpha-card-title { margin: 0 0 4px 0; font-size: 15px; font-weight: 900; color: #1b1e29; }
.alpha-card-sub { font-size: 12px; color: #64748b; font-weight: 700; }
.alpha-card-actions { display: flex; flex-direction: column; }

.alpha-topic-btn {
  background-color: #ffffff;
  color: var(--dark-color);
  border: none;
  border-bottom: 1px solid #f1f5f9;
  padding: 12px 14px;
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.18s ease;
  text-align: center;
}

.alpha-topic-btn:last-child { border-bottom: none; }
.alpha-topic-btn:hover:not(:disabled) { background-color: var(--light-color); color: #1b1e29; }

.user-content-col {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  max-width: 75%;
}

.user-bubble {
  background-color: var(--dark-color);
  color: #ffffff;
  padding: 12px 20px;
  border-radius: 16px 4px 16px 16px;
  font-size: 15px;
  font-weight: 700;
  line-height: 1.6;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08);
}

.msg-meta-foot {
  display: flex;
  align-items: center;
  gap: 10px;
}

.msg-time {
  font-size: 11.5px;
  color: #94a3b8;
  font-weight: 600;
}

.token-cost-pill {
  font-size: 11px;
  font-weight: 800;
  color: #0369a1;
  background-color: #e0f2fe;
  padding: 1px 8px;
  border-radius: 10px;
}

.thinking-bubble { display: inline-flex; align-items: center; gap: 6px; padding: 12px 18px; }
.thinking-bubble .dot {
  width: 7px; height: 7px; background-color: var(--dark-color);
  border-radius: 50%; animation: bounceDot 1.2s infinite ease-in-out;
}
.thinking-bubble .dot:nth-child(2) { animation-delay: 0.2s; }
.thinking-bubble .dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounceDot {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1.1); opacity: 1; }
}
.thinking-text { font-size: 13.5px; font-weight: 700; color: #64748b; margin-left: 6px; }

.scroll-bottom-fab {
  position: absolute;
  right: 24px;
  bottom: 90px;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background-color: rgba(100, 116, 139, 0.85);
  color: #ffffff;
  border: none;
  font-size: 20px;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
}

/* ================= 會員高額度預警 / 用盡警示橫幅 ================= */
.quota-alert-banner {
  padding: 9px 20px;
  font-size: 13.5px;
  font-weight: 800;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.quota-alert-banner.alert-warning {
  background-color: #fef3c7;
  color: #92400e;
  border-top: 1.5px solid #f59e0b;
}

.quota-alert-banner.alert-danger {
  background-color: #fee2e2;
  color: #991b1b;
  border-top: 1.5px solid #ef4444;
}

.alert-detail-btn {
  background-color: rgba(255, 255, 255, 0.8);
  border: 1px solid currentColor;
  color: inherit;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
  white-space: nowrap;
}

/* ================= 左下角彈出「今日剩餘次數 / Token」小視窗 ================= */
.quota-popover-card {
  position: absolute;
  left: 18px;
  bottom: 76px;
  width: 370px;
  background-color: #ffffff;
  border-radius: 16px;
  box-shadow: 0 12px 32px rgba(27, 30, 41, 0.22);
  border: 1.5px solid #cbd5e1;
  z-index: 2500;
  overflow: hidden;
}

.qp-header {
  background-color: #1b1e29;
  color: #ffffff;
  padding: 13px 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 3px solid var(--primary-color);
}

.qp-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.qp-icon {
  font-size: 20px;
}

.qp-title-row h4 {
  margin: 0;
  font-size: 14.5px;
  font-weight: 800;
  color: #ffffff;
}

.qp-sub {
  font-size: 11.5px;
  color: #94a3b8;
  font-weight: 600;
}

.qp-close {
  background: rgba(255, 255, 255, 0.12);
  border: none;
  color: #cbd5e1;
  width: 26px;
  height: 26px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.qp-close:hover {
  background-color: #ef4444;
  color: #ffffff;
}

.qp-body {
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  font-size: 13.5px;
  color: #334155;
}

.qp-role-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 10px;
  border-bottom: 1px dashed #e2e8f0;
  font-weight: 700;
}

.qp-role-badge {
  padding: 3px 10px;
  border-radius: 10px;
  font-size: 12.5px;
  font-weight: 800;
}

.q-role-admin { background-color: #fef3c7; color: #92400e; }
.q-role-expert { background-color: #e0f2fe; color: #075985; }
.q-role-member { background-color: #dcfce7; color: #166534; }
.q-role-guest { background-color: #f1f5f9; color: #475569; }

.qp-unlimited-box {
  background-color: #f0fdf4;
  border: 1px solid #86efac;
  border-radius: 10px;
  padding: 12px 14px;
}

.unlim-title {
  font-weight: 900;
  color: #166534;
  margin-bottom: 4px;
}

.qp-unlimited-box p {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: #15803d;
}

.unlim-stats {
  font-size: 12.5px;
  color: #1e293b;
  background-color: #ffffff;
  padding: 6px 10px;
  border-radius: 6px;
  display: flex;
  justify-content: space-around;
}

.qp-meters-box {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.meter-group {
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.meter-label-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 700;
  color: #1e293b;
}

.rem-highlight {
  color: var(--dark-color);
  font-size: 15px;
  font-weight: 900;
}

.progress-track {
  width: 100%;
  height: 8px;
  background-color: #e2e8f0;
  border-radius: 6px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 6px;
  transition: width 0.35s ease;
}

.fill-normal { background-color: var(--dark-color); }
.fill-warning { background-color: #f59e0b; }
.fill-danger { background-color: #ef4444; }

.meter-foot {
  font-size: 11.5px;
  color: #64748b;
  font-weight: 600;
}

.qp-guest-box {
  background-color: #fffaf0;
  border: 1px solid #fbd38d;
  border-radius: 10px;
  padding: 12px;
  font-size: 13px;
  line-height: 1.55;
}

.qp-guest-box p { margin: 0 0 8px 0; }

.qp-login-btn {
  width: 100%;
  background-color: #1b1e29;
  color: #ffffff;
  border: none;
  padding: 8px;
  border-radius: 8px;
  font-weight: 800;
  cursor: pointer;
}

.qp-rules-list {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
  color: #64748b;
  line-height: 1.55;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* ================= 3. 底部固定輸入列與左下角改造按鈕 ================= */
.chat-input-bar {
  background-color: #ffffff;
  border-top: 1px solid #e2e8f0;
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

/* 改造後的左下角額度按鈕 */
.quota-trigger-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 14px;
  border-radius: 20px;
  font-size: 13.5px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
  border: 1.5px solid #cbd5e1;
  background-color: #f8fafc;
  color: #1e293b;
}

.quota-trigger-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08);
}

.q-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #10b981;
}

.quota-trigger-btn.q-btn-unlimited {
  background-color: #f0fdf4;
  border-color: #86efac;
  color: #166534;
}

.quota-trigger-btn.q-btn-warning {
  background-color: #fef3c7;
  border-color: #f59e0b;
  color: #92400e;
}
.quota-trigger-btn.q-btn-warning .q-dot { background-color: #f59e0b; }

.quota-trigger-btn.q-btn-danger {
  background-color: #fee2e2;
  border-color: #ef4444;
  color: #991b1b;
}
.quota-trigger-btn.q-btn-danger .q-dot { background-color: #ef4444; }

.chat-text-input {
  flex: 1;
  background-color: #f8fafc;
  border: 1.5px solid #cbd5e1;
  border-radius: 24px;
  padding: 11px 20px;
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  outline: none;
  transition: all 0.2s;
}

.chat-text-input:focus {
  background-color: #ffffff;
  border-color: var(--dark-color);
}

.chat-text-input:disabled {
  background-color: #f1f5f9;
  color: #94a3b8;
  cursor: not-allowed;
}

.send-circle-btn {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background-color: var(--dark-color);
  color: #ffffff;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.send-circle-btn:hover:not(:disabled) {
  background-color: #1b1e29;
  transform: scale(1.05);
}

.send-circle-btn:disabled {
  background-color: #cbd5e1;
  cursor: not-allowed;
}

.popover-fade-enter-active,
.popover-fade-leave-active {
  transition: all 0.2s ease;
}
.popover-fade-enter-from,
.popover-fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

:deep(.report-para) { margin: 0 0 10px 0; line-height: 1.75; }
:deep(.sub-sec-title) { margin: 14px 0 8px 0; font-size: 15.5px; color: var(--dark-color); font-weight: 800; }
:deep(.bullet-item), :deep(.num-item) { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 8px; }
:deep(.bullet-dot), :deep(.num-idx) { color: var(--dark-color); font-weight: 900; }

:deep(.apa-citation) {
  position: relative;
  display: inline-block;
  background-color: #e3f2fd;
  color: #0d47a1;
  padding: 0px 6px;
  border-radius: 4px;
  cursor: pointer;
  border-bottom: 1px dashed #1976d2;
  font-weight: 700;
}

:deep(.apa-citation::after) {
  content: "📄 " attr(data-pmid);
  visibility: hidden;
  opacity: 0;
  position: absolute;
  bottom: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%);
  background-color: #1a1e29;
  color: #63e6be;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 6px;
  white-space: nowrap;
  z-index: 3000;
  transition: all 0.2s ease;
}

:deep(.apa-citation:hover::after) {
  visibility: visible;
  opacity: 1;
}
</style>