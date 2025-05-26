<template>
  <div class="dashboard">
    <div class="header">
      <h1 class="title">플래노바와 <span class="day-count">5</span>일째 함께하는중</h1>
    </div>

    <div class="attendance-card">
      <div class="attendance-row">
        <div class="day-circle">
          <div class="day-number">{{ currentDay }}</div>
          <div class="day-texts">
            <div class="day-greeting">연속 출석 현황</div>
            <div class="day-status">{{ consecutiveDays }}일째 출석 중</div>
          </div>
        </div>

        <div class="progress-container">
          <div class="progress-dots">
                          <template v-for="day in 7" :key="day">
              <div :class="['dot', attendanceStatus.completedDays.includes(day) ? 'completed' : '']">
                <span v-if="attendanceStatus.completedDays.includes(day)" class="check-icon">✓</span>
                <span v-else>{{ day }}</span>
              </div>
            </template>
          </div>
          <div class="progress-bar">
            <div class="progress-filled" :style="{ width: progressFillWidth }"></div>
          </div>
        </div>

        <button :class="attendanceBtnClass" @click="checkAttendance" :disabled="isLoading || !attendanceStatus.canCheckToday">
          {{ buttonText }}
        </button>
      </div>
    </div>
    
    <div class="toast-container" v-if="showToastFlag">
      <div class="toast-message">
        {{ toastMessage }}
      </div>
    </div>
    
    <div class="menu-section">
      <div class="menu-card">
        <div class="menu-header">
          <div class="menu-icon study-icon">📚</div>
          <div class="menu-title">학습</div>
        </div>
        <div class="menu-links">
          <div class="menu-link" @click="navigateToPdf('personal')">
            <span>생성된 문제(5)</span>
            <span class="arrow">›</span>
          </div>
          <div class="menu-link" @click="navigateToPdf('personal')">
            <span>생성된 요약 파일(2)</span>
            <span class="arrow">›</span>
          </div>
        </div>
      </div>

      <div class="menu-card">
        <div class="menu-header">
          <div class="menu-icon team-icon">👥</div>
          <div class="menu-title">팀스페이스</div>
        </div>
        <div class="menu-links">
        <div class="menu-link" @click="navigateToPdf('team')">
            <span>나의 팀스페이스(1)</span>
            <span class="arrow">›</span>
        </div>
        </div>
      </div>
    </div>    
    <div class="achievement-section">
      <h3 class="section-title">내 달성 과제</h3>
      <div class="achievements">
        <div class="achievement-card">
          <div class="achievement-icon book-icon"></div>
          <div class="achievement-text">Level 1</div>
        </div>
        <div class="achievement-card">
          <div class="achievement-icon chat-icon"></div>
          <div class="achievement-text">Level 1</div>
        </div>
        <div class="achievement-card">
          <div class="achievement-icon doc-icon"></div>
          <div class="achievement-text">Level 1</div>
        </div>
      </div>
    </div>
    
    <div class="chart-section">
      <div class="chart-header">
        <h3 class="section-title">학습 통계</h3>
        <div class="chart-controls">
          <div class="dropdown">
            최근 3개월 <span class="dropdown-icon">▼</span>
          </div>
          <div class="period">| 2025.01 - 2025.03</div>
        </div>
      </div>
      <div class="chart-container">
        <div class="placeholder-chart"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import LineChart from '@/components/LineChart.vue';
const currentDay = ref(1);
const consecutiveDays = ref(1);
const attendanceStatus = reactive({
  lastCheckDate: null,
  completedDays: [1],
  canCheckToday: true
});

const today = new Date();
const dateFormatOptions = { year: 'numeric', month: '2-digit', day: '2-digit' };
const formattedToday = today.toLocaleDateString('ko-KR', dateFormatOptions);

import { useRouter } from 'vue-router';
const router = useRouter();

const navigateToPdf = (tabType = 'personal') => {
  router.push({ path: '/student/pdf', query: { tab: tabType } });
};

