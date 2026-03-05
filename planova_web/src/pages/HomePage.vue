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

const currentFeature = ref(0);
let featureInterval = null;

const nextFeature = () => {
  currentFeature.value = (currentFeature.value + 1) % featureSteps.length;
};

const goToFeature = (i) => {
  currentFeature.value = i;
  clearInterval(featureInterval);
  featureInterval = setInterval(nextFeature, 3500);
};

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
  featureInterval = setInterval(nextFeature, 3500);

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
  clearInterval(featureInterval);
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

        <!-- 우: 피처 캐러셀 (데스크톱) -->
        <div class="feature-carousel">
          <div class="step-tabs">
            <button
              v-for="(step, i) in featureSteps"
              :key="i"
              :class="['step-tab', { active: currentFeature === i }]"
              :style="currentFeature === i ? { background: step.accent, color: 'white', borderColor: step.accent } : {}"
              @click="goToFeature(i)"
            >
              {{ step.step }}
            </button>
          </div>

          <div class="feature-track-wrap">
            <div
              class="feature-track"
              :style="{ transform: `translateX(-${currentFeature * 100}%)` }"
            >
              <div
                v-for="(step, i) in featureSteps"
                :key="i"
                class="feature-card"
                :style="{ background: step.bg }"
              >
                <div class="fc-top">
                  <span class="fc-step-num" :style="{ color: step.accent }">{{ step.step }}</span>
                  <span class="fc-tag">{{ step.tag }}</span>
                </div>
                <div class="fc-icon-wrap">
                  <i :class="step.faIcon" :style="{ color: step.accent }"></i>
                </div>
                <h3 class="fc-title" :style="{ color: step.accent }">{{ step.title }}</h3>
                <p class="fc-desc">{{ step.desc }}</p>
                <ul class="fc-items">
                  <li
                    v-for="item in step.items"
                    :key="item"
                    class="fc-item"
                    :style="{ borderLeftColor: step.accent }"
                  >{{ item }}</li>
                </ul>
                <div class="fc-progress-bar">
                  <div
                    class="fc-progress-fill"
                    :style="{ background: step.accent }"
                    :class="{ animating: currentFeature === i }"
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <div class="fc-arrow-row">
            <button class="fc-arrow" @click="goToFeature((currentFeature - 1 + featureSteps.length) % featureSteps.length)">←</button>
            <button class="fc-arrow" @click="goToFeature((currentFeature + 1) % featureSteps.length)">→</button>
          </div>
        </div>

        <!-- 모바일 2×2 그리드 -->
        <div class="mobile-feature-cards">
          <div
            v-for="step in featureSteps"
            :key="step.step"
            class="mfc-card"
            :style="{ borderTopColor: step.accent }"
          >
            <i :class="step.faIcon" :style="{ color: step.accent }"></i>
            <div class="mfc-title">{{ step.title }}</div>
          </div>
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
          <!-- 학습(PDF) — big -->
          <div class="bento-card bento-big" :style="{ borderTopColor: bentoFeatures[0].accent }">
            <div class="bento-tag" :style="{ color: bentoFeatures[0].accent, background: '#FFF3E8' }">
              {{ bentoFeatures[0].tag }}
            </div>
            <i :class="bentoFeatures[0].icon" class="bento-icon" :style="{ color: bentoFeatures[0].accent }"></i>
            <h3 class="bento-title">{{ bentoFeatures[0].title }}</h3>
            <p class="bento-desc">{{ bentoFeatures[0].desc }}</p>
            <ul class="bento-items">
              <li v-for="item in bentoFeatures[0].items" :key="item">
                <i class="fa-solid fa-check" :style="{ color: bentoFeatures[0].accent }"></i>
                {{ item }}
              </li>
            </ul>
            <router-link to="/auth/login" class="bento-cta" :style="{ background: bentoFeatures[0].accent }">
              PDF 학습 시작하기 →
            </router-link>
          </div>

          <!-- 이력서 -->
          <div class="bento-card bento-small" :style="{ borderTopColor: bentoFeatures[1].accent }">
            <div class="bento-tag" :style="{ color: bentoFeatures[1].accent, background: '#EFF6FF' }">
              {{ bentoFeatures[1].tag }}
            </div>
            <i :class="bentoFeatures[1].icon" class="bento-icon" :style="{ color: bentoFeatures[1].accent }"></i>
            <h3 class="bento-title">{{ bentoFeatures[1].title }}</h3>
            <p class="bento-desc">{{ bentoFeatures[1].desc }}</p>
          </div>

          <!-- 자소서 -->
          <div class="bento-card bento-small" :style="{ borderTopColor: bentoFeatures[2].accent }">
            <div class="bento-tag" :style="{ color: bentoFeatures[2].accent, background: '#F0FDF4' }">
              {{ bentoFeatures[2].tag }}
            </div>
            <i :class="bentoFeatures[2].icon" class="bento-icon" :style="{ color: bentoFeatures[2].accent }"></i>
            <h3 class="bento-title">{{ bentoFeatures[2].title }}</h3>
            <p class="bento-desc">{{ bentoFeatures[2].desc }}</p>
          </div>

          <!-- AI 튜터 — wide -->
          <div class="bento-card bento-wide" :style="{ borderTopColor: bentoFeatures[3].accent }">
            <div class="bento-tag" :style="{ color: bentoFeatures[3].accent, background: '#F5F3FF' }">
              {{ bentoFeatures[3].tag }}
            </div>
            <i :class="bentoFeatures[3].icon" class="bento-icon" :style="{ color: bentoFeatures[3].accent }"></i>
            <h3 class="bento-title">{{ bentoFeatures[3].title }}</h3>
            <p class="bento-desc">{{ bentoFeatures[3].desc }}</p>
          </div>

          <!-- 기업 조사 — wide -->
          <div class="bento-card bento-wide" :style="{ borderTopColor: bentoFeatures[4].accent }">
            <div class="bento-tag" :style="{ color: bentoFeatures[4].accent, background: '#FDF4FF' }">
              {{ bentoFeatures[4].tag }}
            </div>
            <i :class="bentoFeatures[4].icon" class="bento-icon" :style="{ color: bentoFeatures[4].accent }"></i>
            <h3 class="bento-title">{{ bentoFeatures[4].title }}</h3>
            <p class="bento-desc">{{ bentoFeatures[4].desc }}</p>
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

