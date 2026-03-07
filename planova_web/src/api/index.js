// src/api/index.js
import axios from 'axios';
import router from '@/router';
import qs from "qs";

axios.defaults.paramsSerializer = params => {
  return qs.stringify(params);
}

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ? import.meta.env.VITE_API_BASE_URL + '/api/v1' : '/api/v1',
  timeout: 10000,
});

// 요청 인터셉터
instance.interceptors.request.use(
  (config) => {
    try {
      const auth = localStorage.getItem('auth');
      const token = auth ? JSON.parse(auth).access_token : null;
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
      }
    } catch (error) {
      console.error('토큰 가져오기 실패:', error);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 토큰 갱신 동시 요청 방지
let isRefreshing = false;
let refreshSubscribers = [];

function onRefreshed(newToken) {
  refreshSubscribers.forEach(cb => cb(newToken));
  refreshSubscribers = [];
}

function addRefreshSubscriber(cb) {
  refreshSubscribers.push(cb);
}

function clearAuthAndRedirect() {
  localStorage.removeItem('auth');
  window.dispatchEvent(new CustomEvent('logout'));
  router.push('/auth/login?error=login_required');
}

// 응답 인터셉터
instance.interceptors.response.use(
  (response) => {
    if (response.status >= 200 && response.status < 300) {
      return response;
    }
    if (response.status === 404) {
      return Promise.reject('404: 페이지 없음 ' + response.request);
    }
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      // refresh-token 요청 자체가 401이면 즉시 로그아웃
      if (originalRequest.url?.includes('/auth/refresh-token')) {
        clearAuthAndRedirect();
        return Promise.reject({ error: '로그인이 필요한 서비스입니다.' });
      }

      originalRequest._retry = true;

      try {
        const auth = localStorage.getItem('auth');
        const refreshToken = auth ? JSON.parse(auth).refresh_token : null;

        if (!refreshToken) {
          clearAuthAndRedirect();
          return Promise.reject({ error: '로그인이 필요한 서비스입니다.' });
        }

        if (isRefreshing) {
          // 이미 갱신 중이면 대기 큐에 추가
          return new Promise((resolve) => {
            addRefreshSubscriber((newToken) => {
              originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
              resolve(instance(originalRequest));
            });
          });
        }

        isRefreshing = true;

        const { data } = await instance.post('/auth/refresh-token', JSON.stringify(refreshToken), {
          headers: { 'Content-Type': 'application/json' },
        });

        // localStorage 업데이트
        const authData = JSON.parse(localStorage.getItem('auth'));
        authData.access_token = data.access_token;
        localStorage.setItem('auth', JSON.stringify(authData));

        isRefreshing = false;
        onRefreshed(data.access_token);

        // 원래 요청 재시도
        originalRequest.headers['Authorization'] = `Bearer ${data.access_token}`;
        return instance(originalRequest);
      } catch (refreshError) {
        isRefreshing = false;
        refreshSubscribers = [];
        clearAuthAndRedirect();
        return Promise.reject({ error: '로그인이 필요한 서비스입니다.' });
      }
    } else if (error.response?.status === 403) {
      return Promise.reject({ error: '권한이 부족합니다.' });
    }
    return Promise.reject(error);
  }
);

export default instance;