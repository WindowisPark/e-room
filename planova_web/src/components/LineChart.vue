<script setup>
import { Line } from 'vue-chartjs'
import { Chart, registerables } from 'chart.js'
Chart.register(...registerables)

const props = defineProps({
  chartData: Object,
  chartOptions: Object
})
</script>

<template>
  <Line :chart-data="chartData" :chart-options="chartOptions" />
</template>