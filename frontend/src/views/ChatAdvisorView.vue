<template>
  <main class="chat-page">
    <!-- 聊天室主容器 (仿照智能助理阿發的置中視窗卡片結構) -->
    <div class="chat-window">
      <!-- 1. 頂部標題列 (對應阿發頂部標題與右側重設選單) -->
      <header class="chat-topbar">
        <div class="topbar-left">
          <span class="status-dot"></span>
          <span class="assistant-badge">AI ADVISOR</span>
        </div>
        <h2 class="topbar-title">智能助理 Dr. Manhattan</h2>
        <button class="reset-top-btn" @click="restartConversation" title="重新開始對話導覽">
          ↻ 重新導覽
        </button>
      </header>

      <!-- 2. 訊息滾動區 -->
      <div class="chat-Viewport" ref="chatViewportRef" @scroll="handleScroll">
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
              <img v-if="DR_MANHATTAN_AVATAR" :src="DR_MANHATTAN_AVATAR" alt="Dr. Manhattan" class="avatar-img" />
              <span v-else class="avatar-fallback">⚛️</span>
            </div>

            <div class="ai-content-col">
              <!-- 首則歡迎訊息專屬：仿照阿發左上角的 Hello 大頭貼立繪預留區 (預留空間 2) -->
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
                  <strong>Dr. Manhattan 危害辨識導覽員</strong>
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

              <!-- 情境 B：仿照智能阿發的「多欄式主題卡片選單」 (Step 3 主題選擇) -->
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

                <!-- 第二張輔助操作卡 (仿照阿發並排卡片設計，提供切換物質或角色) -->
                <div class="alpha-card secondary-card">
                  <div class="alpha-card-illust">
                    <div class="illust-circle alt">🧭</div>
                    <h4 class="alpha-card-title">進階探索與切換</h4>
                    <span class="alpha-card-sub">當前身分：{{ currentRole }}</span>
                  </div>
                  <div class="alpha-card-actions">
                    <button class="alpha-topic-btn" :disabled="isThinking" @click="promptSwitchChemical">
                      切換關注化學物質
                    </button>
                    <button class="alpha-topic-btn" :disabled="isThinking" @click="restartConversation">
                      重新選擇角色身分 ({{ currentRole === '專家' ? '改為一般民眾' : '改為專家' }})
                    </button>
                    <button class="alpha-topic-btn" @click="router.push('/history')">
                      前往歷史紀錄勾選管理
                    </button>
                  </div>
                </div>
              </div>

              <!-- 送出時間戳記 -->
              <span class="msg-time">{{ msg.time }} 送出</span>
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
            <img v-if="DR_MANHATTAN_AVATAR" :src="DR_MANHATTAN_AVATAR" alt="Dr. Manhattan" class="avatar-img" />
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

      <!-- 右下角懸浮「滑至最底」按鈕 (仿照阿發右下角灰色圓形箭頭) -->
      <button 
        v-show="showScrollBottomBtn" 
        class="scroll-bottom-fab" 
        @click="scrollToBottom"
        title="滑動至最新訊息"
      >
        ⌄
      </button>

      <!-- 3. 底部固定輸入列 (仿照智能阿發：左側選單鈕 + 圓角輸入框 + 右側圓形發送鈕) -->
      <footer class="chat-input-bar">
        <button 
          class="left-menu-btn" 
          @click="restartConversation" 
          title="重新開始角色與物質選擇"
        >
          ☰
        </button>

        <input
          type="text"
          v-model="userInput"
          class="chat-text-input"
          :placeholder="currentChemical ? `針對「${currentChemical.chemical_name_zh}」評估報告內容向 Dr. Manhattan 提問...` : '請先點擊上方按鈕選擇您的角色與關注化學物質...'"
          :disabled="!currentChemical || isThinking"
          @keyup.enter="handleSendFreeText"
        />

        <button 
          class="send-circle-btn" 
          :disabled="!currentChemical || !userInput.trim() || isThinking"
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
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'

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

const chatViewportRef = ref(null)
const messages = ref([])
const userInput = ref('')
const isThinking = ref(false)
const showScrollBottomBtn = ref(false)

// 當前對話狀態記憶
const currentRole = ref(null)       // '一般民眾' | '專家'
const currentChemical = ref(null)   // 選中的化學物質物件
const selectedChemicalsList = ref([])

let msgIdCounter = 1

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

