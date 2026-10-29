import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import SystematicReview from '../views/SystematicReview.vue'
import MetaAnalysis from '../views/MetaAnalysis.vue'
import HistoryView from '../views/HistoryView.vue'
import ChatAdvisorView from '../views/ChatAdvisorView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/review', name: 'review', component: SystematicReview },
    { path: '/meta', name: 'meta', component: MetaAnalysis },
    { path: '/history', name: 'history', component: HistoryView },
    { path: '/chat', name: 'chat', component: ChatAdvisorView }
  ]
})

export default router