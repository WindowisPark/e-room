<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import MenuGroup from './menu/MenuGroup.vue';
import AccountMenuGroup from './menu/AccountMenuGroup.vue';
import config from '@/config';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();
const state = ref({
  isNavShow: false
});
const router = useRouter();
const navClass = computed(() => (state.value.isNavShow ? 'collapse navbar-collapse show' : 'collapse navbar-collapse'));

const toggleNavShow = () => {
  state.value.isNavShow = !state.value.isNavShow;
};

const navigateToSignup = () => {
  router.push('/auth/login');
};

const navigateToMyPage = () => {
  router.push('/mypage');
};

const logout = () => {
  authStore.logout();
  router.push('/');
};
</script>

<template>
  <div class="navbar-wrapper">
    <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
      <div class="navbar-container">
        <router-link to="/" class="navbar-brand">
          <img src="@/assets/images/planova-logo.png" alt="PlANOVA 로고" class="logo-img" />
        </router-link>
        <button class="navbar-toggler" type="button" @click="toggleNavShow">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div :class="navClass" id="collapsibleNavbar">
          <ul class="navbar-nav me-auto">
            <li class="nav-item menu-spacing" v-for="menu in config.menus" :key="menu.title">
              <router-link class="nav-link" :to="menu.url">{{ menu.title }}</router-link>
            </li>
          </ul>
          <div class="auth-buttons">
            <template v-if="authStore.isLogin">
              <div class="user-greeting">
                <span class="welcome-text">{{ authStore.user.username }}님 환영합니다!</span>
                <div class="user-menu">
                  <button class="btn my-page-btn" @click="navigateToMyPage">마이페이지</button>
                  <button class="btn logout-btn" @click="logout">로그아웃</button>
                </div>
              </div>
            </template>
            <template v-else>
              <button class="btn btn-primary signup-btn" @click="navigateToSignup">
                시작하기
              </button>
            </template>
          </div>
        </div>
      </div>
    </nav>
  </div>
</template>

<style scoped>
.navbar-wrapper {
  width: 100vw;
  margin: 0;
  padding: 0;
  position: relative;
  left: 50%;
  right: 50%;
  margin-left: -50vw;
  margin-right: -50vw;
}

.navbar {
  width: 100%;
  padding: 15px 0;
  border-bottom: 1px solid #eaeaea;
  margin: 0;
}

.navbar-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 15px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
}

.navbar .logo-img {
  max-height: 50px;
  padding: 5px;
}

.navbar-nav {
  display: flex;
  align-items: center;
}

.menu-spacing {
  padding: 0 20px;
}

.nav-link {
  color: #333 !important;
  font-weight: 500;
  font-size: 20px;
}

.auth-buttons {
  display: flex;
  align-items: center;
}

.signup-btn {
  background-color: #F76707;
  border-color: #F76707;
  border-radius: 50px;
  padding: 8px 20px;
  font-weight: 500;
  color: white;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(247, 103, 7, 0.3);
}

.signup-btn:hover {
  background-color: #d95e06;
  border-color: #d95e06;
}

.user-greeting {
  display: flex;
  align-items: center;
  position: relative;
}

.welcome-text {
  font-weight: 500;
  color: #F76707;
  margin-right: 15px;
}

.user-menu {
  display: flex;
}

.my-page-btn {
  margin-right: 10px;
  padding: 8px 16px;
  background: transparent;
  color: #9b9898;
  border: none;
  font-weight: 500;
  cursor: pointer;
}

.my-page-btn:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.logout-btn {
  padding: 8px 16px;
  background: transparent;
  color: #9b9898;
  border: none;
  font-weight: 500;
  cursor: pointer;
}

.logout-btn:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

@media (max-width: 992px) {
  .navbar-collapse {
    width: 100%;
    margin-top: 15px;
  }

  .navbar-nav {
    margin-bottom: 15px;
  }

  .user-greeting {
    flex-direction: column;
    align-items: flex-start;
  }

  .welcome-text {
    margin-bottom: 10px;
  }
}
</style>
