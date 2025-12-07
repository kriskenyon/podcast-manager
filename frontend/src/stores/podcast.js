import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { podcasts, downloads } from '../services/api'

export const usePodcastStore = defineStore('podcast', () => {
  const podcastList = ref([])
  const currentPodcast = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const totalPodcasts = computed(() => podcastList.value.length)

  async function fetchPodcasts() {
    loading.value = true
    error.value = null
    try {
      const response = await podcasts.getAll()
      podcastList.value = response.data.podcasts
    } catch (err) {
      error.value = err.message
      console.error('Error fetching podcasts:', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchPodcastWithEpisodes(id) {
    loading.value = true
    error.value = null
    try {
      const response = await podcasts.getWithEpisodes(id)
      currentPodcast.value = response.data
      return response.data
    } catch (err) {
      error.value = err.message
      console.error('Error fetching podcast:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function addPodcast(rssUrl, maxEpisodes = 3, autoDownload = true) {
    loading.value = true
    error.value = null
    try {
      const response = await podcasts.create({
        rss_url: rssUrl,
        max_episodes_to_keep: maxEpisodes,
        auto_download: autoDownload,
      })
      podcastList.value.push(response.data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      console.error('Error adding podcast:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deletePodcast(id) {
    loading.value = true
    error.value = null
    try {
      await podcasts.delete(id)
      podcastList.value = podcastList.value.filter((p) => p.id !== id)
    } catch (err) {
      error.value = err.message
      console.error('Error deleting podcast:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function refreshPodcast(id) {
    loading.value = true
    error.value = null
    try {
      await podcasts.refresh(id)
      // Refresh the podcast list
      await fetchPodcasts()
    } catch (err) {
      error.value = err.message
      console.error('Error refreshing podcast:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updatePodcast(id, data) {
    loading.value = true
    error.value = null
    try {
      const response = await podcasts.update(id, data)
      const index = podcastList.value.findIndex((p) => p.id === id)
      if (index !== -1) {
        podcastList.value[index] = response.data
      }
      if (currentPodcast.value?.id === id) {
        currentPodcast.value = { ...currentPodcast.value, ...response.data }
      }
      return response.data
    } catch (err) {
      error.value = err.message
      console.error('Error updating podcast:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    podcastList,
    currentPodcast,
    loading,
    error,
    totalPodcasts,
    fetchPodcasts,
    fetchPodcastWithEpisodes,
    addPodcast,
    deletePodcast,
    refreshPodcast,
    updatePodcast,
  }
})
