<script setup>
import { ref, computed } from 'vue';
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
  if (path.includes('/student/myroom')) return 'myroom';
  if (path.includes('/student/faq')) return 'faq';
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

const hoveredItem = ref(null);

const setHovered = (menuName) => {
  hoveredItem.value = menuName;
};

const clearHovered = () => {
  hoveredItem.value = null;
};
</script>

<template>
  <aside class="sidebar">
    <div class="logo-container" @click="navigateToHome" style="cursor: pointer;">
      <img src="@/assets/images/planova-small-logo.jpg" alt="로고" class="logo">
    </div>
    
    <nav class="nav-menu">
      <div 
        class="nav-item" 
        :class="{ active: currentMenu === 'main' }"
        @click="handleMenuClick('main')"
        @mouseenter="setHovered('main')"
        @mouseleave="clearHovered"
      >
      <div class="nav-icon">
        <img 
          :src="currentMenu === 'main' || hoveredItem === 'main'
            ? '/sidebar-home-click.png' 
            : '/sidebar-home.png'" 
          class="icon-image"
        />
      </div>
        <div class="nav-text">홈</div>
      </div>
      
      <div 
        class="nav-item" 
        :class="{ active: currentMenu === 'pdf' }"
        @click="handleMenuClick('pdf')"
        @mouseenter="setHovered('pdf')"
        @mouseleave="clearHovered"
      >
      <div class="nav-icon">
        <img 
          :src="currentMenu === 'pdf' || hoveredItem === 'pdf'
            ? '/sidebar-pdf-click.png' 
            : '/sidebar-pdf.png'" 
          class="icon-image"
        />
      </div>
        <div class="nav-text">학습</div>
      </div>
      
      <div 
        class="nav-item" 
        :class="{ active: currentMenu === 'aitutor' }"
        @click="handleMenuClick('aitutor')"
        @mouseenter="setHovered('aitutor')"
        @mouseleave="clearHovered"
      >
      <div class="nav-icon">
        <img 
          :src="currentMenu === 'aitutor' || hoveredItem === 'aitutor'
            ? '/sidebar-aitutor-click.png' 
            : '/sidebar-aitutor.png'" 
          class="icon-image"
        />
      </div>
         
        <div class="nav-text">AI 튜터</div>
      </div>
      
      <div 
        class="nav-item" 
        :class="{ active: currentMenu === 'calendar' }"
        @click="handleMenuClick('calendar')"
        @mouseenter="setHovered('calendar')"
        @mouseleave="clearHovered"
      >
      <div class="nav-icon">
        <img 
          :src="currentMenu === 'calendar' || hoveredItem === 'calendar'
            ? '/sidebar-calendar-click.png' 
            : '/sidebar-calendar.png'" 
          class="icon-image"
        />
      </div>
        <div class="nav-text">캘린더</div>
      </div>
      
      <div 
        class="nav-item" 
        :class="{ active: currentMenu === 'myroom' }"
        @click="handleMenuClick('myroom')"
        @mouseenter="setHovered('myroom')"
        @mouseleave="clearHovered"
      >
      <div class="nav-icon">
        <img 
          :src="currentMenu === 'myroom' || hoveredItem === 'myroom'
            ? '/sidebar-myroom-click.png' 
            : '/sidebar-myroom.png'" 
          class="icon-image"
        />
      </div>
        <div class="nav-text">마이룸</div>
      </div>
            
      <div 
        class="nav-item" 
        :class="{ active: currentMenu === 'support' }"
        @click="handleMenuClick('support')"
        @mouseenter="setHovered('support')"
        @mouseleave="clearHovered"
      >
      <div class="nav-icon">
        <img 
          :src="currentMenu === 'support' || hoveredItem === 'support'
            ? '/sidebar-support-click.png' 
            : '/sidebar-support.png'" 
          class="icon-image-support"
        />
      </div>
      <div class="nav-text">고객지원</div>
      </div>
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
  z-index: 1000;
}

.logo-container {
  margin-bottom: 30px;
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
  gap: 40px;
  width: 100%;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  width: 100%;
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 5px 0;
}

.nav-icon {
  width: 28px;
  height: 28px;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #666;
  transition: color 0.2s ease;
}

.active-icon {
  color: #F76707;
}

.icon-image {
  width: 30px;
  height: 30px;
  object-fit: contain;
}

.icon-image-support {
  width: 40px;
  height: 40px;
  object-fit: contain;
}

.nav-text {
  font-size: 12px;
  color: #666;
  transition: color 0.2s ease;
  margin-top: 4px;
}

.nav-item.active .nav-text {
  color: #F76707;
  font-weight: 500;
}

.nav-item:hover .nav-text {
  color: #F76707;
}
</style>