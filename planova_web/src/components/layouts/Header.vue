<script setup>
import config from '@/config';
</script>

<template>
  <div class="banner-wrapper">
    <div class="top-banner">지금 가입하면 즉시 사용 가능한<span class="highlight"> 100플래닛 </span> 제공</div>
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
.banner-wrapper {
  width: 100vw;
  margin: 0;
  padding: 0;
  position: relative;
  left: 50%;
  right: 50%;
  margin-left: -50vw;
  margin-right: -50vw;
}

.top-banner {
  background: #FF8538;
  color: white;
  text-align: center;
  padding: 10px 0;
  font-size: 18px;
  width: 100%;
  margin: 0;
}

.highlight {
  color: black;
  font-size: 18px;
  font-weight: 600;
}
</style>