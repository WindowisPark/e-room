<script setup>
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();

defineProps({
  activeMenu: {
    type: String,
    default: 'main'
  }
});

const currentMenu = computed(() => {
  const path = route.path;

  if (path.includes('/student/aitutor')) return 'aitutor';
  if (path.includes('/student/pdf')) return 'pdf';
  if (path.includes('/student/calendar')) return 'calendar';
  if (path.includes('/student/resume')) return 'resume';
  if (path.includes('/student/jobs')) return 'jobs';
  if (path.includes('/student/coverletter')) return 'coverletter';
  if (path.includes('/student/myroom')) return 'myroom';
  if (path.includes('/student/support')) return 'support';

  return 'main';
});

const emit = defineEmits(['menu-click']);

const handleMenuClick = (menuName) => {
  emit('menu-click', menuName);

  if (menuName === 'main') router.push('/student/main');
  else router.push(`/student/${menuName}`);
};

const navigateToHome = () => {
  emit('menu-click', 'main');
  router.push('/student/main');
};
</script>

<template>
  <aside class="sidebar">
    <div class="logo-container" @click="navigateToHome" style="cursor: pointer;">
      <img src="@/assets/images/planova-small-logo.jpg" alt="로고" class="logo">
    </div>

    <nav class="nav-menu" aria-label="주 메뉴">
      <!-- 홈 -->
      <button
        type="button"
        class="nav-item"
        :class="{ active: currentMenu === 'main' }"
        :aria-current="currentMenu === 'main' ? 'page' : undefined"
        @click="handleMenuClick('main')"
      >
        <i class="fa-solid fa-house nav-icon"></i>
        <span class="nav-text">홈</span>
      </button>

      <!-- 학습 섹션 -->
      <div class="section-label" aria-hidden="true">학습</div>

      <button
        type="button"
        class="nav-item"
        :class="{ active: currentMenu === 'pdf' }"
        :aria-current="currentMenu === 'pdf' ? 'page' : undefined"
        @click="handleMenuClick('pdf')"
      >
        <i class="fa-solid fa-file-pdf nav-icon"></i>
        <span class="nav-text">PDF 학습</span>
      </button>

      <button
        type="button"
        class="nav-item"
        :class="{ active: currentMenu === 'aitutor' }"
        :aria-current="currentMenu === 'aitutor' ? 'page' : undefined"
        @click="handleMenuClick('aitutor')"
      >
        <i class="fa-solid fa-robot nav-icon"></i>
        <span class="nav-text">AI 튜터</span>
      </button>

      <!-- 커리어 섹션 -->
      <div class="section-label" aria-hidden="true">커리어</div>

      <button
        type="button"
        class="nav-item"
        :class="{ active: currentMenu === 'resume' }"
        :aria-current="currentMenu === 'resume' ? 'page' : undefined"
        @click="handleMenuClick('resume')"
      >
        <i class="fa-solid fa-id-card nav-icon"></i>
        <span class="nav-text">이력서</span>
      </button>

      <button
        type="button"
        class="nav-item"
        :class="{ active: currentMenu === 'jobs' }"
        :aria-current="currentMenu === 'jobs' ? 'page' : undefined"
        @click="handleMenuClick('jobs')"
      >
        <i class="fa-solid fa-building nav-icon"></i>
        <span class="nav-text">기업 조사</span>
      </button>

      <button
        type="button"
        class="nav-item"
        :class="{ active: currentMenu === 'coverletter' }"
        :aria-current="currentMenu === 'coverletter' ? 'page' : undefined"
        @click="handleMenuClick('coverletter')"
      >
        <i class="fa-solid fa-pen-nib nav-icon"></i>
        <span class="nav-text">자소서</span>
      </button>

      <!-- 관리 섹션 -->
      <div class="section-label" aria-hidden="true">관리</div>

      <button
        type="button"
        class="nav-item"
        :class="{ active: currentMenu === 'calendar' }"
        :aria-current="currentMenu === 'calendar' ? 'page' : undefined"
        @click="handleMenuClick('calendar')"
      >
        <i class="fa-solid fa-calendar-days nav-icon"></i>
        <span class="nav-text">캘린더</span>
      </button>

      <button
        type="button"
        class="nav-item"
        :class="{ active: currentMenu === 'myroom' }"
        :aria-current="currentMenu === 'myroom' ? 'page' : undefined"
        @click="handleMenuClick('myroom')"
      >
        <i class="fa-solid fa-chart-bar nav-icon"></i>
        <span class="nav-text">내 활동</span>
      </button>

      <button
        type="button"
        class="nav-item"
        :class="{ active: currentMenu === 'support' }"
        :aria-current="currentMenu === 'support' ? 'page' : undefined"
        @click="handleMenuClick('support')"
      >
        <i class="fa-solid fa-headset nav-icon"></i>
        <span class="nav-text">고객지원</span>
      </button>
    </nav>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 100px;
  background-color: #ffffff;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
  height: 100vh;
  overflow-y: auto;
  z-index: 1000;
}

.logo-container {
  margin-bottom: 24px;
}

.logo {
  width: 50px;
  height: 50px;
  border-radius: 50%;
}

.nav-menu {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  width: 100%;
}

.section-label {
  font-size: 11px;
  font-weight: 600;
  color: #888;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  width: 100%;
  text-align: center;
  padding: 4px 0 0;
  border-top: 1px solid #f0f0f0;
  margin-top: 4px;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  width: 100%;
  cursor: pointer;
  transition: color 0.2s ease;
  padding: 5px 0;
  /* button reset */
  background: none;
  border: none;
  outline: none;
}

.nav-item:focus-visible {
  outline: 2px solid #F76707;
  outline-offset: -2px;
  border-radius: 4px;
}

.nav-icon {
  width: 24px;
  height: 24px;
  font-size: 18px;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #999;
  transition: color 0.2s ease;
}

.nav-text {
  font-size: 11px;
  color: #666;
  transition: color 0.2s ease;
  text-align: center;
}

.nav-item.active .nav-icon,
.nav-item.active .nav-text {
  color: #F76707;
}

.nav-item.active .nav-text {
  font-weight: 500;
}

.nav-item:hover .nav-icon,
.nav-item:hover .nav-text {
  color: #F76707;
}
</style>
