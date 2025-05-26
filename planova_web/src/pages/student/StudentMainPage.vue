<template>
  <div class="membership-page">
    <div class="page-container">
      <div class="left-section">
        <div class="offer-card">
          <div class="limited-time-banner">
            <div class="countdown-text">한정 기간 이벤트!</div>
          </div>
          <!-- 이벤트 이미지 컨테이너에 스포트라이트 효과 추가 -->
          <div class="event-image-container spotlight-container">
            <div class="spotlight-effect"></div>
            <img src="@/assets/images/planova_open_event.png" alt="플래노바 오픈 이벤트" class="event-image">
          </div>
          
          <!-- 플래닛 수량 표시 섹션 개선 -->
          <div class="credit-breakdown">
            <div class="credit-item">
              <div class="credit-amount">300플래닛</div>
              <div class="credit-label">기본 제공</div>
            </div>
            <div class="plus-divider">+</div>
            <div class="credit-item bonus highlight-bonus">
              <div class="bonus-badge">BONUS</div>
              <div class="credit-amount">100플래닛</div>
              <div class="credit-label">보너스 제공</div>
            </div>
            <div class="equals-divider">=</div>
            <div class="credit-item total">
              <div class="credit-amount glow-text">400플래닛</div>
              <div class="credit-label">총 플래닛</div>
            </div>
          </div>
        </div>
        
        <!-- 버튼 개선 - 움직이는 애니메이션 추가 -->
        <router-link to="/information/planet" class="purchase-button-link">
          <button class="purchase-button">
            <div class="button-content">
              <span class="button-text">플래닛 구매하기</span>
              <span class="button-icon">→</span>
            </div>
            <div class="button-shine"></div>
          </button>
        </router-link>
      </div>
      
      <div class="right-section">
        <!-- 나머지 내용은 그대로 유지 -->
        <div class="user-info-card">
          <div class="calendar-container">
            <v-calendar 
              :attributes="calendarAttributes"
              :is-expanded="true"
              :columns="1"
              :rows="1"
              title-position="left"
              class="custom-calendar"
              color="indigo"
              :masks="masks"
            />
            <!-- 개선된 "오늘 일정이 없습니다" 메시지 -->
            <div v-if="!hasTodayEvent" class="no-event-message">
              <a href="/student/calendar" class="no-event-link">
                <span class="no-event-icon">📅</span>
                <span class="no-event-text">
                  <strong>오늘</strong>은 등록된 일정이 없습니다.<br>
                  새로운 일정을 추가해보세요!
                </span>
                <button class="no-event-button">일정 등록하기</button>
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="features-section">
        <img
          :src="featureImages[currentImageIndex]"
          alt="플래노바 오픈 이벤트"
          class="event-image"
          style="background-color: white; width: 100%; height: 100%; object-fit: cover; display: block;"
        >
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import 'v-calendar/dist/style.css';

export default {
  setup() {
    const masks = {
      title: 'YYYY년 M월'
    };

    const events = ref([
      { date: new Date(2025, 2, 18), title: '학교 수업', type: 'class' },
      { date: new Date(2025, 2, 20), title: '영어 학습', type: 'study' }
    ]);

    const calendarAttributes = computed(() => [
      {
        key: 'today',
        highlight: {
          color: 'indigo',
          fillMode: 'solid'
        },
        dates: new Date()
      },
      ...events.value.filter(event => event.type === 'class').map(event => ({
        key: `class-${event.date.toString()}`,
        dates: event.date,
        popover: {
          label: event.title
        }
      })),
      ...events.value.filter(event => event.type === 'study').map(event => ({
        key: `study-${event.date.toString()}`,
        dates: event.date,
        popover: {
          label: event.title
        }
      }))
    ]);

    const currentImageIndex = ref(0);
    // Use Vite-compatible image imports
    const featureImages = [
      new URL('@/assets/images/planova_main_1.png', import.meta.url).href,
      new URL('@/assets/images/planova_main_2.png', import.meta.url).href,
      new URL('@/assets/images/planova_main_3.png', import.meta.url).href,
      new URL('@/assets/images/planova_main_4.png', import.meta.url).href
    ];

    let intervalId = null;

    function nextImage() {
      // Defensive: ensure featureImages is an array with length
      if (Array.isArray(featureImages) && featureImages.length > 0) {
        currentImageIndex.value = (currentImageIndex.value + 1) % featureImages.length;
      } else {
        currentImageIndex.value = 0;
      }
    }

    onMounted(() => {
      // Defensive: reset to first image on mount
      currentImageIndex.value = 0;
      intervalId = setInterval(nextImage, 2000);
    });

    onBeforeUnmount(() => {
      if (intervalId) clearInterval(intervalId);
    });

    const today = new Date();
    const hasTodayEvent = computed(() => {
      return events.value.some(event => {
        return (
          event.date.getFullYear() === today.getFullYear() &&
          event.date.getMonth() === today.getMonth() &&
          event.date.getDate() === today.getDate()
        );
      });
    });

    return {
      calendarAttributes,
      masks,
      currentImageIndex,
      featureImages,
      hasTodayEvent
    };
  }
}
</script>

