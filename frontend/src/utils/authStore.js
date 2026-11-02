// frontend/src/utils/authStore.js
import { reactive } from 'vue'

const API_BASE_URL = window.location.port === '5173'
  ? `http://${window.location.hostname}:8000/api`
  : '/api'

export const authState = reactive({
  initialized: false,
  isAuthenticated: false,
  isGuest: false,
  user: null, // { id, email, name, role: '系統管理者' | '專家' | '會員' | '訪客', organization }
  isAuthModalOpen: false,
  authModalMode: 'login', // 'login' | 'register'
  authModalMessage: ''
})

// 向後端同步當前 Session 狀態
export const fetchCurrentUser = async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/me`, {
      credentials: 'include'
    })
    if (res.ok) {
      const data = await res.json()
      authState.isAuthenticated = data.is_authenticated
      authState.isGuest = data.is_guest
      authState.user = data.user
    }
  } catch (err) {
    console.error('檢查登入狀態失敗:', err)
  } finally {
    authState.initialized = true
  }
}

export const openAuthModal = (mode = 'login', msg = '') => {
  authState.authModalMode = mode
  authState.authModalMessage = msg
  authState.isAuthModalOpen = true
}

export const closeAuthModal = () => {
  authState.isAuthModalOpen = false
  authState.authModalMessage = ''
}

// 取得當前生效角色 (若完全未點擊登入或訪客，預設視同 '訪客')
export const getCurrentRole = () => {
  return authState.user?.role || '訪客'
}