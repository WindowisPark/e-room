<template>
  <div class="event-container">
    <div class="tab-container">
      <button
        :class="['tab-button', { active: activeTab === 'ongoing' }]"
        @click="activeTab = 'ongoing'"
      >
        진행중인 이벤트
      </button>
      <button
        :class="['tab-button', { active: activeTab === 'ended' }]"
        @click="activeTab = 'ended'"
      >
        진행종료된 이벤트
      </button>
    </div>

    <div v-if="activeTab === 'ongoing'" class="tab-content">
      <div class="event-grid">
        <div v-for="event in ongoingEvents" :key="event.id" class="event-card" @click="viewEventDetail(event)">
          <div class="event-thumbnail">
            <img :src="event.thumbnail" alt="이벤트 썸네일" />
            <div class="event-badge" v-if="event.badge">{{ event.badge }}</div>
          </div>
          <div class="event-info">
            <h3 class="event-card-title">{{ event.title }}</h3>
            <p class="event-card-period">{{ event.period }}</p>
          </div>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'ended'" class="tab-content">
      <div class="event-grid">
        <div v-for="event in endedEvents" :key="event.id" class="event-card ended" @click="viewEventDetail(event)">
          <div class="event-thumbnail">
            <img :src="event.thumbnail" alt="이벤트 썸네일" />
            <div class="event-ended-overlay">종료된 이벤트</div>
          </div>
          <div class="event-info">
            <h3 class="event-card-title">{{ event.title }}</h3>
            <p class="event-card-period">{{ event.period }}</p>
          </div>
        </div>
      </div>
    </div>

    <div v-if="selectedEvent" class="event-modal-backdrop" @click="closeEventDetail">
      <div class="event-modal" @click.stop>
        <button class="modal-close-btn" @click="closeEventDetail">×</button>
        
        <div class="modal-content">
          <h2 class="modal-title">{{ selectedEvent.title }}</h2>
          <p class="modal-period">{{ selectedEvent.period }}</p>
          
          <div class="event-detail-content">
            <div v-if="selectedEvent.type === 'attendance'" class="attendance-event">
              <div class="special-banner">
                <img :src="selectedEvent.bannerImage" alt="출석체크 이벤트 배너" />
              </div>
              
              <div class="special-info">
                <h3>{{ selectedEvent.title }}</h3>
                <p>매일 출석하고 다양한 포인트 혜택을 받아가세요! 연속 출석시 추가 보너스를 드립니다.</p>
                
                <div class="special-details">
                  <div class="detail-item">
                    <div class="detail-label">이벤트 기간</div>
                    <div class="detail-value">{{ selectedEvent.period }}</div>
                  </div>
                  <div class="detail-item">
                    <div class="detail-label">출석 보상</div>
                    <div class="detail-value highlight">1일 50포인트 적립</div>
                  </div>
                  <div class="detail-item">
                    <div class="detail-label">추가 보상</div>
                    <div class="detail-value">
                      5일 연속: <strong>500 포인트</strong><br>
                      10일 연속: <strong>700 포인트</strong><br>
                      한 달 출석 완료: <strong>2,000 포인트</strong>
                    </div>
                  </div>
                </div>
                
                <button 
                  class="primary-button"
                  :disabled="selectedEvent.isEnded"
                  @click="navigateToLogin"
                >
                  {{ selectedEvent.isEnded ? '종료된 이벤트입니다' : '출석체크하기' }}
                </button>
              </div>
            </div>

            <div v-if="selectedEvent.type === 'invite'" class="invite-event">
              <div class="special-banner">
                <img :src="selectedEvent.bannerImage" alt="친구초대 이벤트 배너" />
              </div>                
              <div class="invite-info">
                <div class="invite-step">
                  <div class="step-number">1</div>
                  <div class="step-content">
                    <h3>나만의 초대 코드 확인하기</h3>
                    <div class="invite-code-box">
                      <span class="invite-code">PLANOVA2025</span>
                      <button class="copy-button" :disabled="selectedEvent.isEnded">복사</button>
                    </div>
                  </div>
                </div>
                
                <div class="invite-step">
                  <div class="step-number">2</div>
                  <div class="step-content">
                    <h3>친구에게 초대 코드 공유하기</h3>
                    <div class="share-buttons">
                      <button class="share-button kakao" :disabled="selectedEvent.isEnded">카카오톡</button>
                      <button class="share-button link" :disabled="selectedEvent.isEnded">링크 복사</button>
                    </div>
                  </div>
                </div>
                
                <div class="invite-step">
                  <div class="step-number">3</div>
                  <div class="step-content">
                    <h3>친구가 가입 완료 시 보상 받기</h3>
                    <p>친구가 초대 코드를 입력하고 가입하면 <strong>친구와 함께 3천원 할인쿠폰</strong>을 드립니다!</p>
                  </div>
                </div>
                
                <div class="invite-button-container" style="margin-top: 20px;">
                  <button 
                    class="primary-button"
                    :disabled="selectedEvent.isEnded"
                    @click="navigateToLogin"
                  >
                    {{ selectedEvent.isEnded ? '종료된 이벤트입니다' : '친구 초대하기' }}
                  </button>
                </div>
              </div>
            </div>
            
            <div v-if="selectedEvent.type === 'special'" class="special-event">
              <div class="special-banner">
                <img :src="selectedEvent.bannerImage" alt="할인 이벤트 배너" />
              </div>
              
              <div class="special-info">
                <h3>{{ selectedEvent.title }}</h3>
                <p>{{ selectedEvent.description }}</p>
                
                <div class="special-details">
                  <div class="detail-item">
                    <div class="detail-label">할인 기간</div>
                    <div class="detail-value">{{ selectedEvent.period }}</div>
                  </div>
                  <div class="detail-item">
                    <div class="detail-label">할인율</div>
                    <div class="detail-value highlight">{{ selectedEvent.discountRate }}</div>
                  </div>
                  <div class="detail-item">
                    <div class="detail-label">적용 대상</div>
                    <div class="detail-value">{{ selectedEvent.target }}</div>
                  </div>
                </div>
                
                <button 
                  class="primary-button" 
                  :disabled="selectedEvent.isEnded"
                  @click="navigateToLogin"
                >
                  {{ selectedEvent.isEnded ? '종료된 이벤트입니다' : '혜택 받기' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import eventImage1 from '@/assets/images/event_invite.png';
import eventImage2 from '@/assets/images/event_attendance.png';
import eventImage3 from '@/assets/images/event_lucky_coupon.png';
import eventbannerImage1 from '@/assets/images/event_invite_banner.png';
import eventbannerImage2 from '@/assets/images/event_attendance_banner.png';
import eventbannerImage3 from '@/assets/images/event_lucky_coupon_banner.png';

const router = useRouter();

const activeTab = ref('ongoing');

const ongoingEvents = ref([
  {
    id: 1,
    type: 'attendance',
    title: '매일 매일 출석체크',
    period: '2025.05.20 - 2025.12.31',
    thumbnail: eventbannerImage2,
    badge: 'HOT',
    isEnded: false,
    bannerImage: eventImage2,
  },
  {
    id: 2,
    type: 'invite',
    title: '친구 초대 이벤트',
    period: '2025.05.20 - 2025.06.30',
    thumbnail: eventbannerImage1,
    badge: 'NEW',
    isEnded: false,
    bannerImage: eventImage1,
  },
  {
    id: 3,
    type: 'special',
    title: '신규가입 특별 혜택',
    period: '2025.03.01 - 2025.06.30',
    thumbnail: eventbannerImage3,
    badge: null,
    isEnded: false,
    description: '신규 가입하시는 모든 분들께 특별 혜택을 드립니다.',
    bannerImage: eventImage3,
    discountRate: '프리미엄 이용권 3일 무료 체험',
    target: '신규 가입 회원'
  }
]);

const endedEvents = ref([
  {
    id: 101,
    type: 'attendance',
    title: '신년맞이 출석체크 이벤트',
    period: '2025.01.01 - 2025.02.29',
    thumbnail: 'eventImage1',
    isEnded: true
  },
  {
    id: 102,
    type: 'discount',
    title: '설날 특별 할인 이벤트',
    period: '2025.02.01 - 2025.02.15',
    thumbnail: 'eventImage1',
    isEnded: true,
    description: '설날을 맞아 모든 서비스 특별 할인 혜택을 드렸습니다.',
    bannerImage: 'eventImage1',
    discountRate: '20%',
    target: '모든 회원'
  },
  {
    id: 103,
    type: 'invite',
    title: '2025 친구초대 이벤트',
    period: '2025.01.15 - 2025.02.28',
    thumbnail: 'eventImage1',
    isEnded: true
  }
]);

const selectedEvent = ref(null);

const viewEventDetail = (event) => {
  selectedEvent.value = event;
  document.body.style.overflow = 'hidden';
};

const closeEventDetail = () => {
  selectedEvent.value = null;
  document.body.style.overflow = '';
};

const navigateToLogin = () => {
  router.push({ 
    path: '/auth/login', 
    query: { redirect: router.currentRoute.value.fullPath } 
  });
};

onMounted(() => {
});
</script>

<style scoped>
.event-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Noto Sans KR', sans-serif;
}

.tab-container {
  display: flex;
  border-bottom: 2px solid #ddd;
  margin-bottom: 30px;
}

.tab-button {
  padding: 12px 25px;
  border: none;
  background: none;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  position: relative;
}

.tab-button.active {
  color: #ff6b00;
}

.tab-button.active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: #ff6b00;
}

