<script setup>
import { useRouter } from 'vue-router';
import { ref } from 'vue';

const router = useRouter();
const showDropdown = ref(false);

const logout = () => {
  localStorage.removeItem('isAuthenticated');
  router.push('/auth/login');
};

const goToPassPage = () => {
  router.push('/information/planet');
};

const goToPartnershipPage = () => {
  router.push('/information/partnership');
};

// New function to navigate to PDF page
const goToPdfPage = () => {
  router.push('/student/pdf');
};
</script>

<template>
  <header class="student-header">
    <div class="logo-space">
    </div>
    <div class="right-section">
      <div class="header-links">
        <router-link to="/information/planet" class="header-link">플래닛 구매</router-link>
        <router-link to="/information/partnership" class="header-link">기업 제휴</router-link>
      </div>
      <div class="user-profile-container"
            @mouseover="showDropdown = true"
            @mouseleave="showDropdown = false">
        <div class="user-profile">
          <img src="@/assets/images/student-profile.png" alt="프로필" class="profile-image" />
        </div>
        
        <div v-if="showDropdown" class="mini-dropdown">
          <div class="user-header">
            <div class="user-name">한가연</div>
            <div class="user-email">iamgayeonii@gmail.com</div>
          </div>
          
          <div class="menu-items">
            <div class="menu-item">
              <div class="item-name">플래닛</div>
              <div class="item-value">
                보유 중인 플래닛이 없습니다
              </div>
            </div>
          </div>
          
          <div class="menu-divider"></div>
          
          <div class="menu-item logout-button" @click="logout">
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
  gap: 20px;
}

.header-links {
  display: flex;
  gap: 20px;
}

.header-link {
  color: #333;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: color 0.2s ease;
  cursor: pointer;
}

.header-link:hover {
  color: #F37322;
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
  width: 280px;
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

.menu-items {
  padding: 5px 0;
}

.menu-item {
  padding: 12px 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.menu-item:hover {
  background-color: #f9f9f9;
}

.item-name {
  font-size: 15px;
  color: #333;
}

.item-value {
  display: flex;
  align-items: center;
  color: #666;
  font-size: 14px;
}

.divider {
  width: 1px;
  height: 12px;
  background-color: #ddd;
  margin: 0 8px;
}

.point-value {
  color: #ff5100;
  font-weight: 600;
}

.arrow-icon {
  color: #999;
  font-size: 18px;
  margin-left: 8px;
}

.menu-divider {
  height: 1px;
  background-color: #f0f0f0;
  margin: 5px 0;
}

.logout-button:hover {
  background-color: #f5f5f5;
}
</style>