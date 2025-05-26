<!-- SubscriptionPage.vue -->
<script setup>
import { ref, computed, onMounted } from 'vue';
import * as PortOne from 'portone';

// 구독 플랜 정의
const plans = [
  {
    id: '100',
    name: '플래닛',
    price: 1900,
    planetCount: 100,
    bonusCount: 10,
    isPopular: false
  },
  {
    id: '300',
    name: '플래닛',
    price: 4900,
    planetCount: 300,
    bonusCount: 100,
    isPopular: true
  },
  {
    id: '500',
    name: '플래닛',
    price: 8900,
    planetCount: 500,
    bonusCount: 200,
    isPopular: false
  },
  {
    id: '1500',
    name: '플래닛',
    price: 99900,
    planetCount: 1500,
    bonusCount: 500,
    isPopular: false
  },
  {
    id: '2000',
    name: '플래닛',
    price: 199900,
    planetCount: 2000,
    bonusCount: 1000,
    isPopular: false
  },
  {
    id: '5000',
    name: '플래닛',
    price: 399900,
    planetCount: 5000,
    bonusCount: 2500,
    isPopular: false
  }
];

// 이미지 import
import PlanetIcon from '@/assets/images/planet.png';
import PurchasePassIcon from '@/assets/images/purchase-pass.png';

// 포트원 결제 모듈 초기화
onMounted(async () => {
  try {
    await PortOne.loadUI({
      storeId: import.meta.env.VUE_APP_PORTONE_STORE_ID
    });
    console.log('포트원 초기화 완료');
  } catch (error) {
    console.error('포트원 초기화 실패:', error);
  }
});

/**
 * 결제 처리 함수
 * @param {string} planId - 선택된 플랜 ID
 */
const handlePurchase = async (planId) => {
  console.log(`${planId} 플랜 구매 시작`);
  
  // 선택된 플랜 찾기
  const selectedPlan = plans.find(plan => plan.id === planId);
  if (!selectedPlan) {
    alert('선택된 플랜을 찾을 수 없습니다.');
    return;
  }

  // 사용자 정보 가져오기 (localStorage에서)
  const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
  
  // 결제 고유 ID 생성
  const paymentId = `payment_${Date.now()}_${Math.random().toString(36).substring(7)}`;
  
  try {
    const response = await PortOne.requestPayment({
      // 포트원 설정
      storeId: import.meta.env.VUE_APP_PORTONE_STORE_ID,
      channelKey: import.meta.env.VUE_APP_PORTONE_CHANNEL_KEY,
      paymentId: paymentId,
      
      // 결제 정보
      orderName: `PLANOVA ${selectedPlan.planetCount}${selectedPlan.name}`,
      totalAmount: selectedPlan.price,
      currency: 'KRW',
      
      // 고객 정보
      customer: {
        customerId: userInfo.id || 'guest',
        email: userInfo.email || '',
        fullName: userInfo.properties?.nickname || userInfo.properties?.profile_nickname || '고객'
      },
      
      // 콜백 URL
      returnUrl: `${window.location.origin}/payment/callback`,
      
      // 추가 정보
      productCount: 1,
      productType: 'subscription',
      locale: 'ko-KR',
      
      // 플랜 정보를 customData에 포함
      customData: JSON.stringify({
        planId: selectedPlan.id,
        planName: selectedPlan.name,
        planetCount: selectedPlan.planetCount,
        duration: selectedPlan.days
      })
    });

    console.log('결제 응답:', response);

    if (response.code === 'SUCCESS') {
      // 결제 성공시 결제 검증 요청
      await verifyPayment(response);
    } else {
      // 결제 실패 또는 취소
      console.error('결제 실패:', response.message);
      alert(`결제에 실패했습니다: ${response.message}`);
    }
  } catch (error) {
    console.error('결제 처리 중 오류:', error);
    alert('결제 처리 중 오류가 발생했습니다.');
  }
};

/**
 * 결제 검증 함수
 * @param {Object} paymentResponse - 결제 응답 객체
 */
