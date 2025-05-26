<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import DefaultLayout from './components/layouts/DefaultLayout.vue';
import StudentLayout from './components/layouts/StudentLayout.vue';

const route = useRoute();

const useStudentLayout = computed(() => {
  return route.path.startsWith('/student');
});

const useDefaultLayout = computed(() => {
  return !useStudentLayout.value;
});
</script>

<template>
  <DefaultLayout v-if="useDefaultLayout">
    <router-view />
  </DefaultLayout>
  <StudentLayout v-else-if="useStudentLayout">
    <router-view />
  </StudentLayout>
  <router-view v-else />
</template>