/* ── 피처 캐러셀 (데스크톱) ── */
.feature-carousel {
  flex: 1;
  max-width: 460px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.step-tabs { display: flex; gap: 8px; }

.step-tab {
  width: 40px; height: 40px;
  border-radius: 50%;
  border: 2px solid #e0e0e0;
  background: white; color: #999;
  font-weight: 800; font-size: 0.8rem;
  cursor: pointer; transition: all 0.25s;
}

.step-tab:hover { border-color: #F76707; color: #F76707; }

.feature-track-wrap {
  overflow: hidden;
  border-radius: 20px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.1);
}

.feature-track {
  display: flex;
  transition: transform 0.45s cubic-bezier(0.4, 0, 0.2, 1);
}

.feature-card {
  min-width: 100%;
  padding: 32px 28px 24px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 340px;
}

.fc-top { display: flex; align-items: center; justify-content: space-between; }
.fc-step-num { font-size: 1.8rem; font-weight: 900; line-height: 1; }
.fc-tag { font-size: 0.75rem; color: #999; background: white; padding: 4px 10px; border-radius: 50px; font-weight: 600; }

.fc-icon-wrap {
  font-size: 2rem;
}

.fc-title { font-size: 1.4rem; font-weight: 800; margin: 0; }
.fc-desc { font-size: 0.88rem; color: #555; line-height: 1.65; margin: 0; white-space: pre-line; }

.fc-items { list-style: none; padding: 0; margin: 4px 0 0; display: flex; flex-direction: column; gap: 6px; }
.fc-item { font-size: 0.82rem; color: #444; padding-left: 12px; border-left: 3px solid; font-weight: 500; }

.fc-progress-bar { height: 3px; background: rgba(0,0,0,0.08); border-radius: 2px; margin-top: auto; overflow: hidden; }
.fc-progress-fill { height: 100%; width: 0%; border-radius: 2px; }
.fc-progress-fill.animating { animation: progressFill 3.5s linear forwards; }

@keyframes progressFill { from { width: 0%; } to { width: 100%; } }

.fc-arrow-row { display: flex; gap: 8px; justify-content: flex-end; }
.fc-arrow {
  width: 36px; height: 36px; border-radius: 50%;
  border: 2px solid #e0e0e0; background: white;
  font-size: 1rem; cursor: pointer; transition: all 0.2s;
}
.fc-arrow:hover { border-color: #F76707; color: #F76707; }

/* ── 모바일 피처 카드 ── */
.mobile-feature-cards {
  display: none;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  width: 100%;
  margin-top: 32px;
}

.mfc-card {
  background: #fafafa;
  border-top: 4px solid;
  border-radius: 12px;
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  font-size: 0.88rem;
  font-weight: 600;
  color: #333;
}

.mfc-card i {
  font-size: 1.6rem;
}

.mfc-title {
  font-size: 0.88rem;
  font-weight: 600;
  color: #333;
  text-align: center;
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
  background: white;
  border-radius: 20px;
  padding: 32px 28px;
  border-top: 4px solid;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  transition: transform 0.25s, box-shadow 0.25s;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.bento-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.1);
}

.bento-big {
  grid-row: span 2;
}

.bento-wide {
  grid-column: span 2;
}

.bento-tag {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 50px;
  width: fit-content;
}

.bento-icon {
  font-size: 2rem;
  margin: 4px 0;
}

.bento-title {
  font-size: 1.3rem;
  font-weight: 800;
  color: #1a1a1a;
  margin: 0;
}

.bento-desc {
  font-size: 0.9rem;
  color: #555;
  line-height: 1.65;
  margin: 0;
}

.bento-items {
  list-style: none;
  padding: 0;
  margin: 8px 0 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bento-items li {
  font-size: 0.88rem;
  color: #444;
  display: flex;
  align-items: center;
  gap: 8px;
}

.bento-items li i {
  font-size: 0.78rem;
}

.bento-cta {
  display: inline-block;
  color: white;
  text-decoration: none;
  padding: 12px 24px;
  border-radius: 50px;
  font-size: 0.9rem;
  font-weight: 700;
  margin-top: auto;
  transition: opacity 0.2s, transform 0.2s;
  width: fit-content;
  box-shadow: 0 4px 14px rgba(247, 103, 7, 0.3);
}

.bento-cta:hover {
  opacity: 0.9;
  transform: translateY(-1px);
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
  .feature-carousel {
    display: none;
  }

  .mobile-feature-cards {
    display: grid;
  }

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
