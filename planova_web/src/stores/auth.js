import { ref, computed } from 'vue';
import { defineStore } from 'pinia';

const STORAGE_KEY = 'auth';

const initState = {
  user_id: null,
  username: '',
  email: '',
  is_admin: false,
  access_token: '',
  refresh_token: '',
  token_type: 'bearer',
};

export const useAuthStore = defineStore('auth', () => {
  const state = ref({ ...initState });

  const isLogin = computed(() => !!state.value.access_token);
  const isAdmin = computed(() => state.value.is_admin);
  const userId = computed(() => state.value.user_id);
  const username = computed(() => state.value.username);
  const email = computed(() => state.value.email);
  const token = computed(() => state.value.access_token);

  const load = () => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      state.value = JSON.parse(saved);
    }
  };

  const setAuth = (response) => {
    state.value = {
      user_id: response.user_id,
      username: response.username,
      email: response.email,
      is_admin: response.is_admin ?? false,
      access_token: response.access_token,
      refresh_token: response.refresh_token,
      token_type: response.token_type ?? 'bearer',
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state.value));
  };

  const logout = () => {
    state.value = { ...initState };
    localStorage.removeItem(STORAGE_KEY);
  };

  const getToken = () => state.value.access_token;

  // 앱 시작 시 자동 복원
  load();

  return { state, isLogin, isAdmin, userId, username, email, token, setAuth, logout, getToken };
});
