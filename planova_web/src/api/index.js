// src/api/index.jsi
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';
import router from '@/router';
import qs from "qs";

axios.defaults.paramsSerializer = params => {
  return qs.stringify(params);
}

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,  // ✅ 변수명 정확히 일치시킴
  timeout: 10000,
});

// 요청 인터셉터
instance.interceptors.request.use(
  (config) => {
    // JWT 추출 - Pinia 스토어를 직접 사용하는 대신 함수로 분리하거나 로컬 스토리지에서 직접 가져올 수 있습니다
    try {
      const token = localStorage.getItem('token'); // 또는 다른 방식으로 토큰 가져오기
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
      }
    } catch (error) {
      console.error('토큰 가져오기 실패:', error);
    }
    return config;
  },
  (error) => {
    console.log(error);
    return Promise.reject(error);
  }
);

// 응답 인터셉터
instance.interceptors.response.use(
  (response) => {
    // 성공 상태 코드 확장 (200, 201, 204 등)
    if (response.status >= 200 && response.status < 300) {
      return response;
    }
    if (response.status === 404) {
      return Promise.reject('404: 페이지 없음 ' + response.request);
    }
    return response;
  },
  async (error) => {
    if (error.response?.status === 401) {
      try {
        // 로그아웃 처리를 직접 호출하는 대신 로컬 스토리지에서 토큰을 제거
        localStorage.removeItem('token');
        // 또는 이벤트를 통해 로그아웃 처리
        window.dispatchEvent(new CustomEvent('logout'));
      } catch (e) {
        console.error('로그아웃 처리 오류:', e);
      }
      router.push('/auth/login?error=login_required');
      return Promise.reject({ error: '로그인이 필요한 서비스입니다.' });
    } else if (error.response?.status === 403) {
      return Promise.reject({ error: '권한이 부족합니다.' });
    }
    return Promise.reject(error);
  }
);

export default instance;