const checkAttendance = () => {
  if (!attendanceStatus.canCheckToday) {
    showToast("오늘은 이미 출석체크를 완료했습니다!");
    return;
  }
  
  const nextDay = currentDay.value + 1;
  
  if (nextDay <= 7) {
    currentDay.value = nextDay;
    consecutiveDays.value += 1;
    attendanceStatus.completedDays.push(nextDay);
    attendanceStatus.lastCheckDate = new Date().toISOString();
    attendanceStatus.canCheckToday = false;
    progressFillWidth.value = `${(nextDay - 1) * 16.66}%`;
      
    saveAttendanceData();
  }
};

const saveAttendanceData = () => {
  localStorage.setItem('attendanceData', JSON.stringify({
    currentDay: currentDay.value,
    consecutiveDays: consecutiveDays.value,
    completedDays: attendanceStatus.completedDays,
    lastCheckDate: attendanceStatus.lastCheckDate,
    canCheckToday: attendanceStatus.canCheckToday
  }));
};

const loadAttendanceData = () => {
  const savedData = localStorage.getItem('attendanceData');
  if (savedData) {
    const data = JSON.parse(savedData);
    currentDay.value = data.currentDay;
    consecutiveDays.value = data.consecutiveDays;
    attendanceStatus.completedDays = data.completedDays;
    attendanceStatus.lastCheckDate = data.lastCheckDate;
    
    const lastCheck = new Date(data.lastCheckDate);
    const today = new Date();
    const isNewDay = lastCheck.getDate() !== today.getDate() || 
                    lastCheck.getMonth() !== today.getMonth() || 
                    lastCheck.getFullYear() !== today.getFullYear();
    
    attendanceStatus.canCheckToday = isNewDay;
    progressFillWidth.value = `${(currentDay.value - 1) * 16.66}%`;
  }
};

const toastMessage = ref('');
const showToastFlag = ref(false);

const showToast = (message) => {
  toastMessage.value = message;
  showToastFlag.value = true;
  
  setTimeout(() => {
    showToastFlag.value = false;
  }, 3000);
};

const progressFillWidth = ref('0%');
const isLoading = ref(false);
const buttonText = computed(() => {
  if (isLoading.value) {
    return '처리 중...';
  } else if (!attendanceStatus.canCheckToday) {
    return '완료';
  } else {
    return '출석';
  }
});

const attendanceBtnClass = computed(() => {
  if (!attendanceStatus.canCheckToday) {
    return 'attendance-btn completed';
  } else {
    return 'attendance-btn';
  }
});

onMounted(() => {
  loadAttendanceData();
});

const CircleProgress = {
  props: {
    percentage: {
      type: Number,
      required: true
    },
    color: {
      type: String,
      default: '#ff8c42'
    }
  },
  setup(props) {
    const radius = 40;
    const circumference = 2 * Math.PI * radius;
    const dashoffset = ref(circumference);

    onMounted(() => {
      const offset = circumference - (props.percentage / 100) * circumference;
      dashoffset.value = offset;
    });

    return {
      radius,
      circumference,
      dashoffset
    };
  },
  template: `
    <svg class="circle-progress" width="100" height="100" viewBox="0 0 100 100">
      <circle
        class="circle-bg"
        cx="50"
        cy="50"
        :r="radius"
        fill="none"
        stroke="#e6e6e6"
        stroke-width="10"
      />
      <circle
        class="circle-progress-value"
        cx="50"
        cy="50"
        :r="radius"
        fill="none"
        :stroke="color"
        stroke-width="10"
        stroke-linecap="round"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="dashoffset"
        transform="rotate(-90, 50, 50)"
      />
    </svg>
  `
};
</script>

<style scoped>
.dashboard {
  font-family: 'Noto Sans KR', sans-serif;
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
  padding: 24px;
  background-color: #f5f5f5;
  color: #333;
  position: relative;
}

.header {
  margin-bottom: 20px;
  width: 95%;
  margin-left: auto;
  margin-right: auto;
}

.title {
  font-size: 24px;
  font-weight: 700;
  margin: 0;
  color: #222;
}

.day-count {
  color: #ff8c42;
  font-weight: 800;
}