const verifyPayment = async (paymentResponse) => {
  try {
    // 백엔드 서버에 결제 검증 요청
    const verificationResponse = await fetch('/api/payments/verify', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        paymentId: paymentResponse.paymentId,
        txId: paymentResponse.txId,
        amount: paymentResponse.totalAmount
      })
    });

    if (verificationResponse.ok) {
      const result = await verificationResponse.json();
      console.log('결제 검증 완료:', result);
      
      // 결제 성공 처리
      alert('결제가 완료되었습니다!');
      
      // 구독 정보 저장
      saveSubscriptionInfo(paymentResponse);
      
      // 성공 페이지로 리다이렉트 (라우터 사용시 활성화)
      // router.push('/subscription/success');
    } else {
      throw new Error('결제 검증 실패');
    }
  } catch (error) {
    console.error('결제 검증 중 오류:', error);
    alert('결제 검증 중 오류가 발생했습니다. 고객센터에 문의해주세요.');
  }
};

/**
 * 구독 정보 저장 함수
 * @param {Object} paymentResponse - 결제 응답 객체
 */
const saveSubscriptionInfo = (paymentResponse) => {
  const customData = JSON.parse(paymentResponse.customData);
  
  const subscriptionInfo = {
    paymentId: paymentResponse.paymentId,
    planId: customData.planId,
    planName: customData.planName,
    planetCount: customData.planetCount,
    amount: paymentResponse.totalAmount,
    startDate: new Date(),
    expiryDate: new Date(Date.now() + (customData.duration * 24 * 60 * 60 * 1000))
  };
  
  localStorage.setItem('subscription', JSON.stringify(subscriptionInfo));
  console.log('구독 정보 저장 완료:', subscriptionInfo);
};
</script>

<template>
  <div class="subscription-page">
    <div class="plans-container">
      <!-- 플랜 카드 반복 -->
      <div 
        v-for="(plan, index) in plans" 
        :key="`${plan.id}-${plan.planetCount}`" 
        class="plan-card"
        :class="{ 'popular': plan.isPopular }"
      >
        <!-- 인기 뱃지 -->
        <div v-if="plan.isPopular" class="popular-badge">
          인기
        </div>
        
        <!-- 플랜 헤더 -->
        <div class="plan-header">
          <div class="planet-icon-wrapper">
            <img :src="PlanetIcon" alt="플래닛" class="planet-icon" />
          </div>
          <h3 class="plan-amount">
            {{ plan.planetCount }}<span class="plan-unit">{{ plan.name }}</span>
          </h3>
          <div class="plan-price"><span class="currency">&#8361;</span>{{ plan.price.toLocaleString() }}</div>
        </div>
        
        <!-- 보너스 섹션 -->
        <div class="bonus-section">
          <div class="bonus-tag">
            <span class="bonus-icon">🎁</span>
            <span>보너스 +{{ plan.bonusCount }}플래닛 추가 제공</span>
          </div>
        </div>
        
        <!-- 구매 버튼 -->
        <button 
          class="purchase-button"
          @click="handlePurchase(plan.id)"
        >
          구매하기
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 전체 페이지 스타일 */
.subscription-page {
  background: linear-gradient(135deg,#fffff0 100%);
  padding: 40px 20px 60px;
  font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
  color: #333;
}

/* 플랜 목록 레이아웃 */
.plans-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

/* 플랜 카드 기본 스타일 */
.plan-card {
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border: none;
  border-radius: 20px;
  overflow: hidden;
  position: relative;
  transition: all 0.3s ease;
  color: #333;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
}

.plan-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
}

/* 인기 플랜 강조 */
.plan-card.popular {
  border: 2px solid rgba(255, 149, 0, 0.4);
  background: #ffffff;
  box-shadow: 0 15px 40px rgba(255, 149, 0, 0.15);
  transform: none;
  z-index: 2;
}

