export default [
  {
    path: '/auth/login',
    name: 'login',
    component: () => import('../pages/auth/LoginPage.vue'),
  },
  {
    path: '/auth/signup',
    name: 'signup',
    component: () => import('../pages/auth/SignUpPage.vue'),
  },
  {
    path: '/student/main',
    name: 'studentMain',
    component: () => import('../pages/student/StudentMainPage.vue'),
    meta: { requiresAuth: true }
  },
];