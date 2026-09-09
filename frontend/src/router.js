import { createRouter, createWebHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import NewsDetailView from './views/NewsDetailView.vue'
import AuthView from './views/AuthView.vue'
import CollectionView from './views/CollectionView.vue'
import AdminView from './views/AdminView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/news/:id', name: 'news-detail', component: NewsDetailView },
    { path: '/login', name: 'login', component: AuthView },
    { path: '/register', name: 'register', component: AuthView },
    { path: '/favorites', name: 'favorites', component: CollectionView, meta: { auth: true, mode: 'favorites' } },
    { path: '/history', name: 'history', component: CollectionView, meta: { auth: true, mode: 'history' } },
    { path: '/admin', name: 'admin', component: AdminView, meta: { auth: true, admin: true } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach((to) => {
  const token = localStorage.getItem('ai-news-token')
  let user = null
  try {
    user = JSON.parse(localStorage.getItem('ai-news-user') || 'null')
  } catch {
    user = null
  }
  if (to.meta.auth && !token) return { name: 'login', query: { redirect: to.fullPath } }
  if (to.meta.admin && !user?.is_admin) return { name: 'home' }
  if ((to.name === 'login' || to.name === 'register') && token) return { name: 'home' }
})

export default router