.tab-content {
  animation: fadeIn 0.3s ease-in-out;
}

.event-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 25px;
}

.event-card {
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
  background-color: white;
}

.event-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.15);
}

.event-thumbnail {
  position: relative;
  height: 180px;
  overflow: hidden;
}

.event-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center 30%;
  transition: transform 0.3s;
}

.event-card:hover .event-thumbnail img {
  transform: scale(1.05);
}

.event-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  background-color: #ff6b00;
  color: white;
  padding: 5px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: bold;
}

.event-ended-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
}

.event-info {
  padding: 15px;
}

.event-card-title {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 8px;
  line-height: 1.4;
  color: #333;
}

.event-card-period {
  font-size: 14px;
  color: #666;
}

.event-card.ended {
  opacity: 0.8;
}

.event-modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.event-modal {
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  background-color: white;
  border-radius: 12px;
  position: relative;
  overflow-y: auto;
}

.modal-close-btn {
  position: absolute;
  top: 15px;
  right: 15px;
  width: 30px;
  height: 30px;
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  z-index: 10;
}

.modal-content {
  padding: 30px;
}

.modal-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 10px;
  color: #333;
}

.modal-period {
  color: #666;
  margin-bottom: 25px;
  font-size: 15px;
}

.event-detail-content {
  margin-top: 20px;
}

