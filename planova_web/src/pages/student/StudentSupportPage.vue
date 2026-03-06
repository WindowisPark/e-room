<script setup>
import { ref, computed } from 'vue';
import PlannySvg from '@/components/PlannySvg.vue';

const allFaqItems = ref([
  // 시작하기
  { id: 1, category: 'start', question: '회원가입은 어떻게 하나요?', answer: '플래노바는 카카오 간편 로그인으로 가입할 수 있습니다. 로그인 페이지에서 "카카오로 시작하기" 버튼을 클릭하면 30초 이내로 가입이 완료됩니다.', isOpen: false },
  { id: 2, category: 'start', question: '카카오 로그인이 안 돼요. 어떻게 해야 하나요?', answer: '카카오 계정 로그인 상태를 확인하고 브라우저 캐시를 초기화해 보세요. 문제가 지속되면 support@planova.kr로 문의해 주세요.', isOpen: false },
  { id: 3, category: 'start', question: '계정을 삭제하고 싶어요.', answer: '마이페이지 > 계정 설정 > 회원 탈퇴에서 진행할 수 있습니다. 탈퇴 시 모든 데이터가 삭제되니 신중하게 결정해 주세요.', isOpen: false },

  // 캘린더
  { id: 4, category: 'calendar', question: '일정을 추가하려면 어떻게 하나요?', answer: '캘린더 페이지에서 원하는 날짜를 클릭하거나 "+ 일정 추가" 버튼을 누르면 일정을 등록할 수 있습니다.', isOpen: false },
  { id: 5, category: 'calendar', question: '등록한 일정을 수정하거나 삭제할 수 있나요?', answer: '네, 캘린더에서 일정을 클릭하면 수정 및 삭제 옵션이 나타납니다.', isOpen: false },
  { id: 6, category: 'calendar', question: '반복 일정 설정이 가능한가요?', answer: '현재 버전에서는 반복 일정 기능을 준비 중입니다. 업데이트 공지를 기다려 주세요.', isOpen: false },

  // 이력서/포트폴리오
  { id: 7, category: 'resume', question: '이력서는 어떻게 작성하나요?', answer: '이력서 페이지에서 항목별로 내용을 입력하면 됩니다. AI가 문구 개선을 함께 도와드립니다.', isOpen: false },
  { id: 8, category: 'resume', question: '작성한 이력서를 PDF로 다운로드할 수 있나요?', answer: 'PDF 내보내기 기능을 지원합니다. 이력서 페이지에서 "PDF 저장" 버튼을 클릭하세요.', isOpen: false },
  { id: 9, category: 'resume', question: '포트폴리오 파일을 업로드할 수 있나요?', answer: '네, 이력서 페이지에서 파일을 첨부하거나 링크를 등록할 수 있습니다.', isOpen: false },

  // 기업조사
  { id: 10, category: 'jobs', question: '기업을 검색하는 방법은 무엇인가요?', answer: '기업 조사 페이지에서 기업명 또는 채용 공고 URL을 입력하면 AI가 자동으로 분석해드립니다.', isOpen: false },
  { id: 11, category: 'jobs', question: '채용 공고를 자동으로 불러올 수 있나요?', answer: '채용 공고 URL을 붙여 넣으면 AI가 자동으로 내용을 스크래핑하고 핵심 정보를 요약해드립니다.', isOpen: false },
  { id: 12, category: 'jobs', question: '면접 예상 질문도 제공되나요?', answer: '네, 기업 분석 후 해당 포지션에 맞는 면접 예상 질문을 AI가 제안해드립니다.', isOpen: false },

  // 자소서
  { id: 13, category: 'coverletter', question: 'AI 자소서 초안은 어떻게 생성하나요?', answer: '자소서 페이지에서 지원 기업, 직무, 자신의 경험을 입력하면 AI가 초안을 자동으로 생성해드립니다.', isOpen: false },
  { id: 14, category: 'coverletter', question: '자소서 항목을 개별적으로 편집할 수 있나요?', answer: '네, 생성된 초안에서 각 항목을 클릭하여 자유롭게 편집할 수 있습니다.', isOpen: false },
  { id: 15, category: 'coverletter', question: '여러 회사의 자소서를 관리할 수 있나요?', answer: '자소서 페이지에서 회사별로 별도 문서를 만들어 관리할 수 있습니다.', isOpen: false },

  // 기타
  { id: 16, category: 'etc', question: '모바일에서도 사용할 수 있나요?', answer: '네, 플래노바는 모바일 웹 브라우저에서도 이용하실 수 있습니다.', isOpen: false },
  { id: 17, category: 'etc', question: '오류나 버그를 발견했어요. 어디에 신고해야 하나요?', answer: 'support@planova.kr로 오류 내용과 스크린샷을 보내주시면 신속하게 확인 후 개선하겠습니다.', isOpen: false },
]);