<style scoped>
.membership-page {
  font-family: 'Pretendard', 'Apple SD Gothic Neo', sans-serif;
  max-width: 1200px;
  margin: 0 auto;
  margin-top: 40px;
  padding: 20px;
  color: #333;
  background-color: #f9f9f9;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
}

.page-container {
  display: flex;
  gap: 30px;
  position: relative;
  margin-bottom: 30px;
}

.special-offer-badge {
  background: linear-gradient(135deg, #FF6B00, #FF9500);
  color: white;
  padding: 20px 50px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 30px;
  box-shadow: 0 5px 15px rgba(255, 103, 7, 0.3);
  display: inline-block;
  margin-bottom: 15px;
  transition: all 0.3s ease;
  position: absolute;
  top: 10px;
  left: 20px;
  z-index: 2;
}

.special-offer-badge.static-badge {
  /* Remove animation for static badge */
  /* No extra styles needed, just disables animation */
}

/* 이벤트 이미지 스포트라이트 효과 */
.spotlight-container {
  position: relative;
  text-align: center;
  margin: 45px 0 25px;
  overflow: hidden;
  border-radius: 12px;
  box-shadow: 0 15px 30px rgba(255, 107, 0, 0.15);
  transition: all 0.5s ease;
}

.spotlight-effect {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at 50% 50%, rgba(255, 255, 255, 0.8), transparent 60%);
  opacity: 0;
  z-index: 2;
  pointer-events: none;
  animation: spotlight 5s infinite;
}

@keyframes spotlight {
  0% { opacity: 0; transform: scale(0.8); }
  50% { opacity: 0.5; transform: scale(1.2); }
  100% { opacity: 0; transform: scale(0.8); }
}

.event-image {
  width: 100%;
  display: block;
  transition: transform 0.7s ease;
  border: 6px;
  z-index: 1;
  filter: brightness(1.05);
}

.spotlight-container:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(255, 107, 0, 0.2);
}

.spotlight-container:hover .event-image {
  transform: scale(1.05);
}

/* 한정 시간 배너 스타일 */
.limited-time-banner {
  position: absolute;
  top: 0px;
  left: 0px;
  background: linear-gradient(90deg, #FF3B00, #FF9500);
  color: white;
  padding: 14px 28px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 20px;
  box-shadow: -5px 5px 15px rgba(0, 0, 0, 0.2);
  z-index: 3;
  transform: translateX(0);
  animation: slideIn 0.5s ease-out 1s forwards, attention 3s 2s infinite;
}

.countdown-text {
  display: flex;
  align-items: center;
}

.countdown-text::before {
  content: "⏱️";
  margin-right: 10px;
  font-size: 25px;
}

@keyframes slideInLeft {
  from { transform: translateX(-100%); }
  to { transform: translateX(0); }
}

@keyframes attention {
  0% { transform: translateX(0); }
  5% { transform: translateX(-5px); }
  10% { transform: translateX(5px); }
  15% { transform: translateX(-5px); }
  20% { transform: translateX(0); }
  100% { transform: translateX(0); }
}

.left-section {
  flex: 3;
  background: linear-gradient(135deg, #FFFAF4, #FFF6E8);
  border-radius: 20px;
  padding: 35px;
  position: relative;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.07);
  border: none;
}

.offer-card {
  background-color: white;
  border-radius: 16px;
  padding: 30px;
  padding-top: 50px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.07);
  position: relative;
  overflow: visible; 
  border: none;
  transform: translateY(0);
  transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.4s ease;
}

.offer-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 15px 30px rgba(0, 0, 0, 0.1);
}

/* 보너스 플래닛 강조 스타일 */
.highlight-bonus {
  position: relative;
  padding: 8px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(16, 185, 129, 0.05));
  border-radius: 8px;
  border: 2px dashed #10B981;
}

.bonus-badge {
  position: absolute;
  top: -10px;
  right: -10px;
  background: #10B981;
  color: white;
  font-size: 12px;
  font-weight: bold;
  padding: 3px 8px;
  border-radius: 20px;
  box-shadow: 0 3px 10px rgba(16, 185, 129, 0.3);
}

