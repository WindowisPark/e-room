<script setup>
import { useRouter } from 'vue-router';
import { ref, onMounted, onUnmounted } from 'vue';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const showDropdown = ref(false);
const authStore = useAuthStore();

const logout = () => {
  authStore.logout();
  router.push('/auth/login');
};

const toggleDropdown = () => {
  showDropdown.value = !showDropdown.value;
};

const handleOutsideClick = (e) => {
  if (!e.target.closest('.user-profile-container')) {
    showDropdown.value = false;
  }
};

onMounted(() => document.addEventListener('click', handleOutsideClick));
onUnmounted(() => document.removeEventListener('click', handleOutsideClick));
</script>

<template>
  <header class="student-header">
    <div class="logo-space">
    </div>
    <div class="right-section">
      <div class="user-profile-container" @click.stop="toggleDropdown">
        <div class="user-profile">
          <img src="@/assets/images/student-profile.png" alt="프로필" class="profile-image" />
        </div>

        <div v-if="showDropdown" class="mini-dropdown">
          <div class="user-header">
            <div class="user-name">{{ authStore.username }}</div>
            <div class="user-email">{{ authStore.email }}</div>
          </div>

          <div class="menu-divider"></div>

          <div class="menu-item logout-button" @click="logout">
            <i class="fa-solid fa-right-from-bracket"></i>
            <div class="item-name">로그아웃</div>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.student-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 30px;
  background-color: #ffffff;
  border-bottom: 1px solid #f0f0f0;
  width: 100%;
}

.logo-space {
  flex: 1;
}

.right-section {
  display: flex;
  align-items: center;
}

.user-profile-container {
  position: relative;
}

.user-profile {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.profile-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.mini-dropdown {
  position: absolute;
  top: 45px;
  right: 0;
  width: 240px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 10;
  overflow: hidden;
}

.user-header {
  padding: 15px;
  border-bottom: 1px solid #eee;
}

.user-name {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 3px;
}

.user-email {
  font-size: 14px;
  color: #888;
}

.menu-divider {
  height: 1px;
  background-color: #f0f0f0;
}

.menu-item {
  padding: 12px 15px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.menu-item:hover {
  background-color: #f9f9f9;
}

.menu-item i {
  color: #888;
  font-size: 14px;
}

.item-name {
  font-size: 15px;
  color: #333;
}

.logout-button:hover {
  background-color: #f5f5f5;
}
</style>