const noticeItems = ref([
  {
    id: 1,
    title: '[안내] 플래노바 서비스 오픈 안내',
    date: '2026.03.05',
    content: '안녕하세요, 플래노바입니다. 학창시절부터 취업까지 함께하는 AI 플랜 서비스 플래노바가 정식 오픈했습니다. 이력서, 자소서, 기업 조사, 캘린더 등 모든 기능을 무료로 이용하실 수 있습니다.',
    isOpen: false
  },
  {
    id: 2,
    title: '[업데이트] AI 자소서 초안 생성 기능 출시',
    date: '2026.03.05',
    content: 'AI가 자동으로 자소서 초안을 생성해주는 기능이 출시되었습니다. 지원 기업과 직무, 경험을 입력하면 바로 초안을 받아볼 수 있습니다.',
    isOpen: false
  },
  {
    id: 3,
    title: '[안내] 카카오 간편 로그인 지원',
    date: '2026.03.05',
    content: '카카오 계정으로 간편하게 플래노바에 가입하고 로그인하실 수 있습니다. 별도의 회원가입 절차 없이 30초 이내로 시작하세요.',
    isOpen: false
  },
]);

const guideItems = ref([
  { id: 1, title: '플래노바 시작하기 — 카카오 로그인', content: '카카오 계정으로 30초 만에 플래노바를 시작하세요. 로그인 페이지에서 "카카오로 시작하기" 버튼을 클릭하면 바로 이용할 수 있습니다.', isOpen: false },
  { id: 2, title: '이력서 & 포트폴리오 작성하기', content: '이력서 페이지에서 항목별로 내용을 입력하면 AI가 문구 개선을 도와드립니다. 완성 후 PDF로 바로 다운로드 가능합니다.', isOpen: false },
  { id: 3, title: 'AI 자소서 초안 생성하기', content: '자소서 페이지에서 지원 기업, 직무, 경험을 입력하면 AI가 초안을 자동 생성합니다. 항목별로 자유롭게 편집할 수 있습니다.', isOpen: false },
  { id: 4, title: '기업 조사 & 채용 공고 분석', content: '채용 공고 URL을 붙여 넣으면 AI가 핵심 정보를 요약하고 면접 예상 질문까지 제공합니다.', isOpen: false },
]);

const categories = ref([
  { id: 'start', name: '시작하기', icon: 'fa-solid fa-rocket', color: '#F76707' },
  { id: 'calendar', name: '캘린더', icon: 'fa-solid fa-calendar-days', color: '#F76707' },
  { id: 'resume', name: '이력서', icon: 'fa-solid fa-file-lines', color: '#4A90E2' },
  { id: 'jobs', name: '기업조사', icon: 'fa-solid fa-building', color: '#7C3AED' },
  { id: 'coverletter', name: '자소서', icon: 'fa-solid fa-pen-to-square', color: '#16A34A' },
  { id: 'etc', name: '기타', icon: 'fa-solid fa-circle-question', color: '#888' },
]);