// 新增一則 AI 訊息
const appendAiMessage = ({ html, isHeroGreeting = false, quickButtons = [], topicCards = [], chapterTitle = null }) => {
  messages.value.push({
    id: msgIdCounter++,
    sender: 'ai',
    html,
    isHeroGreeting,
    quickButtons,
    topicCards,
    chapterTitle,
    time: getCurrentTimeStr()
  })
  scrollToBottom()
}

// 新增一則使用者右側訊息氣泡
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
      <p class="report-para">※ 我將根據您在「歷史紀錄」中勾選的化學物質評估檔案，為您提供精準的致癌關鍵特徵（10 KCCs）解析與風險問答。</p>
      <p class="report-para" style="margin-bottom:0;"><strong>您好，請問您的角色是？</strong></p>
    `,
    quickButtons: [
      { type: 'role', value: '一般民眾', label: '一般民眾' },
      { type: 'role', value: '專家', label: '專家' }
    ]
  })
}

// 處理快速按鈕點擊 (Step 1 選角色 / Step 2 選化學物質)
const handleQuickButtonClick = async (btn) => {
  if (btn.type === 'role') {
    await handleSelectRole(btn.value)
  } else if (btn.type === 'chemical') {
    await handleSelectChemical(btn.chemObj)
  } else if (btn.type === 'go-history') {
    router.push('/history')
  }
}

// =====================================================================
// 階段二：使用者點選『一般民眾』或『專家』-> 顯示使用者氣泡 -> 撈出 is_selected=True 的化學物質
// =====================================================================
const handleSelectRole = async (roleName) => {
  currentRole.value = roleName
  appendUserMessage(`我是一般民眾` && roleName === '一般民眾' ? '我是一般民眾' : '我是專家')

  isThinking.value = true
  try {
    const res = await fetch(`${API_BASE_URL}/chat/chemicals`)
    if (!res.ok) throw new Error('無法取得已勾選之化學物質清單')
    const data = await res.json()
    selectedChemicalsList.value = data.chemicals || []

    if (selectedChemicalsList.value.length === 0) {
      appendAiMessage({
        html: `
          <p class="report-para">目前在「歷史紀錄管理」頁面中，尚未勾選任何化學物質（<code>is_selected = True</code>）。</p>
          <p class="report-para" style="margin-bottom:0;">請先前往歷史紀錄頁面勾選您想關注的化學物質評估結果！</p>
        `,
        quickButtons: [
          { type: 'go-history', label: '👉 前往歷史紀錄頁面勾選' }
        ]
      })
      return
    }

    // 將有勾選 (is_selected = true) 的化學物質轉為按鈕選項
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

// 隨時重新列出已勾選的化學物質供切換
const promptSwitchChemical = async () => {
  if (!currentRole.value) return
  await handleSelectRole(currentRole.value)
}

// =====================================================================
// 階段三：使用者點選化學物質 -> 顯示「我想要了解『XXX』相關的危害辨識評估結果。」 -> 列出主題卡片
// =====================================================================
const handleSelectChemical = async (chemObj) => {
  currentChemical.value = chemObj
  appendUserMessage(`我想要了解「${chemObj.chemical_name_zh}」相關的危害辨識評估結果。`)

  isThinking.value = true
  try {
    const res = await fetch(`${API_BASE_URL}/chat/select-chemical`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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
          <strong>請選擇您想要了解的主題？</strong>（您也可以直接在下方輸入框輸入問題向我提問）
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
// 階段四 A：點擊阿發風格卡片上的「主題按鈕」
// =====================================================================
const handleSelectTopic = async (topicName, topicIndex) => {
  if (!currentChemical.value) return
  appendUserMessage(`我想了解「${ currentChemical.value.chemical_name_zh }」的：${topicName}`)

  isThinking.value = true
  try {
    const res = await fetch(`${API_BASE_URL}/chat/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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