@keyframes bonus-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
}

@keyframes rotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 총 플래닛 숫자에 빛나는 효과 */
.glow-text {
  color: #F76707;
  font-size: 26px !important;
  font-weight: 800;
  text-shadow: 0 0 10px rgba(247, 103, 7, 0.5);
  animation: glow 2s ease-in-out infinite;
}

@keyframes glow {
  0%, 100% { text-shadow: 0 0 10px rgba(247, 103, 7, 0.5); }
  50% { text-shadow: 0 0 25px rgba(247, 103, 7, 0.8); }
}

/* 크레딧 브레이크다운 */
.credit-breakdown {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 25px;
  padding: 20px;
  background: linear-gradient(135deg, #F8F9FF, #EEF2FF);
  border-radius: 12px;
  border: 1px solid #E0E7FF;
}

.credit-item {
  text-align: center;
  transition: transform 0.3s ease;
}

.credit-item:hover {
  transform: scale(1.1);
}

.credit-amount {
  font-size: 20px;
  font-weight: bold;
  color: #333;
}

.credit-label {
  font-size: 12px;
  color: #666;
  margin-top: 2px;
}

.credit-item.bonus .credit-amount {
  color: #10B981;
}

.plus-divider, .equals-divider {
  font-size: 18px;
  font-weight: bold;
  color: #666;
}

/* 버튼 스타일 개선 */
.purchase-button-link {
  display: block;
  text-decoration: none;
  width: 100%;
  margin-top: 30px;
}

.purchase-button {
  width: 100%;
  padding: 20px;
  background: #ff5900;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 22px;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.button-content {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 10px;
}

.button-icon {
  transition: transform 0.3s ease;
}

.button-shine {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg, 
    rgba(255, 255, 255, 0) 0%, 
    rgba(255, 255, 255, 0.2) 50%, 
    rgba(255, 255, 255, 0) 100%
  );
  transform: translateX(-100%);
  animation: button-shine 3s infinite;
}

@keyframes button-shine {
  0% { transform: translateX(-100%); }
  20% { transform: translateX(100%); }
  100% { transform: translateX(100%); }
}

.purchase-button:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 30px rgba(247, 103, 7, 0.4);
}

.purchase-button:hover .button-icon {
  transform: translateX(5px);
}

.right-section {
  flex: 2;
}