const searchQuery = ref('');
const isSearching = computed(() => searchQuery.value.trim() !== '');
const activeCategory = ref('자주 묻는 질문');
const activeFaqCategory = ref('start');

const filteredFaqItems = computed(() => {
  if (isSearching.value) {
    const query = searchQuery.value.toLowerCase();
    return allFaqItems.value.filter(item =>
      item.question.toLowerCase().includes(query) ||
      item.answer.toLowerCase().includes(query)
    );
  }
  return allFaqItems.value.filter(item => item.category === activeFaqCategory.value);
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

const clearSearch = () => { searchQuery.value = ''; };

const toggleFaq = (id) => {
  allFaqItems.value = allFaqItems.value.map(item =>
    item.id === id ? { ...item, isOpen: !item.isOpen } : { ...item, isOpen: false }
  );
};

const toggleNotice = (id) => {
  noticeItems.value = noticeItems.value.map(item =>
    item.id === id ? { ...item, isOpen: !item.isOpen } : { ...item, isOpen: false }
  );
};

const toggleGuide = (id) => {
  guideItems.value = guideItems.value.map(item =>
    item.id === id ? { ...item, isOpen: !item.isOpen } : { ...item, isOpen: false }
  );
};

const changeTab = (tab) => {
  activeCategory.value = tab;
  clearSearch();
};

const changeFaqCategory = (categoryId) => {
  activeFaqCategory.value = categoryId;
  clearSearch();
};

const getCategoryColor = (categoryId) =>
  categories.value.find(c => c.id === categoryId)?.color || '#F76707';

const openContact = () => {
  window.open('mailto:support@planova.kr?subject=플래노바 문의');
};
</script>

<template>
  <!-- 페이지 헤더 -->
  <div class="support-hero">
    <PlannySvg :size="88" class="planny-hero" />
    <div class="support-hero-text">
      <h2 class="support-hero-title">무엇을 도와드릴까요?</h2>
      <p class="support-hero-sub">자주 묻는 질문이나 공지사항을 검색해보세요</p>
    </div>
  </div>

  <div class="faq-section">
    <!-- 검색창 -->
    <div class="search-container">
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input
          type="text"
          placeholder="궁금한 질문을 검색해보세요."
          class="search-input"
          v-model="searchQuery"
        />
      </div>
    </div>

    <!-- 탭 -->
    <div class="tab-container">
      <div class="tabs">
        <button class="tab" :class="{ active: activeCategory === 'PLANOVA 가이드' }" @click="changeTab('PLANOVA 가이드')">
          플래노바 가이드
        </button>
        <button class="tab" :class="{ active: activeCategory === '자주 묻는 질문' }" @click="changeTab('자주 묻는 질문')">
          자주 묻는 질문
        </button>
        <button class="tab" :class="{ active: activeCategory === '공지사항' }" @click="changeTab('공지사항')">
          공지사항
        </button>
      </div>
    </div>

    <!-- FAQ 섹션 -->
    <div v-if="activeCategory === '자주 묻는 질문'">
      <div v-if="!isSearching" class="category-cards">
        <button
          v-for="category in categories"
          :key="category.id"
          class="cat-card"
          :class="{ active: category.id === activeFaqCategory }"
          :style="category.id === activeFaqCategory
            ? { background: category.color, borderColor: category.color }
            : { borderColor: '#e0e0e0' }"
          @click="changeFaqCategory(category.id)"
        >
          <i :class="category.icon" :style="{ color: category.id === activeFaqCategory ? 'white' : category.color }"></i>
          <span :style="{ color: category.id === activeFaqCategory ? 'white' : '#555' }">{{ category.name }}</span>
        </button>
      </div>

      <div class="faq-container">
        <div
          v-for="item in filteredFaqItems"
          :key="item.id"
          class="faq-item"
          :class="{ active: item.isOpen }"
        >
          <div class="faq-question" @click="toggleFaq(item.id)">
            <span class="cat-dot" :style="{ background: getCategoryColor(item.category) }"></span>
            <span class="question-icon" :style="{ color: getCategoryColor(item.category) }">Q</span>
            <span class="question-text">{{ item.question }}</span>
            <span class="arrow-icon">{{ item.isOpen ? '▲' : '▼' }}</span>
          </div>
          <div class="faq-answer" v-if="item.isOpen">
            <p>{{ item.answer }}</p>
          </div>
        </div>

        <div v-if="filteredFaqItems.length === 0" class="empty-state">
          <PlannySvg :size="72" class="planny-empty" />
          <p class="empty-title">찾으시는 내용이 없나요?</p>
          <p class="empty-sub">직접 문의해 주시면 빠르게 도와드릴게요.</p>
          <button class="empty-contact-btn" @click="openContact">이메일로 문의하기</button>
        </div>
      </div>
    </div>

    <!-- 공지사항 섹션 -->
    <div v-if="activeCategory === '공지사항'">
      <div class="notice-container">
        <div
          v-for="item in filteredNoticeItems"
          :key="item.id"
          class="notice-item"
          :class="{ active: item.isOpen }"
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
        <div v-if="filteredNoticeItems.length === 0" class="empty-state">
          <PlannySvg :size="72" class="planny-empty" />
          <p class="empty-title">검색 결과가 없습니다.</p>
          <p class="empty-sub">다른 검색어로 시도해보세요.</p>
        </div>
      </div>
    </div>

    <!-- 가이드 섹션 -->
    <div v-if="activeCategory === 'PLANOVA 가이드'">
      <div class="guide-container">
        <div
          v-for="item in filteredGuideItems"
          :key="item.id"
          class="guide-item"
          :class="{ active: item.isOpen }"
        >
          <div class="guide-header" @click="toggleGuide(item.id)">
            <span class="guide-title">{{ item.title }}</span>
            <span class="arrow-icon">{{ item.isOpen ? '▲' : '▼' }}</span>
          </div>
          <div class="guide-content" v-if="item.isOpen">
            <p>{{ item.content }}</p>
          </div>
        </div>
        <div v-if="filteredGuideItems.length === 0" class="empty-state">
          <PlannySvg :size="72" class="planny-empty" />
          <p class="empty-title">검색 결과가 없습니다.</p>
        </div>
      </div>
    </div>
  </div>

  <!-- 하단 문의 섹션 -->
  <div class="contact-section">
    <div class="contact-container">
      <div class="contact-text">
        <h2 class="contact-title">더 궁금한 것이 있으신가요?</h2>
        <p class="contact-desc">플래노바 팀이 이메일로 빠르게 도와드립니다.</p>
        <button class="contact-button" @click="openContact">이메일로 문의하기</button>
      </div>
      <div class="contact-email-info">
        <p class="email-label">이메일 문의</p>
        <p class="email-address">support@planova.kr</p>
        <p class="email-note">평일 오전 10시 ~ 오후 6시 순차 답변</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ── 서포트 히어로 ── */
.support-hero {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 36px 0 28px;
  max-width: 800px;
  margin: 0 auto;
}

.planny-hero {
  flex-shrink: 0;
  filter: drop-shadow(0 6px 16px rgba(247, 103, 7, 0.25));
}

.support-hero-title {
  font-size: 1.8rem;
  font-weight: 900;
  color: #1a1a1a;
  margin: 0 0 6px;
}

.support-hero-sub {
  font-size: 0.95rem;
  color: #888;
  margin: 0;
}

/* ── 검색창 ── */
.search-container {
  width: 100%;
  display: flex;
  justify-content: center;
  margin: 0 0 30px;
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
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.search-input:focus {
  border-color: #F76707;
  background: white;
}

/* ── 탭 ── */
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
  color: #F76707;
  font-weight: bold;
}

.tab.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: #F76707;
}

/* ── 카테고리 카드 ── */
.category-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 32px;
  justify-content: center;
}

