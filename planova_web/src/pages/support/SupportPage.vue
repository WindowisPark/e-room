<script setup>
import { ref, reactive, computed } from 'vue';

const allFaqItems = ref([
  {
    id: 1,
    category: 'tutor',
    question: 'PLANOVA AI 튜터는 무엇인가요?',
    answer: 'PLANOVA AI 튜터는 인공지능을 활용한 학습 도우미로, 개인 맞춤형 학습 계획 수립과 문제 해결에 도움을 드립니다.',
    isOpen: false
  },
  {
    id: 2,
    category: 'tutor',
    question: 'PLANOVA AI 튜터 멤버십은 어떤 혜택가 있나요?',
    answer: '멤버십에 가입하시면 무제한 문제 생성, PDF 요약본 생성, LLM 용량 제공 등 다양한 혜택을 누리실 수 있습니다.',
    isOpen: false
  },
  {
    id: 3,
    category: 'tutor',
    question: 'PLANOVA AI 튜터는 어떤 사람들에게 추천하나요?',
    answer: '학습에 어려움을 느끼는 학생, 개인 맞춤형 학습을 원하는 분, 효율적인 학습 방법을 찾고 계신 분들께 추천합니다.',
    isOpen: false
  },
  {
    id: 4,
    category: 'tutor',
    question: 'PLANOVA AI 튜터도 무료 체험을 할 수 있나요?',
    answer: '네, 신규 가입 시 3일간의 무료 체험 기간을 제공해 드립니다.',
    isOpen: false
  },
  
  // 결제/환불 카테고리
  {
    id: 5,
    category: 'payment',
    question: 'PLANOVA AI 튜터 멤버십 결제는 어떻게 하나요?',
    answer: '홈페이지에서 멤버십 플랜을 선택한 후, 다양한 결제 방법(신용카드, 계좌이체 등)으로 결제하실 수 있습니다.',
    isOpen: false
  },
  {
    id: 6,
    category: 'payment',
    question: 'PLANOVA AI 튜터 멤버십 결제 수단을 변경할 수 있나요?',
    answer: '네, 마이페이지 > 결제 관리에서 언제든지 결제 수단을 변경하실 수 있습니다.',
    isOpen: false
  },
  {
    id: 7,
    category: 'payment',
    question: 'PLANOVA AI 튜터 멤버십은 자동 결제(구독형) 방식인가요?',
    answer: '네, 편의를 위해 자동 결제 방식으로 운영되며, 마이페이지에서 언제든지 해지 가능합니다.',
    isOpen: false
  },
  {
    id: 8,
    category: 'payment',
    question: '멤버십 환불은 어떻게 신청하나요?',
    answer: '멤버십 환불은 마이페이지 > 결제 관리 > 환불 신청에서 신청하실 수 있습니다. 결제일로부터 7일 이내에는 전액 환불이 가능하며, 그 이후에는 남은 기간에 대한 일할 계산 금액이 환불됩니다.',
    isOpen: false
  },
  {
    id: 9,
    category: 'payment',
    question: '환불 처리 기간은 얼마나 걸리나요?',
    answer: '환불 신청 후 영업일 기준 3-5일 이내에 처리되며, 카드사 사정에 따라 실제 환불되는 시점은 달라질 수 있습니다.',
    isOpen: false
  },
  
  // 수업권 카테고리
  {
    id: 10,
    category: 'attendance',
    question: '수업권은 무엇인가요?',
    answer: '수업권은 PLANOVA 서비스에서 제공하는 온라인 강의를 수강할 수 있는 권한을 말합니다. 멤버십에 따라 제공되는 수업권의 수와 유효기간은 다를 수 있습니다.',
    isOpen: false
  },
  {
    id: 11,
    category: 'attendance',
    question: '수업권은 언제까지 사용할 수 있나요?',
    answer: '수업권은 구매일로부터 3개월간 유효하며, 기간 내에 사용하지 않을 경우 자동으로 소멸됩니다.',
    isOpen: false
  },
  {
    id: 12,
    category: 'attendance',
    question: '수업권을 다른 사람에게 양도할 수 있나요?',
    answer: '수업권은 구매자 본인만 사용할 수 있으며, 타인에게 양도하거나 판매할 수 없습니다.',
    isOpen: false
  },
  
  // 계정 카테고리
  {
    id: 13,
    category: 'cancel',
    question: '회원 탈퇴는 어떻게 하나요?',
    answer: '마이페이지 > 계정 설정 > 회원 탈퇴에서 진행하실 수 있습니다. 탈퇴 시 모든 데이터가 삭제되니 신중하게 결정해 주세요.',
    isOpen: false
  },
  {
    id: 14,
    category: 'cancel',
    question: '비밀번호를 잊어버렸어요. 어떻게 해야 하나요?',
    answer: '로그인 페이지에서 "비밀번호 찾기"를 클릭하여 가입 시 등록한 이메일로 비밀번호 재설정 링크를 받으실 수 있습니다.',
    isOpen: false
  },
  {
    id: 15,
    category: 'cancel',
    question: '개인정보는 어떻게 관리되나요?',
    answer: 'PLANOVA는 개인정보보호법을 준수하며, 수집된 개인정보는 서비스 제공 및 개선을 위해서만 사용됩니다. 자세한 내용은 개인정보처리방침을 참고해 주세요.',
    isOpen: false
  },
  
  // 기타 카테고리
  {
    id: 16,
    category: 'etc',
    question: '모바일에서도 서비스를 이용할 수 있나요?',
    answer: '네, PLANOVA는 모바일 웹과 앱을 통해 언제 어디서나 이용하실 수 있습니다.',
    isOpen: false
  },
  {
    id: 17,
    category: 'etc',
    question: '오류나 버그를 발견했어요. 어디에 신고해야 하나요?',
    answer: '고객센터 > 문의하기를 통해 신고해 주시면 신속하게 확인 후 개선하겠습니다.',
    isOpen: false
  }
]);