.user-info-card {
  background-color: #fff9ef;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.07);
  height: 100%;
  display: flex;
  flex-direction: column;
  border: none;
  position: relative;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.greeting {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 10px;
  color: #222;
  position: relative;
  display: inline-block;
}

.subscription-info {
  color: #666;
  font-size: 14px;
  margin-bottom: 30px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.calendar-container {
  margin-top: 10px;
  width: 100%;
}

:deep(.custom-calendar) {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
  background-color: white;
  width: 100%;
}

:deep(.vc-title) {
  font-weight: bold;
  font-size: 20px;
  background-color: white;
}

:deep(.vc-weekday) {
  color: #888;
  font-size: 14px;
  font-weight: normal;
}

:deep(.vc-day) {
  font-size: 14px;
  color: #333;
  height: 50px;
}

:deep(.vc-day-content) {
  height: 45px;
  width: 45px;
  align-items: center;
  justify-content: center;
}

:deep(.vc-container) {
  border: none;
}

:deep(.vc-highlight) {
  background-color: #ff7300
}

:deep(.vc-day.is-today) {
  font-weight: bold;
}

:deep(.vc-day.is-not-in-month) {
  opacity: 0.4;
}

/* 개선된 '오늘 일정이 없습니다' 메시지 스타일 */
.no-event-message {
  margin-top: 25px;
  padding: 20px;
  background: linear-gradient(135deg, #FFF8F0, #FFF0E0);
  border-radius: 16px;
  border: 2px dashed #FFB366;
  text-align: center;
  position: relative;
  box-shadow: 0 8px 20px rgba(255, 107, 0, 0.08);
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  overflow: hidden;
}

.no-event-message::before {
  content: "";
  position: absolute;
  top: -50%;
  left: -60%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255, 180, 0, 0.1) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.5s ease;
  pointer-events: none;
}

.no-event-icon {
  display: block;
  margin: 0 auto 10px;
  font-size: 28px;
  opacity: 0.9;
  transition: transform 0.4s ease;
}

.no-event-link {
  color: #ff6b00;
  font-weight: 600;
  text-decoration: none;
  display: block;
  transition: all 0.3s ease;
  padding: 5px;
  border-radius: 10px;
  position: relative;
}

.no-event-text {
  font-size: 16px;
  line-height: 1.5;
  color: #555;
}

.no-event-text strong {
  color: #ff6b00;
  font-weight: 700;
}

.no-event-link::after {
  content: "";
  display: inline-block;
  margin-left: 5px;
  opacity: 0;
  transform: translateX(-10px);
  transition: all 0.3s ease;
}

.no-event-message:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 30px rgba(255, 107, 0, 0.15);
  border-color: #FF8533;
}

.no-event-message:hover::before {
  opacity: 1;
  animation: shine 2s infinite;
}

.no-event-message:hover .no-event-icon {
  transform: scale(1.2) rotate(10deg);
}

.no-event-link:hover {
  background-color: rgba(255, 107, 0, 0.07);
}

.no-event-link:hover::after {
  opacity: 1;
  transform: translateX(5px);
}

.no-event-link:hover .no-event-text {
  color: #333;
}

.no-event-button {
  margin-top: 12px;
  background: linear-gradient(90deg, #FF7A00, #FF9500);
  border: none;
  color: white;
  padding: 8px 20px;
  border-radius: 50px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  opacity: 0;
  transform: translateY(10px);
  box-shadow: 0 4px 15px rgba(255, 122, 0, 0.25);
}

.no-event-message:hover .no-event-button {
  opacity: 1;
  transform: translateY(0);
}

.no-event-button:hover {
  background: linear-gradient(90deg, #FF6B00, #FF8500);
  box-shadow: 0 6px 20px rgba(255, 122, 0, 0.35);
  transform: translateY(-2px);
}

@keyframes shine {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 피처 섹션 스타일 유지 */
.features-section {
  margin-top: 50px;
  background-color: white;
  border-radius: 20px;
  padding: 0;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.07);
  border: none;
  position: relative;
  overflow: hidden;
}

.features-section::before {
  content: "";
  position: absolute;
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(247, 103, 7, 0.05), transparent);
  top: -150px;
  right: -150px;
  border-radius: 50%;
}


.features-header {
  position: relative;
  margin-bottom: 50px;
  text-align: center;
  padding: 20px 0;
  overflow: hidden;
}

.glow-effect {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  background: radial-gradient(circle, rgba(247, 103, 7, 0.2) 0%, rgba(255, 255, 255, 0) 70%);
  animation: pulse-glow 3s infinite;
}

@keyframes pulse-glow {
  0% { opacity: 0.5; }
  50% { opacity: 1; }
  100% { opacity: 0.5; }
}

.features-title {
  font-size: 28px;
  font-weight: bold;
  color: #333;
  text-align: center;
  position: relative;
  display: inline-block;
  padding: 0 15px;
}

.feature-cards {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 40px;
}

.feature-card {
  display: flex;
  align-items: center;
  background-color: white;
  border-radius: 16px;
  padding: 25px 30px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
  border: none;
  transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.4s ease, background-color 0.3s ease;
  position: relative;
  overflow: hidden;
}

.feature-icon {
  width: 30px;
  height: 30px;
  margin-right: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s ease;
}

.feature-content {
  flex: 1;
}

.feature-text {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.feature-credit {
  font-size: 14px;
  color: #F76707;
  font-weight: 500;
}

.check-icon {
  width: 32px;
  height: 32px;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  background-image: url('@/assets/images/studentmain-noncheck.png');
  transition: transform 0.3s ease;
}

.check-icon.checked {
  background-image: url('@/assets/images/studentmain-check.png');
  animation: bounce 0.5s ease;
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {transform: translateY(0);}
  40% {transform: translateY(-10px);}
  60% {transform: translateY(-5px);}
}

/* 반응형 스타일 */
@media (max-width: 768px) {
  .page-container {
    flex-direction: column;
  }
  
  .right-section {
    margin-top: 40px;
  }
  
  .left-section {
    padding: 25px;
  }
  
  .special-offer-badge {
    font-size: 24px;
    padding: 15px 30px;
  }
  
  .credit-breakdown {
    flex-direction: column;
    gap: 10px;
  }
  
  .plus-divider, .equals-divider {
    transform: rotate(90deg);
  }
  
  .no-event-message {
    padding: 15px;
  }
  
  .no-event-icon {
    font-size: 24px;
    margin-bottom: 8px;
  }
  
  .no-event-text {
    font-size: 15px;
  }
  
  .no-event-button {
    padding: 6px 16px;
    font-size: 13px;
  }
}
</style>