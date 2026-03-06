<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';

// ── Hero 캐러셀 데이터 ──
const featureSteps = [
  {
    step: '01',
    faIcon: 'fa-solid fa-book-open',
    tag: '학생 · 수험생',
    title: 'AI 학습 플랜',
    desc: '나의 목표와 일정에 맞게\nAI가 최적의 학습 플랜을 설계해드려요.',
    bg: '#FFF8F0',
    accent: '#F76707',
    items: ['과목별 일정 자동 배분', '약점 집중 학습 추천', '24시간 AI 질문 응답']
  },
  {
    step: '02',
    faIcon: 'fa-solid fa-file-lines',
    tag: '취업 준비생',
    title: '이력서·포트폴리오',
    desc: 'AI가 함께 다듬어주는 나만의 이력서,\n첫인상부터 완벽하게 만들어보세요.',
    bg: '#F0F5FF',
    accent: '#3B82F6',
    items: ['AI 문구 개선 제안', '직무 맞춤 키워드 추출', '포트폴리오 구성 가이드']
  },
  {
    step: '03',
    faIcon: 'fa-solid fa-pen-to-square',
    tag: '취업 준비생',
    title: '자기소개서',
    desc: 'AI 초안으로 시작해서\n나다운 자소서로 완성하세요.',
    bg: '#F0FDF4',
    accent: '#10B981',
    items: ['AI 초안 자동 생성', '지원 기업별 맞춤 편집', '합격 자소서 패턴 분석']
  },
  {
    step: '04',
    faIcon: 'fa-solid fa-magnifying-glass',
    tag: '취업 준비생',
    title: '기업 조사',
    desc: '공고 분석부터 기업 정보까지\n한눈에 파악하고 준비하세요.',
    bg: '#FDF4FF',
    accent: '#A855F7',
    items: ['채용 공고 자동 스크래핑', '기업 문화·연봉 정보', '면접 예상 질문 제공']
  }
];

const activeTab = ref(0);
const setTab = (i) => { activeTab.value = i; };

// ── Stats ──
const stats = [
  { number: '100% 무료', label: '모든 기능 제공' },
  { number: 'AI 4종', label: '학습 + 취준 도구' },
  { number: '5분', label: '이내 시작 가능' },
  { number: '24/7', label: '언제든지 이용' },
];

// ── Bento 카드 ──
const bentoFeatures = [
  {
    id: 'study',
    icon: 'fa-solid fa-book-open',
    accent: '#F76707',
    tag: '학생 · 수험생',
    title: 'AI 학습 플랜',
    desc: 'PDF를 올리면 AI가 요약·문제·QA를 자동 생성합니다. 약점을 파악하고 최적의 학습 루트를 설계해드려요.',
    items: ['PDF 자동 요약', 'AI 문제 생성', '24시간 질의응답'],
    big: true,
    hasCta: true,
  },
  {
    id: 'resume',
    icon: 'fa-solid fa-id-card',
    accent: '#3B82F6',
    tag: '취업 준비생',
    title: '이력서',
    desc: 'AI가 함께 다듬는 나만의 이력서',
    items: [],
    big: false,
    hasCta: false,
  },
  {
    id: 'cover',
    icon: 'fa-solid fa-pen-to-square',
    accent: '#10B981',
    tag: '취업 준비생',
    title: '자기소개서',
    desc: 'AI 초안으로 빠르게 시작',
    items: [],
    big: false,
    hasCta: false,
  },
  {
    id: 'aitutor',
    icon: 'fa-solid fa-robot',
    accent: '#8B5CF6',
    tag: '학생',
    title: 'AI 튜터',
    desc: '모르는 개념을 AI에게 즉시 질문하세요. 언제든, 몇 번이든 무제한으로.',
    items: [],
    big: false,
    wide: true,
    hasCta: false,
  },
  {
    id: 'jobs',
    icon: 'fa-solid fa-building',
    accent: '#A855F7',
    tag: '취업 준비생',
    title: '기업 공고 조사',
    desc: '채용 공고를 자동 분석하고 면접 예상 질문까지 제공합니다.',
    items: [],
    big: false,
    wide: true,
    hasCta: false,
  },
];

