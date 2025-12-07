<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Downloads</h1>
      <div class="flex gap-2">
        <button @click="processQueue" class="btn btn-primary">
          ▶ Process Queue
        </button>
        <button @click="retryFailed" class="btn btn-secondary">
          ↻ Retry Failed
        </button>
      </div>
    </div>

    <!-- Filter Tabs -->
    <div class="mb-6 border-b">
      <nav class="flex gap-4">
        <button
          v-for="status in statuses"
          :key="status.value"
          @click="currentStatus = status.value"
          :class="[
            'pb-2 px-1 border-b-2 font-medium text-sm',
            currentStatus === status.value
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          ]"
        >
          {{ status.label }}
        </button>
      </nav>
    </div>

    <!-- Downloads List -->
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <div v-else-if="downloadsList.length === 0" class="text-center py-12 text-gray-500">
      No {{ currentStatus || 'downloads' }} found
    </div>

    <div v-else class="space-y-3">
      <DownloadItem
        v-for="download in downloadsList"
        :key="download.id"
        :download="download"
        @delete="handleDelete"
        @refresh="loadDownloads"
      />
    </div>

    <!-- Auto-refresh toggle -->
    <div class="mt-6 flex items-center gap-2 text-sm">
      <input
        v-model="autoRefresh"
        type="checkbox"
        id="auto-refresh"
        class="w-4 h-4 text-blue-600"
      />
      <label for="auto-refresh" class="text-gray-700">
        Auto-refresh every 5 seconds
      </label>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { downloads } from '../services/api'
import DownloadItem from '../components/DownloadItem.vue'

const currentStatus = ref('')
const downloadsList = ref([])
const loading = ref(false)
const autoRefresh = ref(false)
let refreshInterval = null

const statuses = [
  { label: 'All', value: '' },
  { label: 'Pending', value: 'pending' },
  { label: 'Downloading', value: 'downloading' },
  { label: 'Completed', value: 'completed' },
  { label: 'Failed', value: 'failed' },
]

onMounted(() => {
  loadDownloads()
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})

watch(currentStatus, () => {
  loadDownloads()
})

watch(autoRefresh, (value) => {
  if (value) {
    refreshInterval = setInterval(loadDownloads, 5000)
  } else if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
})

async function loadDownloads() {
  loading.value = true
  try {
    const params = currentStatus.value ? { status: currentStatus.value } : {}
    const response = await downloads.getAll(params)
    downloadsList.value = response.data.downloads
  } catch (err) {
    console.error('Error loading downloads:', err)
  } finally {
    loading.value = false
  }
}

async function processQueue() {
  try {
    await downloads.processQueue()
    alert('Download queue processing started!')
    setTimeout(loadDownloads, 2000)
  } catch (err) {
    alert('Failed to process queue')
  }
}

async function retryFailed() {
  try {
    await downloads.retryFailed()
    alert('Retrying failed downloads!')
    loadDownloads()
  } catch (err) {
    alert('Failed to retry downloads')
  }
}

async function handleDelete(id) {
  if (confirm('Delete this download?')) {
    try {
      await downloads.delete(id)
      loadDownloads()
    } catch (err) {
      alert('Failed to delete download')
    }
  }
}
</script>