const noticeItems = ref([
  {
    id: 1,
    title: '[안내] PLANOVA 서비스 이용약관 개정 안내',
    date: '2025.04.01',
    content: '안녕하세요, PLANOVA입니다. 당사의 서비스 이용약관이 2025년 4월 15일부터 변경됩니다. 주요 변경사항은 개인정보 처리방침과 멤버십 갱신 정책입니다. 자세한 내용은 홈페이지에서 확인하실 수 있습니다.',
    isOpen: false
  },
  {
    id: 2,
    title: '[업데이트] PLANOVA AI 튜터 기능 업데이트 안내',
    date: '2025.03.15',
    content: 'PLANOVA AI 튜터의 기능이 업데이트되었습니다. 이번 업데이트에서는 더 정확한 학습 분석과 개인화된 학습 플랜 추천 기능이 개선되었습니다. 지금 바로 새로운 기능을 경험해보세요!',
    isOpen: false
  },
  {
    id: 3,
    title: '[공지] 설 연휴 고객센터 운영 안내',
    date: '2025.02.08',
    content: '설 연휴 기간(2월 10일 ~ 2월 13일) 동안 고객센터는 제한적으로 운영됩니다. 문의사항은 이메일로 남겨주시면 연휴 이후 순차적으로 답변 드리겠습니다. 즐거운 명절 보내세요!',
    isOpen: false
  },
  {
    id: 4,
    title: '[안내] 시스템 점검 안내',
    date: '2025.01.20',
    content: '서비스 안정화를 위한 시스템 점검이 2025년 1월 25일 오전 2시부터 5시까지 진행됩니다. 해당 시간 동안에는 서비스 이용이 제한될 수 있으니 양해 부탁드립니다.',
    isOpen: false
  }
]);