// 階段四 B：使用者於下方輸入框「自由輸入問題」(支援報告內回答與超綱攔截)
// =====================================================================
const handleSendFreeText = async () => {
  const questionText = userInput.value.trim()
  if (!questionText || !currentChemical.value || isThinking.value) return

  userInput.value = ''
  appendUserMessage(questionText)

  isThinking.value = true
  try {
    const res = await fetch(`${API_BASE_URL}/chat/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chemical_query: currentChemical.value.cas_number,
        role: currentRole.value,
        question: questionText,
        is_topic_click: false
      })
    })
    if (!res.ok) throw new Error('AI 回覆失敗')
    const data = await res.json()

    appendAiMessage({
      html: data.reply_html,
      topicCards: data.available_topics || []
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
})
</script>

<style scoped>
.chat-page {
  max-width: 1060px;
  margin: 16px auto 28px auto;
  padding: 0 20px;
}

/* 仿照智能助理阿發的對話主視窗 */
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
  color: #1b1e29;
  letter-spacing: 1.5px;
  text-shadow: 
    1px 1px 0px #f6d32d,
    2px 2px 0px #f6d32d,
    3px 3px 0px #e25740,
    4px 4px 0px #f6d32d;
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

.row-ai {
  justify-content: flex-start;
}

.row-user {
  justify-content: flex-end;
}

/* Dr. Manhattan 左側圓形頭像 (預留空間 1) */
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

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-fallback {
  font-size: 22px;
}

.ai-content-col {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  max-width: 82%;
}

/* 首則訊息上方：仿照阿發 Hello 大頭貼立繪預留區 (預留空間 2) */
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
  overflow: visible;
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

.hero-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 18px;
}

.hero-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #0369a1;
}

.atom-symbol {
  font-size: 34px;
  line-height: 1;
}

.placeholder-hint {
  font-size: 9.5px;
  font-weight: 900;
  margin-top: 4px;
}

.hero-intro-tag {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hero-intro-tag strong {
  font-size: 16px;
  color: #1b1e29;
  font-weight: 900;
}

.hero-intro-tag span {
  font-size: 12.5px;
  color: var(--dark-color);
  font-weight: 700;
}

/* AI 白色對話氣泡 */
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

/* 快速選項按鈕群 (『一般民眾』『專家』 / 『苯駢芘』『塑化劑』) */
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
  box-shadow: 0 5px 12px rgba(0, 0, 0, 0.12);
}

/* 仿照智能阿發的「並排主題卡片」設計 */
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

.illust-circle.alt {
  background-color: #e0f2fe;
}

.alpha-card-title {
  margin: 0 0 4px 0;
  font-size: 15px;
  font-weight: 900;
  color: #1b1e29;
}

.alpha-card-sub {
  font-size: 12px;
  color: #64748b;
  font-weight: 700;
}

.alpha-card-actions {
  display: flex;
  flex-direction: column;
}

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

.alpha-topic-btn:last-child {
  border-bottom: none;
}

.alpha-topic-btn:hover:not(:disabled) {
  background-color: var(--light-color);
  color: #1b1e29;
}

/* 右側使用者氣泡 (對應阿發右側綠底氣泡，融入本系統深青色系) */
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

.msg-time {
  font-size: 11.5px;
  color: #94a3b8;
  font-weight: 600;
}

/* 思考中動畫 */
.thinking-bubble {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 12px 18px;
}

.thinking-bubble .dot {
  width: 7px;
  height: 7px;
  background-color: var(--dark-color);
  border-radius: 50%;
  animation: bounceDot 1.2s infinite ease-in-out;
}

.thinking-bubble .dot:nth-child(2) { animation-delay: 0.2s; }
.thinking-bubble .dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounceDot {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1.1); opacity: 1; }
}

.thinking-text {
  font-size: 13.5px;
  font-weight: 700;
  color: #64748b;
  margin-left: 6px;
}

/* 右下角滑至最底圓鈕 */
.scroll-bottom-fab {
  position: absolute;
  right: 24px;
  bottom: 84px;
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

/* 3. 底部固定輸入列 */
.chat-input-bar {
  background-color: #ffffff;
  border-top: 1px solid #e2e8f0;
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.left-menu-btn {
  background: transparent;
  border: none;
  color: #64748b;
  font-size: 20px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
}

.left-menu-btn:hover {
  background-color: #f1f5f9;
  color: #1b1e29;
}

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

/* 支援報告段落與專家版 APA 7th PMID 懸浮窗樣式 */
:deep(.report-para) {
  margin: 0 0 10px 0;
  line-height: 1.75;
}

:deep(.sub-sec-title) {
  margin: 14px 0 8px 0;
  font-size: 15.5px;
  color: var(--dark-color);
  font-weight: 800;
}

:deep(.bullet-item),
:deep(.num-item) {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}

:deep(.bullet-dot),
:deep(.num-idx) {
  color: var(--dark-color);
  font-weight: 900;
}

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