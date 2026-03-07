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

function isTokenExpired(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    // 만료 60초 전부터 만료로 간주 (갱신 여유)
    return payload.exp * 1000 < Date.now() + 60000;
  } catch {
    return true;
  }
}

router.beforeEach(async (to, from, next) => {
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth);
  if (!requiresAuth) return next();

  const auth = localStorage.getItem('auth');
  let authData;
  try {
    authData = auth ? JSON.parse(auth) : null;
  } catch {
    authData = null;
  }
  const token = authData?.access_token;

  if (!token) {
    return next({ path: '/auth/login', query: { redirect: to.fullPath } });
  }

  if (isTokenExpired(token)) {
    const refreshToken = authData?.refresh_token;
    if (!refreshToken) {
      localStorage.removeItem('auth');
      return next({ path: '/auth/login', query: { redirect: to.fullPath } });
    }

    try {
      const { default: api } = await import('@/api');
      const { data } = await api.post('/auth/refresh-token', JSON.stringify(refreshToken), {
        headers: { 'Content-Type': 'application/json' },
      });
      authData.access_token = data.access_token;
      localStorage.setItem('auth', JSON.stringify(authData));
      return next();
    } catch {
      localStorage.removeItem('auth');
      return next({ path: '/auth/login', query: { redirect: to.fullPath } });
    }
  }

  next();
});

export default router;
