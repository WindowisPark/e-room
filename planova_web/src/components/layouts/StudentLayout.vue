<template>
  <div class="layout-wrapper">
    <StudentHeader class="fixed-header" />
    <div class="student-layout">
      <Sidebar :activeMenu="activeMenu" @menu-click="handleMenuClick" class="fixed-sidebar" />
      <main class="content">
        <slot></slot>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import Sidebar from './Sidebar.vue';
import StudentHeader from './StudentHeader.vue';

const activeMenu = ref('home');
const router = useRouter();

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
  background-color: #f9f9f9;
  overflow-y: auto;
  min-height: calc(100vh - 60px);
}
</style>