<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';

// ✅ 이미지 정적 import (이게 가장 확실합니다)
import main1 from '@/assets/images/main.png'
import main2 from '@/assets/images/main-2.png'
import main3 from '@/assets/images/main-3.png'

const slides = [
  { src: main1, alt: '메인 이미지 1' },
  { src: main2, alt: '메인 이미지 2' },
  { src: main3, alt: '메인 이미지 3' }
]

const imagesLoaded = ref(false);
const currentIndex = ref(0);
let intervalId = null;

const nextSlide = () => {
  currentIndex.value = (currentIndex.value + 1) % slides.length;
};

const prevSlide = () => {
  currentIndex.value = (currentIndex.value - 1 + slides.length) % slides.length;
};

const goToSlide = (index) => {
  currentIndex.value = index;
};

const checkImagesLoaded = () => {
  console.log('이미지 로드 체크 중...');
  imagesLoaded.value = true;
};

onMounted(() => {
  console.log('슬라이드 이미지 경로:', slides.map(slide => slide.src));
  intervalId = setInterval(nextSlide, 5000);
});

onBeforeUnmount(() => {
  if (intervalId) clearInterval(intervalId);
});
</script>

<template>
  <div class="image-wrapper">
    <div class="slider-container">
      <div 
        class="slider-track" 
        :style="{ transform: `translateX(-${currentIndex * 100}%)` }"
      >
        <div v-for="(slide, index) in slides" :key="index" class="slide">
          <img 
            :src="slide.src" 
            :alt="slide.alt" 
            class="absolute-fullwidth-image"
            @load="checkImagesLoaded"
            @error="console.error(`이미지 로드 실패: ${slide.src}`)"
          >
        </div>
      </div>
      <div class="indicators">
        <button 
          v-for="(slide, index) in slides" 
          :key="index"
          @click="goToSlide(index)"
          :class="['indicator-dot', { active: currentIndex === index }]"
        ></button>
      </div>
    </div>
    
    <div v-if="!imagesLoaded" class="debug-message">
      이미지 로딩 중... (이미지가 보이지 않는다면 경로를 확인해주세요)
    </div>
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
.image-wrapper {
  width: 100vw;
  margin: 0;
  padding: 0;
  overflow: hidden;
  position: relative;
  left: 50%;
  right: 50%;
  margin-left: -50vw;
  margin-right: -50vw;
}

.slider-container {
  position: relative;
  overflow: hidden;
  width: 100%;
  height: 500px;
}

.slider-track {
  display: flex;
  transition: transform 0.5s ease-in-out;
  width: 100%;
  height: 100%;
}

.slide {
  min-width: 100%;
  flex: 0 0 auto;
  height: 100%;
}

.absolute-fullwidth-image {
  width: 100%;
  height: 100%;
  display: block;
  margin: 0;
  padding: 0;
  object-fit: cover;
}

.nav-button {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background-color: rgba(255, 255, 255, 0.5);
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  font-size: 18px;
  z-index: 10;
}

.prev-button {
  left: 20px;
}

.next-button {
  right: 20px;
}

.indicators {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
  z-index: 10;
}

.indicator-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.5);
  border: none;
  cursor: pointer;
}

.indicator-dot.active {
  background-color: white;
}

.debug-message {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 10px;
  border-radius: 5px;
  z-index: 20;
}
</style>