const guideItems = ref([
  {
    id: 1,
    title: 'PLANOVA AI 튜터 시작하기',
    content: 'PLANOVA AI 튜터를 처음 사용하시는 분들을 위한 기본 가이드입니다.',
    isOpen: false
  },
  {
    id: 2,
    title: '효과적인 학습 계획 세우기',
    content: 'AI 튜터를 활용하여 자신만의, 효과적인 학습 계획을 세우는 방법을 안내합니다.',
    isOpen: false
  },
  {
    id: 3,
    title: '문제 생성 기능 활용하기',
    content: '맞춤형 문제 생성 기능을 최대한 활용하여 학습 효과를 높이는 방법을 알아봅니다.',
    isOpen: false
  }
]);

const searchQuery = ref('');
const isSearching = computed(() => searchQuery.value.trim() !== '');

const activeCategory = ref('자주 묻는 질문');
const activeFaqCategory = ref('tutor');

const filteredFaqItems = computed(() => {
  let items = allFaqItems.value;
  
  if (isSearching.value) {
    const query = searchQuery.value.toLowerCase();
    return items.filter(item => 
      item.question.toLowerCase().includes(query) || 
      item.answer.toLowerCase().includes(query)
    );
  } 
  else {
    return items.filter(item => item.category === activeFaqCategory.value);
  }
});

const filteredNoticeItems = computed(() => {
  if (!isSearching.value) return noticeItems.value;
  
  const query = searchQuery.value.toLowerCase();
  return noticeItems.value.filter(item => 
    item.title.toLowerCase().includes(query) || 
    item.content.toLowerCase().includes(query)
  );
});

const filteredGuideItems = computed(() => {
  if (!isSearching.value) return guideItems.value;
  
  const query = searchQuery.value.toLowerCase();
  return guideItems.value.filter(item => 
    item.title.toLowerCase().includes(query) || 
    item.content.toLowerCase().includes(query)
  );
});

const performSearch = () => {
  
};

const toggleFaq = (id) => {
  const updatedItems = allFaqItems.value.map(item => {
    if (item.id === id) {
      return { ...item, isOpen: !item.isOpen };
    } else {
      return { ...item, isOpen: false };
    }
  });
  
  allFaqItems.value = updatedItems;
};

const toggleNotice = (id) => {
  const updatedItems = noticeItems.value.map(item => {
    if (item.id === id) {
      return { ...item, isOpen: !item.isOpen };
    } else {
      return { ...item, isOpen: false };
    }
  });
  
  noticeItems.value = updatedItems;
};

const toggleGuide = (id) => {
  const updatedItems = guideItems.value.map(item => {
    if (item.id === id) {
      return { ...item, isOpen: !item.isOpen };
    } else {
      return { ...item, isOpen: false };
    }
  });
  
  guideItems.value = updatedItems;
};

const changeTab = (tab) => {
  activeCategory.value = tab;
  clearSearch();
};

const changeFaqCategory = (categoryId) => {
  activeFaqCategory.value = categoryId;
  clearSearch();
};

const categories = ref([
  { id: 'payment', name: '결제/환불' },
  { id: 'attendance', name: '수업권' },
  { id: 'cancel', name: '계정' },
  { id: 'tutor', name: 'PLANOVA AI 튜터' },
  { id: 'etc', name: '기타' }
]);
</script>

