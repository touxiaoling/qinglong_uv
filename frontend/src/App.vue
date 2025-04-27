<script setup>
import { ref, onMounted } from 'vue'
import api from './api'

const message = ref('')

onMounted(async () => {
  try {
    const data = await api.getHello()
    message.value = data.message
  } catch (error) {
    message.value = 'Failed to load message from API'
  }
})
</script>

<template>
  <div>
    <h1>FastAPI + Vue3 Template</h1>
    <p>Message from backend: {{ message }}</p>
  </div>
</template>