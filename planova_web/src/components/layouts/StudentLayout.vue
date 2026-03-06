<template>
  <div class="layout-wrapper">
    <StudentHeader class="fixed-header" />
    <div class="student-layout">
      <Sidebar :activeMenu="activeMenu" @menu-click="handleMenuClick" class="fixed-sidebar" />
      <main class="content">
        <slot></slot>
      </main>
    </div>
    <nav class="bottom-nav">
      <router-link to="/student/main" class="nav-tab" :class="{ active: currentTab === 'home' }">
        <i class="fa-solid fa-house"></i>
        <span>홈</span>
      </router-link>
      <router-link to="/student/aitutor" class="nav-tab" :class="{ active: currentTab === 'learn' }">
        <i class="fa-solid fa-book-open"></i>
        <span>학습</span>
      </router-link>
      <router-link to="/student/resume" class="nav-tab" :class="{ active: currentTab === 'career' }">
        <i class="fa-solid fa-briefcase"></i>
        <span>커리어</span>
      </router-link>
      <router-link to="/student/calendar" class="nav-tab" :class="{ active: currentTab === 'calendar' }">
        <i class="fa-solid fa-calendar-days"></i>
        <span>캘린더</span>
      </router-link>
      <router-link to="/student/myroom" class="nav-tab" :class="{ active: currentTab === 'myroom' }">
        <i class="fa-solid fa-chart-bar"></i>
        <span>내 활동</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import Sidebar from './Sidebar.vue';
import StudentHeader from './StudentHeader.vue';

const activeMenu = ref('home');
const router = useRouter();
const route = useRoute();

const currentTab = computed(() => {
  const path = route.path;
  if (path.includes('/aitutor') || path.includes('/pdf')) return 'learn';
  if (path.includes('/resume') || path.includes('/jobs') || path.includes('/coverletter')) return 'career';
  if (path.includes('/calendar')) return 'calendar';
  if (path.includes('/myroom')) return 'myroom';
  return 'home';
});

const handleMenuClick = (menuName) => {
  activeMenu.value = menuName;
  if (menuName === 'home') {
    router.push({ name: 'studentMain' });
  } else if (menuName === 'pdf') {
    router.push({ name: 'studentPdf' });
  } else if (menuName === 'ai-tutor') {
    router.push({ name: 'studentAitutor' });
  } else if (menuName === 'calendar') {
    router.push({ name: 'studentCalendar' });
  } else if (menuName === 'myroom') {
    router.push({ name: 'studentMyroom' });
  } else if(menuName === 'faq'){
    router.push({ name: 'studentFaq'});
  } else if(menuName === 'support'){
    router.push({ name: 'studentSupport'});
  }
};
</script>

<style scoped>
.layout-wrapper {
  position: relative;
  min-height: 100vh;
}

.fixed-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 900;
  background-color: #ffffff;
  border-bottom: 1px solid #f0f0f0;
}

.student-layout {
  display: flex;
  min-height: 100vh;
  padding-top: 60px;
}

.fixed-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 1000;
  height: 100vh;
  overflow-y: auto;
}

.content {
  flex: 1;
  margin-left: 100px;
  background-color: var(--bg-page);
  overflow-y: auto;
  min-height: calc(100vh - 60px);
  display: flex;
  flex-direction: column;
}

/* ── 모바일 하단 탭 바 ── */
.bottom-nav {
  display: none;
}

@media (max-width: 768px) {
  .fixed-sidebar {
    display: none;
  }

  .content {
    margin-left: 0;
    padding-bottom: 64px;
  }

  .bottom-nav {
    display: flex;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 60px;
    background: white;
    border-top: 1px solid #f0f0f0;
    box-shadow: 0 -1px 8px rgba(0,0,0,0.08);
    z-index: 999;
  }
}

.nav-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  text-decoration: none;
  color: #999;
  font-size: 10px;
  font-weight: 500;
  transition: color 0.15s;
}

.nav-tab i { font-size: 18px; }

.nav-tab.active { color: #F76707; }
</style>