<template>
  <div class="faq-section">
    <div class="search-container">
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input 
          type="text" 
          placeholder="궁금한 질문 검색해보세요." 
          class="search-input"
          v-model="searchQuery"
          @keyup.enter="performSearch"
        >

      </div>
    </div>
    
    <div class="tab-container">
      <div class="tabs">
        <button 
          class="tab" 
          :class="{ active: activeCategory === 'PLANOVA 가이드' }"
          @click="changeTab('PLANOVA 가이드')"
        >
          PLANOVA 가이드
        </button>
        <button 
          class="tab" 
          :class="{ active: activeCategory === '자주 묻는 질문' }"
          @click="changeTab('자주 묻는 질문')"
        >
          자주 묻는 질문
        </button>
        <button 
          class="tab" 
          :class="{ active: activeCategory === '공지사항' }"
          @click="changeTab('공지사항')"
        >
          공지사항
        </button>
      </div>
    </div>
    

    <div v-if="activeCategory === '자주 묻는 질문'">
      <div v-if="!isSearching" class="category-filter">
        <button 
          v-for="category in categories" 
          :key="category.id" 
          class="category-btn"
          :class="{ active: category.id === activeFaqCategory }"
          @click="changeFaqCategory(category.id)"
        >
          {{ category.name }}
        </button>
      </div>
      
      <div class="faq-container">
        <div 
          v-for="item in filteredFaqItems" 
          :key="item.id" 
          class="faq-item"
          :class="{ 'active': item.isOpen }"
        >
          <div class="faq-question" @click="toggleFaq(item.id)">
            <span class="question-icon">Q</span>
            <span class="question-text">{{ item.question }}</span>
            <span class="arrow-icon">{{ item.isOpen ? '▲' : '▼' }}</span>
          </div>
          <div class="faq-answer" v-if="item.isOpen">
            <p>{{ item.answer }}</p>
          </div>
        </div>
        
        <div v-if="filteredFaqItems.length === 0" class="empty-message">
          <p v-if="isSearching">검색 결과가 없습니다.</p>
          <p v-else>해당 카테고리에 등록된 FAQ가 없습니다.</p>
        </div>
      </div>
    </div>
    
    <div v-if="activeCategory === '공지사항'">
      <div class="notice-container">
        <div 
          v-for="item in filteredNoticeItems" 
          :key="item.id" 
          class="notice-item"
          :class="{ 'active': item.isOpen }"
        >
          <div class="notice-header" @click="toggleNotice(item.id)">
            <div class="notice-title-container">
              <span class="notice-title">{{ item.title }}</span>
              <span class="notice-date">{{ item.date }}</span>
            </div>
            <span class="arrow-icon">{{ item.isOpen ? '▲' : '▼' }}</span>
          </div>
          <div class="notice-content" v-if="item.isOpen">
            <p>{{ item.content }}</p>
          </div>
        </div>

        <div v-if="filteredNoticeItems.length === 0" class="empty-message">
          <p>검색 결과가 없습니다.</p>
        </div>
      </div>
    </div>
    
    <div v-if="activeCategory === 'PLANOVA 가이드'">
      <div class="guide-container">
        <div 
          v-for="item in filteredGuideItems" 
          :key="item.id" 
          class="guide-item"
          :class="{ 'active': item.isOpen }"
        >
          <div class="guide-header" @click="toggleGuide(item.id)">
            <span class="guide-title">{{ item.title }}</span>
            <span class="arrow-icon">{{ item.isOpen ? '▲' : '▼' }}</span>
          </div>
          <div class="guide-content" v-if="item.isOpen">
            <p>{{ item.content }}</p>
          </div>
        </div>
        
        <div v-if="filteredGuideItems.length === 0" class="empty-message">
          <p>검색 결과가 없습니다.</p>
        </div>
      </div>
    </div>
  </div>
  
  <div class="contact-section">
    <div class="contact-container">
      <div class="contact-text">
        <h2 class="title">더 궁금한 것이 있다면 PLANOVA<br>고객센터로 연락주세요.</h2>
        <button class="contact-button">PLANOVA팀에 문의하기</button>
      </div>
      
      <div class="contact-info">
        <p class="contact-type">대표전화</p>
        <p class="phone-number">02-1234-1234</p>
        
        <p class="hours-title">운영시간</p>
        <p class="hours">평일 오전 10:00 ~ 오후 6:00 KST</p>
        <p class="lunch-time">점심시간 : 오후 1:00 ~ 오후 2:00 KST</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-container {
  width: 100%;
  display: flex;
  justify-content: center;
  margin: 20px 0 30px;
}

.search-box {
  position: relative;
  width: 100%;
  max-width: 800px;
}

.search-icon {
  position: absolute;
  left: 15px;
  top: 50%;
  transform: translateY(-50%);
  color: #999;
}

.search-input {
  width: 100%;
  padding: 15px 15px 15px 45px;
  border: 1px solid #eee;
  border-radius: 25px;
  background-color: #f7f7f7;
  font-size: 16px;
  outline: none;
}

