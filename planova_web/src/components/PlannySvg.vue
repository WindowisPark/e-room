<script setup>
import { computed } from 'vue';

const props = defineProps({
  size:  { type: Number, default: 100 },
  stage: { type: Number, default: 2 },   // 1~4
});

// Unique clip-path ID per instance to avoid conflicts when multiple Plannys on the same page
const uid = `planny-${Math.random().toString(36).slice(2, 8)}`;
const clipId = `ring-clip-${uid}`;

const planetColor  = computed(() => props.stage === 1 ? '#FFAA6E' : '#F76707');
const planetRadius = computed(() => props.stage === 1 ? 22 : 30);
const showRing     = computed(() => props.stage >= 2);
const ringWidth    = computed(() => props.stage >= 3 ? 9 : 6);
const showSparkles = computed(() => props.stage === 4);
const showGlow     = computed(() => props.stage >= 3);
</script>

<template>
  <svg :width="size" :height="size" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="플래니 마스코트">
    <defs>
      <!-- Clip path for the front half of the Saturn ring -->
      <clipPath :id="clipId">
        <rect x="0" y="58" width="100" height="42" />
      </clipPath>
      <!-- Glow filter for stage 3~4 -->
      <filter v-if="showGlow" :id="`glow-${uid}`">
        <feGaussianBlur stdDeviation="3" result="blur"/>
        <feMerge>
          <feMergeNode in="blur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
    </defs>

    <!-- Ring — back half (stage >= 2) -->
    <ellipse v-if="showRing" cx="50" cy="58" rx="44" ry="10" fill="none" stroke="#FFB366" :stroke-width="ringWidth" opacity="0.6" />

    <!-- Planet body -->
    <circle cx="50" cy="47" :r="planetRadius" :fill="planetColor" :filter="showGlow ? `url(#glow-${uid})` : undefined" />

    <!-- Shine highlight -->
    <ellipse cx="40" cy="35" rx="10" ry="7" fill="white" opacity="0.22" transform="rotate(-25 40 35)" />

    <!-- Eyes: stage 1 — half-closed (drowsy arcs) -->
    <template v-if="stage === 1">
      <path d="M 33 44 Q 40 40 47 44" stroke="#1a1a1a" stroke-width="2.5" fill="none" stroke-linecap="round" />
      <path d="M 55 44 Q 62 40 69 44" stroke="#1a1a1a" stroke-width="2.5" fill="none" stroke-linecap="round" />
    </template>

    <!-- Eyes: stage 2 — normal (white sclera + pupils) -->
    <template v-else-if="stage === 2">
      <circle cx="40" cy="44" r="7.5" fill="white" />
      <circle cx="62" cy="44" r="7.5" fill="white" />
      <circle cx="42" cy="45.5" r="3.8" fill="#1a1a1a" />
      <circle cx="64" cy="45.5" r="3.8" fill="#1a1a1a" />
      <circle cx="43.5" cy="43.8" r="1.4" fill="white" />
      <circle cx="65.5" cy="43.8" r="1.4" fill="white" />
    </template>

    <!-- Eyes: stage 3~4 — wide open, bigger pupils shifted up -->
    <template v-else>
      <circle cx="40" cy="44" r="7.5" fill="white" />
      <circle cx="62" cy="44" r="7.5" fill="white" />
      <circle cx="42" cy="44" r="4.3" fill="#1a1a1a" />
      <circle cx="64" cy="44" r="4.3" fill="#1a1a1a" />
      <circle cx="43.5" cy="42.5" r="1.4" fill="white" />
      <circle cx="65.5" cy="42.5" r="1.4" fill="white" />
    </template>

    <!-- Smile -->
    <path d="M 37 57 Q 50 68 63 57" stroke="white" stroke-width="3" fill="none" stroke-linecap="round" />

    <!-- Ring — front half (clipped to below planet center, drawn over planet) -->
    <ellipse v-if="showRing" cx="50" cy="58" rx="44" ry="10" fill="none" stroke="#FFCA99" :stroke-width="ringWidth" :clip-path="`url(#${clipId})`" opacity="0.95" />

    <!-- Sparkles: stage 4 only -->
    <template v-if="showSparkles">
      <text x="14" y="20" font-size="10" opacity="0.9">✦</text>
      <text x="76" y="20" font-size="10" opacity="0.9">✦</text>
      <text x="10" y="72" font-size="8"  opacity="0.7">✦</text>
      <text x="80" y="72" font-size="8"  opacity="0.7">✦</text>
    </template>
  </svg>
</template>
