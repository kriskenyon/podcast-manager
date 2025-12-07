<template>
  <div class="card hover:shadow-lg transition-shadow cursor-pointer">
    <router-link :to="`/podcast/${podcast.id}`">
      <!-- Podcast Image -->
      <div class="aspect-square w-full mb-4 bg-gray-200 rounded-lg overflow-hidden">
        <img
          v-if="podcast.image_url"
          :src="podcast.image_url"
          :alt="podcast.title"
          class="w-full h-full object-cover"
        />
        <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
          <svg class="h-20 w-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
          </svg>
        </div>
      </div>

      <!-- Podcast Info -->
      <h3 class="text-lg font-semibold text-gray-900 truncate">{{ podcast.title }}</h3>
      <p v-if="podcast.author" class="text-sm text-gray-600 truncate">{{ podcast.author }}</p>
    </router-link>

    <!-- Stats -->
    <div class="mt-3 flex items-center justify-between text-sm text-gray-500">
      <span>{{ podcast.max_episodes_to_keep }} episodes</span>
      <span v-if="podcast.auto_download" class="text-green-600">● Auto</span>
    </div>

    <!-- Actions -->
    <div class="mt-4 flex gap-2">
      <button
        @click.stop="$emit('refresh', podcast.id)"
        class="flex-1 btn btn-secondary text-sm"
        title="Refresh feed"
      >
        ↻ Refresh
      </button>
      <button
        @click.stop="$emit('delete', podcast.id)"
        class="btn btn-danger text-sm"
        title="Delete podcast"
      >
        ×
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  podcast: {
    type: Object,
    required: true,
  },
})

defineEmits(['refresh', 'delete'])
</script>