.tab-container {
  margin-bottom: 30px;
  border-bottom: 1px solid #eee;
}

.tabs {
  display: flex;
  justify-content: space-around;
  max-width: 800px;
  margin: 0 auto;
}

.tab {
  padding: 15px 20px;
  font-size: 16px;
  border: none;
  background: none;
  cursor: pointer;
  position: relative;
  color: #888;
}

.tab.active {
  color: #FF6B01;
  font-weight: bold;
}

.tab.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: #FF6B01;
}

.category-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 30px;
  justify-content: center;
}

.category-btn {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 20px;
  background-color: white;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.category-btn.active {
  background-color: #FF6B01;
  color: white;
  border-color: #FF6B01;
}

.category-btn:hover {
  background-color: #f5f5f5;
}

.category-btn.active:hover {
  background-color: #e35f00;
}

.faq-container, .notice-container, .guide-container {
  max-width: 800px;
  margin: 0 auto 50px;
}

.faq-item, .notice-item, .guide-item {
  border-bottom: 1px solid #eee;
  margin-bottom: 10px;
}

.faq-question, .notice-header, .guide-header {
  display: flex;
  align-items: center;
  padding: 20px 0;
  cursor: pointer;
}

.question-icon {
  color: #FF6B01;
  font-weight: bold;
  font-size: 18px;
  margin-right: 15px;
}

.question-text, .notice-title, .guide-title {
  flex: 1;
  font-size: 16px;
}

.notice-title-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.notice-date {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

.arrow-icon {
  font-size: 12px;
  color: #999;
  margin-left: 10px;
}

.faq-answer, .notice-content, .guide-content {
  padding: 0 0 20px 35px;
  color: #666;
  line-height: 1.6;
}

.notice-content, .guide-content {
  padding: 0 0 20px 0;
}

.faq-item.active .faq-question,
.notice-item.active .notice-header,
.guide-item.active .guide-header {
  color: #FF6B01;
  font-weight: bold;
}

.empty-message {
  text-align: center;
  padding: 30px 0;
  color: #999;
}

.contact-section {
  background-color: #FFF1E5;
  width: 100vw;
  margin: 0;
  padding: 0;
  position: relative;
  left: 50%;
  right: 50%;
  margin-left: -50vw;
  margin-right: -50vw;
  min-height: 300px;
}

.contact-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 80px 20px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.contact-text {
  flex: 1;
  padding-right: 40px;
  margin-top: 20px;
  margin-bottom: 20px;
}

.title {
  font-size: 28px;
  font-weight: bold;
  color: #FF6B01;
  line-height: 1.4;
  margin-bottom: 40px;
}

.contact-button {
  background-color: #FFE4D0;
  border: none;
  color: #FF6B01;
  padding: 15px 30px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.3s;
}

.contact-button:hover {
  background-color: #FFD6BA;
}

.contact-info {
  flex: 1;
  margin-top: 20px;
  margin-bottom: 20px;
}

.contact-type {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.phone-number {
  font-size: 28px;
  font-weight: bold;
  color: #FF6B01;
  margin-bottom: 40px;
}

.hours-title {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.hours {
  font-size: 16px;
  color: #333;
  margin-bottom: 5px;
}

.lunch-time {
  font-size: 16px;
  color: #333;
}

@media (max-width: 768px) {
  .tabs {
    overflow-x: auto;
    justify-content: flex-start;
    padding: 0 10px;
  }
  
  .tab {
    white-space: nowrap;
    flex-shrink: 0;
  }

  .category-filter {
    overflow-x: auto;
    justify-content: flex-start;
    padding: 0 10px;
  }
  
  .category-btn {
    white-space: nowrap;
    flex-shrink: 0;
  }
  
  .contact-container {
    flex-direction: column;
    padding: 60px 20px;
  }
  
  .contact-text {
    padding-right: 0;
    margin-bottom: 40px;
  }
}
</style>