<template>
  <div>
    <h1 class="text-2xl font-bold mb-6">Background Jobs</h1>

    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <div v-else-if="jobsList.length === 0" class="text-center py-12 text-gray-500">
      No background jobs configured
    </div>

    <div v-else class="grid gap-4">
      <div v-for="job in jobsList" :key="job.id" class="card">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <h3 class="text-lg font-semibold">{{ job.name }}</h3>
            <p class="text-sm text-gray-600 mt-1">ID: {{ job.id }}</p>
            <p class="text-sm text-gray-600">Schedule: {{ job.trigger }}</p>
            <p v-if="job.next_run_time" class="text-sm text-gray-600 mt-2">
              Next run: {{ formatDate(job.next_run_time) }}
            </p>
          </div>

          <div class="flex gap-2">
            <button
              @click="triggerJob(job.id)"
              class="btn btn-primary text-sm"
              title="Run now"
            >
              ▶ Run
            </button>
            <button
              @click="pauseJob(job.id)"
              class="btn btn-secondary text-sm"
              title="Pause"
            >
              ⏸ Pause
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Refresh Button -->
    <div class="mt-6">
      <button @click="loadJobs" class="btn btn-secondary">
        ↻ Refresh
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { jobs } from '../services/api'

const jobsList = ref([])
const loading = ref(false)

onMounted(() => {
  loadJobs()
})

async function loadJobs() {
  loading.value = true
  try {
    const response = await jobs.getAll()
    jobsList.value = response.data.jobs || []
  } catch (err) {
    console.error('Error loading jobs:', err)
  } finally {
    loading.value = false
  }
}

async function triggerJob(jobId) {
  try {
    await jobs.trigger(jobId)
    alert(`Job '${jobId}' triggered successfully!`)
    loadJobs()
  } catch (err) {
    alert('Failed to trigger job')
  }
}

async function pauseJob(jobId) {
  try {
    await jobs.pause(jobId)
    alert(`Job '${jobId}' paused`)
    loadJobs()
  } catch (err) {
    alert('Failed to pause job')
  }
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleString()
}
</script>
