import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/podcast/:id',
      name: 'podcast-detail',
      component: () => import('../views/PodcastDetailView.vue'),
    },
    {
      path: '/add-podcast',
      name: 'add-podcast',
      component: () => import('../views/AddPodcastView.vue'),
    },
    {
      path: '/downloads',
      name: 'downloads',
      component: () => import('../views/DownloadsView.vue'),
    },
    {
      path: '/jobs',
      name: 'jobs',
      component: () => import('../views/JobsView.vue'),
    },
    {
      path: '/opml',
      name: 'opml',
      component: () => import('../views/OPMLView.vue'),
    },
  ],
})

export default router
