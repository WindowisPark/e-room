<template>
  <div
    class="promo-banner"
    @mouseenter="pause"
    @mouseleave="resume"
  >
    <div class="banner-track" :style="{ transform: `translateX(-${current * 100}%)` }">
      <div
        v-for="(slide, idx) in slides"
        :key="idx"
        class="banner-slide"
      >
        <!-- 이미지 슬라이드 -->
        <a v-if="slide.type === 'image'" :href="slide.link" class="slide-link">
          <img :src="slide.src" :alt="slide.alt" class="slide-img" />
        </a>
        <!-- 텍스트 슬라이드 -->
        <a v-else :href="slide.link" class="slide-link text-slide" :style="{ background: slide.bg }">
          <div class="text-inner">
            <p class="slide-title" v-html="slide.title.replace(/\n/g, '<br>')"></p>
            <span class="slide-cta">{{ slide.cta }} →</span>
          </div>
        </a>
      </div>
    </div>

    <!-- 이전/다음 버튼 -->
    <button class="banner-nav nav-prev" @click.prevent="prev" aria-label="이전">&#8249;</button>
    <button class="banner-nav nav-next" @click.prevent="next" aria-label="다음">&#8250;</button>

    <!-- 도트 인디케이터 -->
    <div class="dot-row">
      <button
        v-for="(_, idx) in slides"
        :key="idx"
        :class="['dot', { active: current === idx }]"
        @click="goTo(idx)"
        :aria-label="`슬라이드 ${idx + 1}`"
      ></button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import imgAttendance from '@/assets/images/event_attendance_banner.png';
import imgInvite     from '@/assets/images/event_invite_banner.png';
import imgCoupon     from '@/assets/images/event_lucky_coupon_banner.png';
import imgMain1      from '@/assets/images/planova_main_1.png';
import imgMain2      from '@/assets/images/planova_main_2.png';

const slides = [
  { type: 'image', src: imgAttendance, alt: '출석 이벤트',       link: '#' },
  { type: 'text',  bg: '#F76707',      title: '이력서 AI 피드백\n지금 바로 사용해보세요',     cta: '이력서 작성하기', link: '/student/resume' },
  { type: 'image', src: imgInvite,     alt: '친구 초대 이벤트',   link: '#' },
  { type: 'text',  bg: '#1a1a2e',      title: '학창시절부터 취업까지\n모든 계획은 플래노바가', cta: '시작하기',       link: '/student/myroom' },
  { type: 'image', src: imgCoupon,     alt: '럭키 쿠폰',          link: '#' },
  { type: 'image', src: imgMain1,      alt: '플래노바 소개',       link: '#' },
  { type: 'image', src: imgMain2,      alt: '플래노바 소개 2',     link: '#' },
];

const current = ref(0);
let timer = null;

const next = () => { current.value = (current.value + 1) % slides.length; };
const prev = () => { current.value = (current.value - 1 + slides.length) % slides.length; };
const goTo = (idx) => { current.value = idx; };

const start = () => { timer = setInterval(next, 4000); };
const pause = () => { clearInterval(timer); timer = null; };
const resume = () => { if (!timer) start(); };

onMounted(start);
onBeforeUnmount(pause);
</script>

<style scoped>
.promo-banner {
  position: relative;
  width: 95%;
  margin: 20px auto 0;
  height: 160px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  cursor: pointer;
}

.banner-track {
  display: flex;
  height: 100%;
  transition: transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.banner-slide {
  min-width: 100%;
  height: 100%;
  flex-shrink: 0;
}

.slide-link {
  display: block;
  width: 100%;
  height: 100%;
  text-decoration: none;
}

.slide-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

/* 텍스트 슬라이드 */
.text-slide {
  display: flex;
  align-items: center;
  padding: 0 48px;
}

.text-inner {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.slide-title {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  line-height: 1.4;
  margin: 0;
}

.slide-cta {
  display: inline-block;
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: var(--radius-full);
  padding: 4px 14px;
  transition: background 0.2s;
}

.text-slide:hover .slide-cta {
  background: rgba(255, 255, 255, 0.15);
}

/* 이전/다음 버튼 */
.banner-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(0, 0, 0, 0.35);
  color: #fff;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.nav-prev { left: 10px; }
.nav-next { right: 10px; }

.promo-banner:hover .banner-nav { opacity: 1; }

.banner-nav:hover { background: rgba(0, 0, 0, 0.55); }

/* 도트 인디케이터 */
.dot-row {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 6px;
  align-items: center;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.5);
  border: none;
  cursor: pointer;
  padding: 0;
  transition: all 0.25s;
}

.dot.active {
  width: 20px;
  border-radius: 3px;
  background: #fff;
}
</style>
