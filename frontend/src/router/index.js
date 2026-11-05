import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import SystematicReview from '../views/SystematicReview.vue'
import MetaAnalysis from '../views/MetaAnalysis.vue'
import HistoryView from '../views/HistoryView.vue'
import ChatAdvisorView from '../views/ChatAdvisorView.vue'
import AccountManageView from '../views/AccountManageView.vue'
// 在 frontend/src/router/index.js 中加入路由守衛：
import { authState, fetchCurrentUser, openAuthModal } from '../utils/authStore'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/review', name: 'review', component: SystematicReview },
    { path: '/meta', name: 'meta', component: MetaAnalysis },
    { path: '/history', name: 'history', component: HistoryView },
    { path: '/chat', name: 'chat', component: ChatAdvisorView },
    { path: '/account', name: 'account', component: AccountManageView }
  ]
})

router.beforeEach(async (to, from, next) => {
  if (!authState.initialized) {
    await fetchCurrentUser()
  }

  const role = authState.user?.role || '訪客'

  // 1. 帳號管理頁面 (/account) 僅限『系統管理者』進入
  if (to.path.startsWith('/account') && role !== '系統管理者') {
    openAuthModal('login', '請先登入「系統管理者」帳號以存取帳號管理頁面。')
    return next('/chat')
  }

  // 2. 危害辨識 (/, /review, /meta) 與 歷史紀錄 (/history) 僅限『系統管理者』與『專家』進入
  const restrictedToExpert = ['/', '/review', '/meta', '/history']
  if (restrictedToExpert.includes(to.path) && role !== '系統管理者' && role !== '專家') {
    if (!authState.isAuthenticated && !authState.isGuest) {
      openAuthModal('login', '請先登入系統，或點擊下方以『訪客』身份進入智能助理。')
    }
    return next('/chat')
  }

  next()
})

export default router