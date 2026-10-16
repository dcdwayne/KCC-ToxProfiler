import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import SystematicReview from '../views/SystematicReview.vue'
import MetaAnalysis from '../views/MetaAnalysis.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/review', name: 'review', component: SystematicReview },
    { path: '/meta', name: 'meta', component: MetaAnalysis }
  ]
})

export default router