.attendance-card {
  background-color: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;
  width: 95%;
  margin-left: auto;
  margin-right: auto;
  transition: all 0.3s ease;
}

.attendance-card:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
}

.attendance-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.day-circle {
  width: 100px;
  height: 100px;
  background-color: #ff8c42;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  position: relative;
  padding: 10px;
  box-shadow: 0 4px 8px rgba(255, 140, 66, 0.3);
}

.day-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: white;
  color: #ff8c42;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 18px;
  margin-bottom: 8px;
}

.day-texts {
  text-align: center;
}

.day-greeting {
  font-size: 12px;
  margin-bottom: 4px;
  opacity: 0.9;
}

.day-status {
  font-size: 14px;
  font-weight: bold;
}

.progress-container {
  flex: 1;
  margin: 0 40px;
}

.progress-dots {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  position: relative;
  top: 0px;
}

.dot {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #eeeeee;
  font-size: 14px;
  color: #666;
  z-index: 2;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
  margin-top: 5px;
}

.dot.completed {
  background-color: #ff8c42;
  color: white;
  box-shadow: 0 2px 6px rgba(255, 140, 66, 0.4);
  border-radius: 50%;
  overflow: hidden;
  position: relative;
}

.check-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.progress-bar {
  height: 4px;
  background-color: #eeeeee;
  border-radius: 2px;
  position: relative;
  margin-top: -20px;
  z-index: 1;
  top: -10px;
}

.progress-filled {
  height: 100%;
  width: 14.3%;
  background-color: #ff8c42;
  border-radius: 2px;
  transition: width 0.5s ease;
}

.attendance-btn {
  background-color: #ff8c42;
  color: white;
  border: none;
  border-radius: 12px;
  padding: 12px 28px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  box-shadow: 0 4px 8px rgba(255, 140, 66, 0.3);
  transition: all 0.2s ease;
  min-width: 100px;
  position: relative;
  overflow: hidden;
}

.attendance-btn:hover:not(:disabled) {
  background-color: #ff7c32;
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(255, 140, 66, 0.4);
}

.attendance-btn:active:not(:disabled) {
  transform: translateY(1px);
  box-shadow: 0 2px 4px rgba(255, 140, 66, 0.3);
}

.attendance-btn:disabled {
  cursor: not-allowed;
  opacity: 0.8;
}

.attendance-btn.completed {
  background-color: #777777;
  box-shadow: 0 4px 8px rgba(119, 119, 119, 0.3);
}

.attendance-btn.completed:hover {
  background-color: #666666;
  box-shadow: 0 6px 12px rgba(119, 119, 119, 0.4);
}

.user-info {
  display: flex;
  background-color: #FFF5F0;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 20px;
  width: 95%;
  margin-left: auto;
  margin-right: auto;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
}

.info-item {
  flex: 1;
  text-align: center;
  padding: 0 10px;
  position: relative;
}

.border-x {
  border-left: 1px solid rgba(255, 140, 66, 0.2);
  border-right: 1px solid rgba(255, 140, 66, 0.2);
}

.info-label {
  font-size: 14px;
  color: #ff8c42;
  margin-bottom: 8px;
  font-weight: 500;
}