.cat-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: 2px solid;
  border-radius: 50px;
  background: white;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.cat-card i {
  font-size: 14px;
}

.cat-card:hover:not(.active) {
  background: #fafafa;
  transform: translateY(-1px);
}

/* ── FAQ ── */
.faq-container,
.notice-container,
.guide-container {
  max-width: 800px;
  margin: 0 auto 50px;
}

.faq-item,
.notice-item,
.guide-item {
  border-bottom: 1px solid #eee;
  margin-bottom: 4px;
}

.faq-question,
.notice-header,
.guide-header {
  display: flex;
  align-items: center;
  padding: 20px 0;
  cursor: pointer;
  gap: 4px;
}

.cat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-right: 6px;
}

.question-icon {
  font-weight: bold;
  font-size: 17px;
  margin-right: 12px;
  flex-shrink: 0;
}

.question-text,
.notice-title,
.guide-title {
  flex: 1;
  font-size: 15px;
  color: #333;
}

.notice-title-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.notice-date {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.arrow-icon {
  font-size: 11px;
  color: #bbb;
  margin-left: 10px;
  flex-shrink: 0;
}

.faq-answer,
.notice-content,
.guide-content {
  padding: 0 0 20px 50px;
  color: #555;
  line-height: 1.7;
  font-size: 14px;
}

.notice-content,
.guide-content {
  padding: 0 0 20px 0;
}

.faq-item.active .question-text {
  font-weight: 600;
}

/* ── 빈 상태 ── */
.empty-state {
  text-align: center;
  padding: 48px 0 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.planny-empty {
  filter: drop-shadow(0 4px 12px rgba(247, 103, 7, 0.2));
  margin-bottom: 4px;
}

.empty-title {
  font-size: 1rem;
  font-weight: 700;
  color: #555;
  margin: 0;
}

.empty-sub {
  font-size: 0.88rem;
  color: #999;
  margin: 0;
}

.empty-contact-btn {
  margin-top: 8px;
  background: #F76707;
  color: white;
  border: none;
  border-radius: 50px;
  padding: 10px 24px;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.2s, transform 0.2s;
}

.empty-contact-btn:hover {
  background: #d95e06;
  transform: translateY(-1px);
}

/* ── 하단 문의 섹션 ── */
.contact-section {
  background-color: #FFF1E5;
  width: 100vw;
  position: relative;
  left: 50%;
  margin-left: -50vw;
  margin-right: -50vw;
}

.contact-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 72px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 40px;
}

.contact-title {
  font-size: 1.8rem;
  font-weight: 900;
  color: #F76707;
  line-height: 1.35;
  margin: 0 0 12px;
}

.contact-desc {
  font-size: 1rem;
  color: #666;
  margin: 0 0 28px;
}

.contact-button {
  background-color: #F76707;
  border: none;
  color: white;
  padding: 14px 32px;
  border-radius: 50px;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.2s;
  box-shadow: 0 4px 14px rgba(247,103,7,0.35);
}

.contact-button:hover {
  background-color: #d95e06;
  transform: translateY(-2px);
}

.contact-email-info {
  flex-shrink: 0;
}

.email-label {
  font-size: 13px;
  color: #999;
  margin: 0 0 6px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.email-address {
  font-size: 1.4rem;
  font-weight: 800;
  color: #F76707;
  margin: 0 0 8px;
}

.email-note {
  font-size: 13px;
  color: #888;
  margin: 0;
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .support-hero {
    flex-direction: column;
    text-align: center;
    padding: 24px 0 16px;
  }

  .tabs {
    overflow-x: auto;
    justify-content: flex-start;
    padding: 0 10px;
  }

  .tab {
    white-space: nowrap;
    flex-shrink: 0;
  }

  .category-cards {
    padding: 0 4px;
  }

  .contact-container {
    flex-direction: column;
    padding: 56px 20px;
    text-align: center;
  }

  .contact-email-info {
    text-align: center;
  }
}
</style>
