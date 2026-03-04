<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
// 우측 피처 스텝 캐러셀
const featureSteps = [
  {
    step: '01',
    icon: '📚',
    tag: '학생 · 수험생',
    title: 'AI 학습 플랜',
    desc: '나의 목표와 일정에 맞게\nAI가 최적의 학습 플랜을 설계해드려요.',
    bg: '#FFF8F0',
    accent: '#F76707',
    items: ['과목별 일정 자동 배분', '약점 집중 학습 추천', '24시간 AI 질문 응답']
  },
  {
    step: '02',
    icon: '📄',
    tag: '취업 준비생',
    title: '이력서·포트폴리오',
    desc: 'AI가 함께 다듬어주는 나만의 이력서,\n첫인상부터 완벽하게 만들어보세요.',
    bg: '#F0F5FF',
    accent: '#3B82F6',
    items: ['AI 문구 개선 제안', '직무 맞춤 키워드 추출', '포트폴리오 구성 가이드']
  },
  {
    step: '03',
    icon: '✍️',
    tag: '취업 준비생',
    title: '자기소개서',
    desc: 'AI 초안으로 시작해서\n나다운 자소서로 완성하세요.',
    bg: '#F0FDF4',
    accent: '#10B981',
    items: ['AI 초안 자동 생성', '지원 기업별 맞춤 편집', '합격 자소서 패턴 분석']
  },
  {
    step: '04',
    icon: '🔍',
    tag: '취업 준비생',
    title: '기업 조사',
    desc: '공고 분석부터 기업 정보까지\n한눈에 파악하고 준비하세요.',
    bg: '#FDF4FF',
    accent: '#A855F7',
    items: ['채용 공고 자동 스크래핑', '기업 문화·연봉 정보', '면접 예상 질문 제공']
  }
]

const currentFeature = ref(0);
let featureInterval = null;

const nextFeature = () => {
  currentFeature.value = (currentFeature.value + 1) % featureSteps.length;
};

const goToFeature = (i) => {
  currentFeature.value = i;
  // 인터벌 리셋
  clearInterval(featureInterval);
  featureInterval = setInterval(nextFeature, 3500);
};

onMounted(() => {
  featureInterval = setInterval(nextFeature, 3500);
});

onBeforeUnmount(() => {
  clearInterval(featureInterval);
});
</script>

