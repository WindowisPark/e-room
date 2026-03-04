import { createRouter, createWebHistory } from 'vue-router';
import HomePage from '../pages/HomePage.vue';
import authRoutes from './auth';
import informationRoutes from './information';
import supportRoutes from './support';
import StudentRoutes from './student';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomePage,
    },
    ...authRoutes,
    ...informationRoutes,
    ...supportRoutes,
    ...StudentRoutes
  ],
});

router.beforeEach((to, from, next) => {
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth);
  if (!requiresAuth) return next();

  const auth = localStorage.getItem('auth');
  const token = auth ? JSON.parse(auth).access_token : null;

  if (token) {
    next();
  } else {
    next({ path: '/auth/login', query: { redirect: to.fullPath } });
  }
});

export default router;
