<template>
  <div class="flex items-start gap-4 p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
    <div class="flex-1">
      <h3 class="font-semibold text-gray-900">{{ episode.title }}</h3>
      <div
        v-if="episode.description"
        class="text-sm text-gray-600 mt-1 line-clamp-2 episode-description"
        v-html="episode.description"
      ></div>
      <div class="flex gap-4 mt-2 text-sm text-gray-500">
        <span v-if="episode.pub_date">{{ formatDate(episode.pub_date) }}</span>
        <span v-if="episode.duration">{{ formatDuration(episode.duration) }}</span>
        <span v-if="episode.file_size">{{ formatFileSize(episode.file_size) }}</span>
      </div>
    </div>
    <button
      @click="$emit('download', episode.id)"
      class="btn btn-primary text-sm flex-shrink-0"
    >
      ⬇ Download
    </button>
  </div>
</template>

<script setup>
defineProps({
  episode: {
    type: Object,
    required: true,
  },
})

defineEmits(['download'])

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString()
}

function formatDuration(seconds) {
  if (!seconds) return ''
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  return `${minutes}m`
}

function formatFileSize(bytes) {
  if (!bytes) return ''
  const mb = bytes / (1024 * 1024)
  return `${mb.toFixed(1)} MB`
}
</script>

<style scoped>
.episode-description :deep(a) {
  @apply text-blue-600 hover:underline;
}

.episode-description :deep(strong),
.episode-description :deep(b) {
  @apply font-semibold;
}

.episode-description :deep(em),
.episode-description :deep(i) {
  @apply italic;
}

.episode-description :deep(ul),
.episode-description :deep(ol) {
  @apply ml-4;
}

.episode-description :deep(li) {
  @apply list-disc;
}
</style>