.info-value {
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.menu-section {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  width: 95%;
  margin-left: auto;
  margin-right: auto;
}

.menu-card {
  flex: 1;
  background-color: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.menu-card:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.menu-header {
  display: flex;
  align-items: center;
  margin-bottom: 18px;
}

.menu-icon {
  font-size: 22px;
  margin-right: 12px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
}

.study-icon {
  background-color: rgba(255, 193, 7, 0.15);
  color: #ffc107;
}

.team-icon {
  background-color: rgba(33, 150, 243, 0.15);
  color: #2196f3;
}

.menu-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.menu-links {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.menu-link {
  display: flex;
  justify-content: space-between;
  align-items: center;
  text-decoration: none;
  color: #555;
  font-size: 14px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  transition: all 0.2s ease;
  cursor: pointer; /* 클릭 가능한 커서 스타일 추가 */
}

.menu-link:last-child {
  border-bottom: none;
}

.menu-link:hover {
  color: #ff8c42;
}

.arrow {
  font-size: 20px;
  color: #999;
  transition: transform 0.2s ease;
}

.menu-link:hover .arrow {
  transform: translateX(3px);
  color: #ff8c42;
}

.stats-section {
  display: flex;
  background-color: #FFF5F0;
  border-radius: 16px;
  padding: 24px;
  gap: 20px;
  width: 95%;
  margin-left: auto;
  margin-right: auto;
  margin-bottom: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
}

.stat-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-3px);
}

.stat-chart {
  position: relative;
  width: 110px;
  height: 110px;
  margin-bottom: 15px;
}

.circle-progress {
  width: 100%;
  height: 100%;
}

.stat-percentage {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 18px;
  font-weight: 700;
  color: #333;
}

.stat-label {
  font-size: 14px;
  text-align: center;
  color: #555;
  font-weight: 500;
}

.achievement-section {
  width: 95%;
  margin: 0 auto 20px auto;
  background-color: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 16px 0;
  color: #333;
}

.achievements {
  display: flex;
  gap: 20px;
}

.achievement-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  background-color: #f9f9f9;
  padding: 20px;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.achievement-card:hover {
  background-color: #f0f0f0;
  transform: translateY(-3px);
}

.achievement-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  margin-bottom: 12px;
  background-position: center;
  background-repeat: no-repeat;
  background-size: 30px;
}

.book-icon {
  background-color: rgba(255, 193, 7, 0.15);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23FFC107' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 19.5A2.5 2.5 0 0 1 6.5 17H20'%3E%3C/path%3E%3Cpath d='M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z'%3E%3C/path%3E%3C/svg%3E");
}

.chat-icon {
  background-color: rgba(33, 150, 243, 0.15);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%232196F3' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z'%3E%3C/path%3E%3C/svg%3E");
}

.doc-icon {
  background-color: rgba(76, 175, 80, 0.15);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%234CAF50' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'%3E%3C/path%3E%3Cpolyline points='14 2 14 8 20 8'%3E%3C/polyline%3E%3Cline x1='16' y1='13' x2='8' y2='13'%3E%3C/line%3E%3Cline x1='16' y1='17' x2='8' y2='17'%3E%3C/line%3E%3Cpolyline points='10 9 9 9 8 9'%3E%3C/polyline%3E%3C/svg%3E");
}

.achievement-text {
  font-size: 14px;
  font-weight: 600;
  color: #555;
}

.chart-section {
  width: 95%;
  margin: 0 auto 20px auto;
  background-color: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chart-controls {
  display: flex;
  align-items: center;
}

.dropdown {
  display: flex;
  align-items: center;
  background-color: #f5f5f5;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  margin-right: 10px;
  transition: background-color 0.2s ease;
}

.dropdown:hover {
  background-color: #eeeeee;
}

.dropdown-icon {
  font-size: 10px;
  margin-left: 5px;
  color: #999;
}

.period {
  font-size: 14px;
  color: #ff8c42;
}

.chart-container {
  height: 200px;
}

.placeholder-chart {
  width: 100%;
  height: 100%;
  background: linear-gradient(to right, #f5f5f5 0%, #eeeeee 10%, #f5f5f5 20%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 8px;
}

@keyframes shimmer {
  0% {
    background-position: 100% 0;
  }
  100% {
    background-position: -100% 0;
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translate3d(0, 20px, 0);
  }
  to {
    opacity: 1;
    transform: translate3d(0, 0, 0);
  }
}

@keyframes fadeOut {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}

@media (max-width: 768px) {
  .menu-section {
    flex-direction: column;
  }
  
  .stats-section {
    flex-direction: column;
  }
  
  .stat-card {
    margin-bottom: 20px;
  }
  
  .achievements {
    flex-direction: column;
  }
  
  .achievement-card {
    margin-bottom: 10px;
  }
  
  .progress-container {
    margin: 0 15px;
  }
  
  .attendance-row {
    flex-direction: column;
    gap: 20px;
  }
  
  .day-circle {
    margin-bottom: 20px;
  }
  
  .attendance-btn {
    width: 100%;
  }
}
</style>