<template>
  <div class="page-root">
    <!-- ① Hero -->
    <section class="hero">
      <!-- 배경 애니메이션 블롭 -->
      <div class="bg-blobs" aria-hidden="true">
        <div class="bg-blob b1"></div>
        <div class="bg-blob b2"></div>
        <div class="bg-blob b3"></div>
        <div class="bg-blob b4"></div>
      </div>

      <div class="hero-body">
        <!-- 좌: 텍스트 -->
        <div class="hero-text">
          <span class="hero-eyebrow">학창시절부터 취업까지 AI 파트너</span>
          <h1 class="hero-title">
            당신의 모든 계획,<br>
            <em class="accent">플래노바</em>가<br>함께합니다
          </h1>
          <p class="hero-desc">
            AI 학습 플랜으로 실력을 쌓고,<br>
            이력서·자소서·기업 조사까지 한 번에
          </p>
          <div class="hero-actions">
            <router-link to="/auth/login" class="btn-primary">지금 시작하기 →</router-link>
            <router-link to="/auth/signup" class="btn-ghost">무료로 가입하기</router-link>
          </div>
        </div>

        <!-- 우: 피처 스텝 캐러셀 -->
        <div class="feature-carousel">
          <!-- 스텝 탭 -->
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

          <!-- 카드 슬라이드 -->
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
                <div class="fc-icon-wrap">{{ step.icon }}</div>
                <h3 class="fc-title" :style="{ color: step.accent }">{{ step.title }}</h3>
                <p class="fc-desc">{{ step.desc }}</p>
                <ul class="fc-items">
                  <li
                    v-for="item in step.items"
                    :key="item"
                    class="fc-item"
                    :style="{ borderLeftColor: step.accent }"
                  >
                    {{ item }}
                  </li>
                </ul>
                <!-- 진행 바 -->
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

          <!-- 화살표 -->
          <div class="fc-arrow-row">
            <button class="fc-arrow" @click="goToFeature((currentFeature - 1 + featureSteps.length) % featureSteps.length)">←</button>
            <button class="fc-arrow" @click="goToFeature((currentFeature + 1) % featureSteps.length)">→</button>
          </div>
        </div>
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
/* ── 전체 래퍼 (full-width breakout) ── */
.page-root {
  width: 100vw;
  position: relative;
  left: 50%;
  margin-left: -50vw;
  overflow-x: hidden;
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

/* 배경 블롭 애니메이션 */
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

.b1 {
  width: 500px; height: 500px;
  background: #FFD4A8;
  top: -120px; left: -100px;
  animation: blobDrift 12s ease-in-out infinite;
}
.b2 {
  width: 380px; height: 380px;
  background: #FFA559;
  bottom: -80px; right: 5%;
  animation: blobDrift 15s ease-in-out infinite reverse;
}
.b3 {
  width: 280px; height: 280px;
  background: #FFE0C0;
  top: 40%; left: 30%;
  animation: blobDrift 10s ease-in-out infinite 3s;
}
.b4 {
  width: 200px; height: 200px;
  background: #F76707;
  top: 10%; right: 30%;
  animation: blobDrift 18s ease-in-out infinite 1s;
  opacity: 0.12;
}

@keyframes blobDrift {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33%       { transform: translate(24px, -20px) scale(1.05); }
  66%       { transform: translate(-16px, 18px) scale(0.95); }
}

/* ── Hero body ── */
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

/* ── 좌: 텍스트 ── */
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

/* ── 우: 피처 캐러셀 ── */
.feature-carousel {
  flex: 1;
  max-width: 460px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.step-tabs {
  display: flex;
  gap: 8px;
}

.step-tab {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2px solid #e0e0e0;
  background: white;
  color: #999;
  font-weight: 800;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.25s;
}

.step-tab:hover {
  border-color: #F76707;
  color: #F76707;
}

/* 슬라이드 래퍼 */
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

.fc-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.fc-step-num {
  font-size: 1.8rem;
  font-weight: 900;
  line-height: 1;
}

.fc-tag {
  font-size: 0.75rem;
  color: #999;
  background: white;
  padding: 4px 10px;
  border-radius: 50px;
  font-weight: 600;
}

.fc-icon-wrap {
  font-size: 2.4rem;
}

.fc-title {
  font-size: 1.4rem;
  font-weight: 800;
  margin: 0;
}

.fc-desc {
  font-size: 0.88rem;
  color: #555;
  line-height: 1.65;
  margin: 0;
  white-space: pre-line;
}

.fc-items {
  list-style: none;
  padding: 0;
  margin: 4px 0 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.fc-item {
  font-size: 0.82rem;
  color: #444;
  padding-left: 12px;
  border-left: 3px solid;
  font-weight: 500;
}

/* 진행바 */
.fc-progress-bar {
  height: 3px;
  background: rgba(0, 0, 0, 0.08);
  border-radius: 2px;
  margin-top: auto;
  overflow: hidden;
}

.fc-progress-fill {
  height: 100%;
  width: 0%;
  border-radius: 2px;
}

.fc-progress-fill.animating {
  animation: progressFill 3.5s linear forwards;
}

@keyframes progressFill {
  from { width: 0%; }
  to   { width: 100%; }
}

/* 화살표 */
.fc-arrow-row {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.fc-arrow {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 2px solid #e0e0e0;
  background: white;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.fc-arrow:hover {
  border-color: #F76707;
  color: #F76707;
}

/* ── Responsive ── */
@media (max-width: 960px) {
  .feature-carousel {
    display: none;
  }

  .hero-title {
    font-size: 2.4rem;
  }

  .hero-body {
    justify-content: center;
    padding: 60px 0 50px;
  }

  .hero-text {
    max-width: 100%;
    text-align: center;
  }

  .hero-actions {
    justify-content: center;
  }

  .hero-eyebrow {
    display: inline-block;
  }
}

@media (max-width: 480px) {
  .hero-title {
    font-size: 1.9rem;
  }

  .btn-primary, .btn-ghost {
    padding: 14px 28px;
    font-size: 0.95rem;
    width: 100%;
    text-align: center;
  }

  .hero-actions {
    flex-direction: column;
  }
}
</style>