.popular-badge {
  position: absolute;
  top: 0;
  right: 25px;
  padding: 7px 20px;
  background: linear-gradient(90deg, #FF9500, #FFCC00);
  color: #fff;
  font-size: 0.85rem;
  font-weight: 700;
  border-radius: 0 0 12px 12px;
  box-shadow: 0 4px 10px rgba(255, 149, 0, 0.3);
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* 플랜 헤더 */
.plan-header {
  text-align: center;
  padding: 30px 20px 25px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  background: linear-gradient(to bottom, rgba(255, 255, 255, 0) 0%, rgba(248, 250, 255, 0.8) 100%);
}

.planet-icon-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.planet-icon {
  width: 70px;
  height: 70px;
  filter: drop-shadow(0 6px 15px rgba(255, 149, 0, 0.25));
  transition: transform 0.3s ease;
}

.plan-card:hover .planet-icon {
  transform: scale(1.1) rotate(5deg);
}

.plan-amount {
  font-size: 2.6rem;
  font-weight: 800;
  color: #333;
  text-align: center;
  width: 100%;
  margin: 0 auto 6px;
  display: flex;
  justify-content: center;
  align-items: baseline;
  line-height: 1.1;
}

.plan-unit {
  font-size: 1.1rem;
  margin-left: 6px;
  margin-top: 10px;
  font-weight: 500;
  color: #555;
  align-self: center;
}

.plan-price {
  font-size: 1.8rem;
  font-weight: 700;
  color: #FF9500;
  text-align: center;
  width: 100%;
  margin: 8px auto 0;
}

.currency {
  margin-right: 2px;
}

/* 보너스 영역 */
.bonus-section {
  padding: 25px 20px;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  gap: 25px;
  background: #ffffff;
}

.bonus-tag {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  padding: 12px 18px;
  border-radius: 50px;
  font-weight: 600;
  font-size: 1rem;
  color: #FF9500;
  background-color: rgba(255, 149, 0, 0.08);
  border: 1px dashed rgba(255, 149, 0, 0.3);
  transition: all 0.3s ease;
}

.plan-card:hover .bonus-tag {
  background-color: rgba(255, 149, 0, 0.12);
  transform: translateY(-2px);
}

.bonus-icon {
  font-size: 1.2rem;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

.total-section {
  text-align: center;
  padding: 20px;
  border-radius: 16px;
  background: linear-gradient(145deg, #f8faff 0%, #f1f5ff 100%);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.03);
  margin-top: 10px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.plan-card:hover .total-section {
  transform: translateY(-4px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.06);
}

.total-amount {
  font-size: 2.4rem;
  font-weight: 800;
  margin-bottom: 5px;
  color: #FF9500;
}

.total-label {
  font-size: 0.95rem;
  color: #777;
  font-weight: 500;
}

/* 구매 버튼 */
.purchase-button {
  border: none;
  padding: 18px;
  font-size: 1.05rem;
  font-weight: 700;
  cursor: pointer;
  background: linear-gradient(90deg, #FF9500, #FFCC00);
  color: white;
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  position: relative;
  overflow: hidden;
  z-index: 1;
}

.purchase-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, #FFCC00, #FF9500);
  transition: opacity 0.3s ease;
  opacity: 0;
  z-index: -1;
}

.purchase-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(255, 149, 0, 0.2);
}

.purchase-button:hover::before {
  opacity: 1;
}

/* 인기 플랜 추가 스타일 */
.plan-card.popular:hover {
  transform: translateY(-10px);
  box-shadow: 0 20px 40px rgba(255, 149, 0, 0.15);
}

.plan-card.popular .purchase-button {
  background: linear-gradient(90deg, #FF7F00, #FF9500);
  box-shadow: 0 6px 15px rgba(255, 127, 0, 0.2);
}

.plan-card.popular .purchase-button::before {
  background: linear-gradient(90deg, #FF9500, #FF7F00);
}

.plan-card.popular .purchase-button:hover {
  box-shadow: 0 10px 25px rgba(255, 127, 0, 0.3);
}

/* 반응형 디자인 */
@media (max-width: 992px) {
  .plans-container {
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
  }

  .plan-amount { font-size: 2rem; }
  .plan-price { font-size: 1.5rem; }
  .total-amount { font-size: 1.8rem; }
}

@media (max-width: 768px) {
  .plans-container {
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
  }
}

@media (max-width: 576px) {
  .plans-container {
    grid-template-columns: 1fr;
    max-width: 350px;
    margin: 0 auto;
  }

  .plan-card.popular {
    transform: none;
  }
}
</style>