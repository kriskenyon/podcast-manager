<template>
  <div class="card">
    <div class="flex items-start justify-between gap-4">
      <div class="flex-1">
        <div class="flex items-center gap-2">
          <span
            :class="[
              'inline-block w-2 h-2 rounded-full',
              statusColor
            ]"
          />
          <span class="text-sm font-medium text-gray-500">{{ download.status.toUpperCase() }}</span>
        </div>

        <p class="text-sm text-gray-600 mt-1">{{ download.file_path || 'No path' }}</p>

        <!-- Progress Bar -->
        <div v-if="download.status === 'downloading'" class="mt-3">
          <div class="flex justify-between text-sm text-gray-600 mb-1">
            <span>Progress</span>
            <span>{{ Math.round(download.progress * 100) }}%</span>
          </div>
          <div class="w-full bg-gray-200 rounded-full h-2">
            <div
              class="bg-blue-600 h-2 rounded-full transition-all"
              :style="{ width: `${download.progress * 100}%` }"
            />
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="download.error_message" class="mt-2 p-2 bg-red-50 rounded text-sm text-red-700">
          {{ download.error_message }}
        </div>

        <!-- Stats -->
        <div class="mt-2 flex gap-4 text-xs text-gray-500">
          <span v-if="download.file_size">{{ formatFileSize(download.file_size) }}</span>
          <span v-if="download.retry_count > 0">Retries: {{ download.retry_count }}</span>
          <span v-if="download.completed_at">{{ formatDate(download.completed_at) }}</span>
        </div>
      </div>

      <button
        @click="$emit('delete', download.id)"
        class="text-red-600 hover:text-red-700"
        title="Delete"
      >
        ×
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  download: {
    type: Object,
    required: true,
  },
})

defineEmits(['delete', 'refresh'])

const statusColor = computed(() => {
  switch (props.download.status) {
    case 'completed':
      return 'bg-green-500'
    case 'downloading':
      return 'bg-blue-500 animate-pulse'
    case 'failed':
      return 'bg-red-500'
    case 'pending':
      return 'bg-yellow-500'
    default:
      return 'bg-gray-500'
  }
})

function formatFileSize(bytes) {
  if (!bytes) return ''
  const mb = bytes / (1024 * 1024)
  return `${mb.toFixed(1)} MB`
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleString()
}
</script>
