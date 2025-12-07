<template>
  <div>
    <div class="px-4 sm:px-0">
      <h2 class="text-2xl font-bold text-gray-900 mb-6">Your Podcasts</h2>

      <!-- Loading State -->
      <div v-if="loading" class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <p class="mt-4 text-gray-600">Loading podcasts...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="card bg-red-50 border border-red-200 text-red-800">
        <p>Error loading podcasts: {{ error }}</p>
        <button @click="loadPodcasts" class="btn btn-primary mt-4">Retry</button>
      </div>

      <!-- Empty State -->
      <div v-else-if="podcastList.length === 0" class="text-center py-12">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">No podcasts</h3>
        <p class="mt-1 text-sm text-gray-500">Get started by adding a new podcast.</p>
        <div class="mt-6">
          <router-link to="/add-podcast" class="btn btn-primary">
            + Add Your First Podcast
          </router-link>
        </div>
      </div>

      <!-- Podcast Grid -->
      <div v-else class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <PodcastCard
          v-for="podcast in podcastList"
          :key="podcast.id"
          :podcast="podcast"
          @refresh="handleRefresh"
          @delete="handleDelete"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { usePodcastStore } from '../stores/podcast'
import PodcastCard from '../components/PodcastCard.vue'

const podcastStore = usePodcastStore()
const { podcastList, loading, error } = podcastStore

onMounted(() => {
  loadPodcasts()
})

async function loadPodcasts() {
  await podcastStore.fetchPodcasts()
}

async function handleRefresh(id) {
  try {
    await podcastStore.refreshPodcast(id)
    alert('Podcast refreshed successfully!')
  } catch (err) {
    alert('Failed to refresh podcast')
  }
}

async function handleDelete(id) {
  if (confirm('Are you sure you want to delete this podcast?')) {
    try {
      await podcastStore.deletePodcast(id)
    } catch (err) {
      alert('Failed to delete podcast')
    }
  }
}
</script>