.special-banner {
  margin-bottom: 20px;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

.special-banner img {
  max-width: 100%;
  width: auto;
  height: auto;
  display: block;
  object-fit: cover;
}

.special-info, .invite-info {
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 8px;
  margin-bottom: 0;
}

.calendar-container {
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 20px;
}

.calendar-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  background-color: #f5f5f5;
}

.weekday {
  padding: 10px;
  text-align: center;
  font-weight: 500;
}

.calendar-body {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
}

.calendar-date {
  height: 50px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  border: 1px solid #eee;
}

.calendar-date.disabled {
  color: #ccc;
}

.calendar-date.today {
  background-color: #fff8f3;
}

.calendar-date.checked {
  background-color: #ffebe0;
}

.date-number {
  font-size: 14px;
}

.check-mark {
  color: #ff6b00;
  font-size: 18px;
  margin-top: 3px;
}

.reward-info {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.reward-info h3 {
  font-size: 18px;
  margin-bottom: 10px;
}

.reward-info ul {
  padding-left: 20px;
}

.reward-info li {
  margin-bottom: 5px;
}

.invite-info {
  margin-bottom: 30px;
}

.invite-step {
  display: flex;
  margin-bottom: 20px;
}

.step-number {
  width: 30px;
  height: 30px;
  background-color: #ff6b00;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-right: 15px;
}

.step-content {
  flex: 1;
}

.step-content h3 {
  font-size: 18px;
  margin-bottom: 10px;
}

.invite-code-box {
  display: flex;
  align-items: center;
  margin-top: 10px;
}

.invite-code {
  background-color: #f5f5f5;
  padding: 10px 15px;
  border-radius: 4px;
  font-weight: bold;
  letter-spacing: 1px;
  margin-right: 10px;
}

.copy-button, .share-button {
  background-color: #ff6b00;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 15px;
  cursor: pointer;
  font-size: 14px;
}

.copy-button:disabled, .share-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.share-buttons {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.share-button.kakao {
  background-color: #FEE500;
  color: #000;
}

.share-button.kakao:disabled {
  background-color: #f8f8f8;
  color: #bbb;
}

.special-details {
  margin-bottom: 20px;
}

.detail-item {
  display: flex;
  padding: 10px 0;
  border-bottom: 1px solid #eee;
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-label {
  width: 120px;
  font-weight: 500;
  color: #666;
}

.detail-value {
  flex: 1;
}

.detail-value.highlight {
  color: #ff6b00;
  font-weight: bold;
}

.primary-button {
  display: block;
  width: 100%;
  padding: 15px;
  background-color: #ff6b00;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  margin-top: 20px;
}

.primary-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@media (max-width: 768px) {
  .event-grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 15px;
  }
  
  .event-thumbnail {
    height: 160px;
  }
  
  .modal-content {
    padding: 20px;
  }
}

@media (max-width: 576px) {
  .event-grid {
    grid-template-columns: 1fr;
  }
  
  .event-thumbnail {
    height: 200px;
  }
  
  .tab-button {
    padding: 10px 15px;
    font-size: 14px;
  }
}
</style>