// ── How It Works ──
const steps = [
  {
    num: '01',
    title: '회원가입 (30초)',
    desc: '카카오 간편 가입으로\n30초면 충분합니다.',
    primary: true,
  },
  {
    num: '02',
    title: '학습 또는 취준 선택',
    desc: 'PDF 학습, 이력서, 자소서,\n기업 조사 — 원하는 것부터.',
    primary: false,
  },
  {
    num: '03',
    title: 'AI와 함께 목표 달성',
    desc: '질문하고, 분석하고, 완성하세요.\nAI가 옆에서 함께합니다.',
    primary: false,
  },
];

// ── IntersectionObserver 스크롤 애니메이션 ──
let observer = null;

onMounted(() => {
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12 }
  );

  document.querySelectorAll('.fade-in-section').forEach((el) => {
    observer.observe(el);
  });
});

onBeforeUnmount(() => {
  if (observer) observer.disconnect();
});
</script>

<template>
  <div class="page-root">

    <!-- ① Hero -->
    <section class="hero">
      <div class="bg-blobs" aria-hidden="true">
        <div class="bg-blob b1"></div>
        <div class="bg-blob b2"></div>
        <div class="bg-blob b3"></div>
        <div class="bg-blob b4"></div>
      </div>

      <div class="hero-body">
        <!-- 좌: 텍스트 -->
        <div class="hero-text">
          <span class="hero-eyebrow">무료로 시작하는 AI 학습 + 취준 플랫폼</span>
          <h1 class="hero-title">
            당신의 모든 계획,<br>
            <em class="accent">플래노바</em>가<br>함께합니다
          </h1>
          <p class="hero-desc">
            PDF 요약, AI 질문, 이력서, 자소서, 기업 조사<br>
            지금 바로, 무료로.
          </p>
          <div class="hero-actions">
            <router-link to="/auth/login" class="btn-primary">지금 무료로 시작하기 →</router-link>
            <a href="#bento" class="btn-ghost">둘러보기</a>
          </div>
        </div>

        <!-- 우: 탭 전환 패널 (데스크톱) -->
        <div class="feature-tabs-panel">
          <div class="ftab-row">
            <button
              v-for="(step, i) in featureSteps"
              :key="i"
              :class="['ftab', { active: activeTab === i }]"
              @click="setTab(i)"
            >
              <i :class="step.faIcon"></i>
              {{ step.title }}
            </button>
          </div>

          <Transition name="fp-fade" mode="out-in">
            <div :key="activeTab" class="feature-panel">
              <div class="fp-icon-wrap">
                <i :class="featureSteps[activeTab].faIcon"></i>
              </div>
              <h3 class="fp-title">{{ featureSteps[activeTab].title }}</h3>
              <p class="fp-desc">{{ featureSteps[activeTab].desc }}</p>
              <ul class="fp-items">
                <li v-for="item in featureSteps[activeTab].items" :key="item">
                  <i class="fa-solid fa-check"></i> {{ item }}
                </li>
              </ul>
            </div>
          </Transition>
        </div>

        <!-- 모바일 필 -->
        <div class="mobile-feature-pills">
          <span v-for="step in featureSteps" :key="step.step" class="mfp-pill">
            <i :class="step.faIcon"></i> {{ step.title }}
          </span>
        </div>
      </div>
    </section>

    <!-- ② Stats Bar -->
    <section class="stats-bar fade-in-section">
      <div class="stats-container">
        <div v-for="stat in stats" :key="stat.number" class="stat-item">
          <div class="stat-number">{{ stat.number }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>
    </section>

    <!-- ③ Bento Grid -->
    <section id="bento" class="bento-section fade-in-section">
      <div class="section-container">
        <div class="section-header">
          <span class="section-eyebrow">Features</span>
          <h2 class="section-title">AI가 있으면,<br>이것으로 충분합니다</h2>
          <p class="section-subtitle">학습부터 취업 준비까지 — 모두 한 곳에서, 모두 무료로</p>
        </div>

        <div class="bento-grid">
          <!-- AI 학습 플랜 — big -->
          <div class="bento-card bento-big study-card">
            <div class="mock-window">
              <div class="mock-bar">
                <div class="mock-dots">
                  <span class="mock-dot"></span>
                  <span class="mock-dot"></span>
                  <span class="mock-dot"></span>
                </div>
                <span class="mock-bar-label">수능_국어_독서.pdf</span>
              </div>
              <div class="mock-body">
                <div class="mock-section-hd">AI 요약</div>
                <div class="mock-line"></div>
                <div class="mock-line short"></div>
                <div class="mock-line"></div>
                <div class="mock-section-hd" style="margin-top: 14px;">생성된 문제</div>
                <div class="mock-q-item">
                  <span class="mock-q-circle"></span>
                  다음 중 글쓴이의 주장과 일치하는 것은?
                </div>
                <div class="mock-q-item">
                  <span class="mock-q-circle"></span>
                  밑줄 친 ⓐ의 의미로 가장 적절한 것은?
                </div>
              </div>
            </div>
            <div class="card-footer">
              <div class="card-ft-title">AI 학습 플랜</div>
              <div class="card-ft-desc">PDF 업로드 → 요약·문제 자동 생성</div>
            </div>
          </div>

          <!-- 이력서 — small -->
          <div class="bento-card bento-small resume-card">
            <div class="mock-window">
              <div class="mock-bar">
                <div class="mock-dots">
                  <span class="mock-dot"></span>
                  <span class="mock-dot"></span>
                  <span class="mock-dot"></span>
                </div>
                <span class="mock-bar-label">이력서.pdf</span>
              </div>
              <div class="mock-body">
                <div class="mock-name-row">김플래노 · 프론트엔드 개발자</div>
                <div class="mock-chips">
                  <span class="mock-chip">Vue.js</span>
                  <span class="mock-chip">React</span>
                  <span class="mock-chip">TypeScript</span>
                </div>
              </div>
            </div>
            <div class="card-footer">
              <div class="card-ft-title">이력서</div>
              <div class="card-ft-desc">AI가 함께 다듬는 나만의 이력서</div>
            </div>
          </div>

          <!-- 자소서 — small -->
          <div class="bento-card bento-small cover-card">
            <div class="mock-window">
              <div class="mock-bar">
                <div class="mock-dots">
                  <span class="mock-dot"></span>
                  <span class="mock-dot"></span>
                  <span class="mock-dot"></span>
                </div>
                <span class="mock-bar-label">자기소개서 · 지원동기</span>
              </div>
              <div class="mock-body">
                <div class="mock-line"></div>
                <div class="mock-line short"></div>
                <div class="mock-line"></div>
                <span class="mock-ai-badge">AI 다듬기 ✓</span>
              </div>
            </div>
            <div class="card-footer">
              <div class="card-ft-title">자기소개서</div>
              <div class="card-ft-desc">AI 초안으로 빠르게 시작</div>
            </div>
          </div>

          <!-- AI 튜터 — wide -->
          <div class="bento-card bento-wide tutor-card">
            <div class="mock-window">
              <div class="mock-bar">
                <div class="mock-dots">
                  <span class="mock-dot"></span>
                  <span class="mock-dot"></span>
                  <span class="mock-dot"></span>
                </div>
                <span class="mock-bar-label">AI 튜터 채팅</span>
              </div>
              <div class="mock-body mock-chat-body">
                <div class="mock-chat-r">미적분 극한값 구하는 방법을 모르겠어요 😅</div>
                <div class="mock-chat-l">극한은 x가 특정 값에 가까워질 때의 함수값이에요. 예시로 보여드릴게요!</div>
                <div class="mock-chat-r">lim(x→0) sinx/x 는 얼마예요?</div>
                <div class="mock-chat-l">그 값은 1이에요. 로피탈 정리를 쓰면 바로 구할 수 있어요 ✨</div>
              </div>
            </div>
            <div class="card-footer">
              <div class="card-ft-title">AI 튜터</div>
              <div class="card-ft-desc">모르는 개념을 즉시 질문, 무제한 응답</div>
            </div>
          </div>

          <!-- 기업 조사 — wide -->
          <div class="bento-card bento-wide jobs-card">
            <div class="mock-window">
              <div class="mock-bar">
                <div class="mock-dots">
                  <span class="mock-dot"></span>
                  <span class="mock-dot"></span>
                  <span class="mock-dot"></span>
                </div>
                <span class="mock-bar-label">기업 공고 분석</span>
              </div>
              <div class="mock-body">
                <div class="mock-job-name">카카오 · 프론트엔드 개발자</div>
                <div class="mock-chips">
                  <span class="mock-chip">서울</span>
                  <span class="mock-chip">연봉 5,000만+</span>
                  <span class="mock-chip">경력 3년+</span>
                </div>
                <div class="mock-section-hd" style="margin-top: 10px;">예상 면접 질문</div>
                <div class="mock-line short"></div>
              </div>
            </div>
            <div class="card-footer">
              <div class="card-ft-title">기업 공고 조사</div>
              <div class="card-ft-desc">채용 공고 자동 분석 + 면접 예상 질문 제공</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ④ How It Works -->
    <section class="how-section fade-in-section">
      <div class="section-container">
        <div class="section-header">
          <span class="section-eyebrow">How It Works</span>
          <h2 class="section-title">3단계로 시작하세요</h2>
          <p class="section-subtitle">복잡한 설정 없이, 지금 바로</p>
        </div>

        <div class="steps-row">
          <div
            v-for="(step, i) in steps"
            :key="step.num"
            class="step-card"
          >
            <div
              class="step-num"
              :style="step.primary ? { background: '#F76707', color: 'white' } : { background: '#1a1a1a', color: 'white' }"
            >
              {{ step.num }}
            </div>
            <h3 class="step-title">{{ step.title }}</h3>
            <p class="step-desc">{{ step.desc }}</p>

            <!-- 연결선 (마지막 제외) -->
            <div v-if="i < steps.length - 1" class="step-connector">→</div>
          </div>
        </div>

        <div class="how-cta">
          <router-link to="/auth/login" class="btn-primary">지금 무료로 시작하기 →</router-link>
        </div>
      </div>
    </section>

    <!-- ⑤ Bottom CTA -->
    <section class="dark-cta fade-in-section">
      <div class="dark-cta-inner">
        <p class="dark-cta-sub">플래노바와 함께라면</p>
        <h2 class="dark-cta-title gradient-text">
          AI 파트너가 생기면,<br>공부도 취준도 달라집니다
        </h2>
        <p class="dark-cta-desc">가입 즉시 모든 기능을 무료로. 신용카드도, 구독료도 없습니다.</p>
        <router-link to="/auth/login" class="dark-cta-btn">무료로 시작하기 →</router-link>
        <p class="dark-cta-footnote">카카오 간편가입 지원 · 개인정보 안전 보호</p>
      </div>
    </section>

  </div>
</template>

<style>
body, html {
  margin: 0;
  padding: 0;
  overflow-x: hidden;
  width: 100%;
}
</style>

<style scoped>
/* ── 공통 유틸 ── */
.page-root {
  width: 100vw;
  position: relative;
  left: 50%;
  margin-left: -50vw;
  overflow-x: hidden;
}

.section-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

.section-header {
  text-align: center;
  margin-bottom: 56px;
}

.section-eyebrow {
  display: inline-block;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #F76707;
  background: #FFF3E8;
  padding: 5px 14px;
  border-radius: 50px;
  margin-bottom: 16px;
}

.section-title {
  font-size: 2.4rem;
  font-weight: 900;
  color: #1a1a1a;
  line-height: 1.25;
  margin: 0 0 12px;
  letter-spacing: -0.02em;
}

.section-subtitle {
  font-size: 1rem;
  color: #666;
  margin: 0;
}

.gradient-text {
  background: linear-gradient(135deg, #F76707, #FF9A45);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* ── 스크롤 애니메이션 ── */
.fade-in-section {
  opacity: 0;
  transform: translateY(32px);
  transition: opacity 0.6s ease, transform 0.6s ease;
}

.fade-in-section.visible {
  opacity: 1;
  transform: translateY(0);
}

/* ── Hero ── */
.hero {
  min-height: 92vh;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 0 5vw;
  position: relative;
  box-sizing: border-box;
  overflow: hidden;
}

/* 파스텔 도트 배경 패턴 */
.hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, rgba(247, 103, 7, 0.07) 1.5px, transparent 1.5px);
  background-size: 30px 30px;
  pointer-events: none;
  z-index: 0;
}

.bg-blobs {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.bg-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.35;
}

.b1 { width: 500px; height: 500px; background: #FFD4A8; top: -120px; left: -100px; animation: blobDrift 12s ease-in-out infinite; }
.b2 { width: 380px; height: 380px; background: #FFA559; bottom: -80px; right: 5%; animation: blobDrift 15s ease-in-out infinite reverse; }
.b3 { width: 280px; height: 280px; background: #FFE0C0; top: 40%; left: 30%; animation: blobDrift 10s ease-in-out infinite 3s; }
.b4 { width: 200px; height: 200px; background: #F76707; top: 10%; right: 30%; animation: blobDrift 18s ease-in-out infinite 1s; opacity: 0.12; }

@keyframes blobDrift {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33%       { transform: translate(24px, -20px) scale(1.05); }
  66%       { transform: translate(-16px, 18px) scale(0.95); }
}

.hero-body {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  gap: 48px;
  padding: 80px 0 60px;
}

.hero-text {
  flex: 1;
  max-width: 520px;
}

.hero-eyebrow {
  display: inline-block;
  font-size: 0.82rem;
  color: #F76707;
  font-weight: 700;
  letter-spacing: 0.04em;
  background: #FFF3E8;
  padding: 6px 14px;
  border-radius: 50px;
  margin-bottom: 22px;
  text-transform: uppercase;
}

.hero-title {
  font-size: 3rem;
  font-weight: 900;
  color: #1a1a1a;
  line-height: 1.22;
  margin: 0 0 20px;
  letter-spacing: -0.025em;
}

.accent {
  font-style: normal;
  color: #F76707;
  position: relative;
}

.accent::after {
  content: '';
  position: absolute;
  left: 0; bottom: -2px;
  width: 100%; height: 4px;
  background: #F76707;
  border-radius: 2px;
}

.hero-desc {
  font-size: 1rem;
  color: #666;
  line-height: 1.7;
  margin: 0 0 32px;
}

.hero-actions {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}

.btn-primary {
  background: #F76707;
  color: white;
  border-radius: 50px;
  padding: 16px 40px;
  text-decoration: none;
  font-weight: 700;
  font-size: 1rem;
  transition: background 0.2s, transform 0.2s;
  display: inline-block;
  box-shadow: 0 6px 20px rgba(247, 103, 7, 0.35);
}

.btn-primary:hover {
  background: #d95e06;
  transform: translateY(-2px);
}

.btn-ghost {
  border: 2px solid #ddd;
  color: #555;
  border-radius: 50px;
  padding: 16px 36px;
  text-decoration: none;
  font-weight: 600;
  font-size: 1rem;
  transition: border-color 0.2s, color 0.2s;
  display: inline-block;
}

.btn-ghost:hover {
  border-color: #F76707;
  color: #F76707;
}

/* ── 탭 전환 패널 ── */
.feature-tabs-panel {
  flex: 1;
  max-width: 480px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ftab-row { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }

.ftab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 50px;
  border: 2px solid #e0e0e0;
  background: white;
  color: #888;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.ftab:hover { border-color: #F76707; color: #F76707; }
.ftab.active { background: #F76707; border-color: #F76707; color: white; }

.feature-panel {
  background: white;
  border-radius: 20px;
  padding: 32px 28px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.08);
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 280px;
}

.fp-icon-wrap { font-size: 2.2rem; color: #F76707; }
.fp-title { font-size: 1.4rem; font-weight: 800; color: #1a1a1a; margin: 0; }
.fp-desc { font-size: 0.9rem; color: #555; line-height: 1.7; margin: 0; white-space: pre-line; }
.fp-items { list-style: none; padding: 0; margin: 4px 0 0; display: flex; flex-direction: column; gap: 8px; }
.fp-items li { font-size: 0.85rem; color: #444; display: flex; align-items: center; gap: 8px; font-weight: 500; }
.fp-items li i { color: #F76707; font-size: 0.75rem; }

/* Fade transition */
.fp-fade-enter-active, .fp-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fp-fade-enter-from { opacity: 0; transform: translateY(10px); }
.fp-fade-leave-to   { opacity: 0; transform: translateY(-6px); }

/* ── 모바일 필 ── */
.mobile-feature-pills {
  display: none;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  margin-top: 28px;
}
.mfp-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 50px;
  background: #FFF3E8;
  color: #F76707;
  font-size: 0.82rem;
  font-weight: 600;
}

/* ── Stats Bar ── */
.stats-bar {
  background: linear-gradient(135deg, #FFF3E8, #fff8f3);
  border-top: 2px solid #FFD4A8;
  border-bottom: 2px solid #FFD4A8;
  padding: 48px 5vw;
}

.stats-container {
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  justify-content: space-around;
  flex-wrap: wrap;
  gap: 32px;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 2rem;
  font-weight: 900;
  background: linear-gradient(135deg, #F76707, #FF9A45);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.1;
  margin-bottom: 6px;
}

.stat-label {
  font-size: 0.88rem;
  color: #888;
  font-weight: 500;
}

/* ── Bento Grid ── */
.bento-section {
  padding: 100px 5vw;
  background: #fafafa;
}

.bento-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto auto auto;
  gap: 20px;
}

.bento-card {
  border-radius: 20px;
  padding: 18px 18px 14px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  transition: transform 0.25s, box-shadow 0.25s;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.bento-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.1);
}

.bento-big  { grid-row: span 2; }
.bento-wide { grid-column: span 2; }

/* Card accent backgrounds */
.study-card  { background: linear-gradient(145deg, #FFF3E8, #ffffff); }
.resume-card { background: linear-gradient(145deg, #EFF6FF, #ffffff); }
.cover-card  { background: linear-gradient(145deg, #F0FDF4, #ffffff); }
.tutor-card  { background: linear-gradient(145deg, #F5F3FF, #ffffff); }
.jobs-card   { background: linear-gradient(145deg, #FDF4FF, #ffffff); }

/* Mock window */
.mock-window {
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.mock-bar {
  background: #f3f3f3;
  border-radius: 10px 10px 0 0;
  padding: 8px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid #e8e8e8;
  flex-shrink: 0;
}

.mock-dots {
  display: flex;
  gap: 5px;
  flex-shrink: 0;
}

.mock-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d4d4d4;
}

.study-card  .mock-dot { background: rgba(247, 103,  7, 0.45); }
.resume-card .mock-dot { background: rgba( 59, 130,246, 0.45); }
.cover-card  .mock-dot { background: rgba( 16, 185,129, 0.45); }
.tutor-card  .mock-dot { background: rgba(139,  92,246, 0.45); }
.jobs-card   .mock-dot { background: rgba(168,  85,247, 0.45); }

.mock-bar-label {
  font-size: 0.72rem;
  color: #888;
  font-weight: 500;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mock-body {
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow: hidden;
  flex: 1;
}

/* Placeholder lines */
.mock-line {
  height: 9px;
  background: #ececec;
  border-radius: 4px;
  width: 100%;
}
.mock-line.short { width: 58%; }

.mock-section-hd {
  font-size: 0.66rem;
  font-weight: 700;
  color: #bbb;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  margin-bottom: 2px;
}

.mock-q-item {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 0.72rem;
  color: #555;
  line-height: 1.4;
}

.mock-q-circle {
  width: 13px;
  height: 13px;
  border-radius: 50%;
  border: 1.5px solid #ccc;
  flex-shrink: 0;
  display: inline-block;
}

/* Chips */
.mock-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.mock-chip {
  font-size: 0.67rem;
  font-weight: 600;
  padding: 3px 9px;
  border-radius: 50px;
  background: #f0f0f0;
  color: #555;
}

/* Resume */
.mock-name-row {
  font-size: 0.8rem;
  font-weight: 700;
  color: #333;
  margin-bottom: 4px;
}

/* Cover letter */
.mock-ai-badge {
  display: inline-flex;
  align-items: center;
  font-size: 0.68rem;
  font-weight: 700;
  color: #10B981;
  background: #F0FDF4;
  border: 1px solid rgba(16, 185, 129, 0.3);
  padding: 3px 9px;
  border-radius: 50px;
  margin-top: 4px;
  width: fit-content;
}

/* Chat bubbles */
.mock-chat-body { gap: 7px; }

.mock-chat-r {
  align-self: flex-end;
  background: #8B5CF6;
  color: white;
  font-size: 0.71rem;
  padding: 7px 11px;
  border-radius: 12px 12px 0 12px;
  max-width: 76%;
  line-height: 1.45;
}

.mock-chat-l {
  align-self: flex-start;
  background: #f0f0f0;
  color: #333;
  font-size: 0.71rem;
  padding: 7px 11px;
  border-radius: 12px 12px 12px 0;
  max-width: 82%;
  line-height: 1.45;
}

/* Jobs */
.mock-job-name {
  font-size: 0.82rem;
  font-weight: 700;
  color: #333;
  margin-bottom: 5px;
}

/* Card footer */
.card-footer {
  padding: 14px 2px 2px;
  flex-shrink: 0;
}

.card-ft-title {
  font-size: 1rem;
  font-weight: 800;
  color: #1a1a1a;
  margin-bottom: 3px;
}

.card-ft-desc {
  font-size: 0.82rem;
  color: #888;
}

/* ── How It Works ── */
.how-section {
  padding: 100px 5vw;
  background: white;
}

.steps-row {
  display: flex;
  gap: 0;
  justify-content: center;
  align-items: flex-start;
  position: relative;
}

.step-card {
  flex: 1;
  max-width: 300px;
  text-align: center;
  padding: 0 24px;
  position: relative;
}

.step-num {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  font-weight: 900;
  margin: 0 auto 20px;
}

.step-title {
  font-size: 1.1rem;
  font-weight: 800;
  color: #1a1a1a;
  margin: 0 0 10px;
}

.step-desc {
  font-size: 0.88rem;
  color: #666;
  line-height: 1.65;
  white-space: pre-line;
  margin: 0;
}

.step-connector {
  position: absolute;
  right: -16px;
  top: 16px;
  font-size: 1.4rem;
  color: #ddd;
  z-index: 1;
}

.how-cta {
  text-align: center;
  margin-top: 56px;
}

/* ── Bottom CTA ── */
.dark-cta {
  background: #1a1a1a;
  padding: 100px 5vw;
  position: relative;
  overflow: hidden;
}

.dark-cta::before {
  content: '';
  position: absolute;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(247,103,7,0.18) 0%, transparent 70%);
  top: -200px;
  left: 50%;
  transform: translateX(-50%);
  pointer-events: none;
}

.dark-cta-inner {
  position: relative;
  z-index: 1;
  text-align: center;
  max-width: 700px;
  margin: 0 auto;
}

.dark-cta-sub {
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #F76707;
  margin-bottom: 16px;
}

.dark-cta-title {
  font-size: 2.6rem;
  font-weight: 900;
  line-height: 1.25;
  margin: 0 0 20px;
  letter-spacing: -0.02em;
}

.dark-cta-desc {
  font-size: 1rem;
  color: #aaa;
  margin-bottom: 36px;
}

.dark-cta-btn {
  display: inline-block;
  background: linear-gradient(135deg, #F76707, #FF9A45);
  color: white;
  text-decoration: none;
  padding: 18px 48px;
  border-radius: 50px;
  font-size: 1.05rem;
  font-weight: 800;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 8px 24px rgba(247, 103, 7, 0.4);
}

.dark-cta-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 14px 32px rgba(247, 103, 7, 0.5);
}

.dark-cta-footnote {
  font-size: 0.8rem;
  color: #666;
  margin-top: 20px;
}

/* ── Responsive ── */
@media (max-width: 960px) {
  .feature-tabs-panel { display: none; }
  .mobile-feature-pills { display: flex; }

  .hero-title { font-size: 2.4rem; }
  .hero-body {
    flex-direction: column;
    justify-content: center;
    padding: 60px 0 50px;
  }
  .hero-text { max-width: 100%; text-align: center; }
  .hero-actions { justify-content: center; }

  .bento-grid {
    grid-template-columns: 1fr;
  }
  .bento-big, .bento-wide {
    grid-column: span 1;
    grid-row: span 1;
  }

  .steps-row {
    flex-direction: column;
    align-items: center;
    gap: 32px;
  }
  .step-connector {
    display: none;
  }
  .step-card {
    max-width: 100%;
    padding: 0;
  }

  .section-title { font-size: 1.9rem; }
  .dark-cta-title { font-size: 2rem; }
}

@media (max-width: 480px) {
  .hero-title { font-size: 1.9rem; }
  .btn-primary, .btn-ghost {
    padding: 14px 28px;
    font-size: 0.95rem;
    width: 100%;
    text-align: center;
  }
  .hero-actions { flex-direction: column; }

  .stats-container { gap: 20px; }
  .stat-number { font-size: 1.6rem; }

  .dark-cta-title { font-size: 1.6rem; }
  .dark-cta-btn { width: 100%; text-align: center; }
}
</style>
