<template>
  <div>
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      <p class="mt-4 text-gray-600">Loading podcast...</p>
    </div>

    <div v-else-if="podcast" class="space-y-6">
      <!-- Header -->
      <div class="card">
        <div class="flex items-start gap-6">
          <!-- Podcast Image -->
          <div class="flex-shrink-0">
            <div class="w-48 h-48 bg-gray-200 rounded-lg overflow-hidden">
              <img
                v-if="podcast.image_url"
                :src="podcast.image_url"
                :alt="podcast.title"
                class="w-full h-full object-cover"
              />
            </div>
          </div>

          <!-- Podcast Info -->
          <div class="flex-1">
            <div class="flex items-start justify-between">
              <div>
                <h1 class="text-3xl font-bold text-gray-900">{{ podcast.title }}</h1>
                <p v-if="podcast.author" class="text-lg text-gray-600 mt-1">{{ podcast.author }}</p>
              </div>
              <router-link to="/" class="btn btn-secondary">
                ← Back
              </router-link>
            </div>

            <div
              v-if="podcast.description"
              class="mt-4 text-gray-700 line-clamp-3 podcast-description"
              v-html="podcast.description"
            ></div>

            <!-- Stats & Settings -->
            <div class="mt-6 flex flex-wrap gap-4">
              <div class="flex items-center gap-2">
                <span class="text-sm text-gray-500">Episodes:</span>
                <span class="font-semibold">{{ podcast.max_episodes_to_keep }}</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-sm text-gray-500">Auto-download:</span>
                <span :class="podcast.auto_download ? 'text-green-600' : 'text-gray-400'">
                  {{ podcast.auto_download ? '✓ Enabled' : '✗ Disabled' }}
                </span>
              </div>
              <div v-if="podcast.last_checked" class="flex items-center gap-2">
                <span class="text-sm text-gray-500">Last checked:</span>
                <span>{{ formatDate(podcast.last_checked) }}</span>
              </div>
            </div>

            <!-- Actions -->
            <div class="mt-6 flex gap-3">
              <button @click="refreshPodcast" class="btn btn-primary" :disabled="refreshing">
                {{ refreshing ? 'Refreshing...' : '↻ Refresh Feed' }}
              </button>
              <button @click="showSettings = true" class="btn btn-secondary">
                ⚙ Settings
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Episodes List -->
      <div class="card">
        <h2 class="text-xl font-bold mb-4">Episodes ({{ podcast.episodes?.length || 0 }})</h2>

        <div v-if="!podcast.episodes || podcast.episodes.length === 0" class="text-center py-8 text-gray-500">
          No episodes found. Try refreshing the feed.
        </div>

        <div v-else class="space-y-3">
          <EpisodeItem
            v-for="episode in podcast.episodes"
            :key="episode.id"
            :episode="episode"
            @download="handleDownload"
          />
        </div>
      </div>

      <!-- Settings Modal -->
      <div v-if="showSettings" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="card max-w-md w-full mx-4">
          <h3 class="text-xl font-bold mb-4">Podcast Settings</h3>

          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Episodes to Keep
              </label>
              <input
                v-model.number="settingsForm.max_episodes_to_keep"
                type="number"
                min="1"
                max="100"
                class="input"
              />
            </div>

            <div class="flex items-center">
              <input
                v-model="settingsForm.auto_download"
                type="checkbox"
                id="auto-download"
                class="w-4 h-4 text-blue-600"
              />
              <label for="auto-download" class="ml-2 text-sm text-gray-700">
                Automatically download new episodes
              </label>
            </div>
          </div>

          <div class="mt-6 flex gap-3 justify-end">
            <button @click="showSettings = false" class="btn btn-secondary">
              Cancel
            </button>
            <button @click="saveSettings" class="btn btn-primary">
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { usePodcastStore } from '../stores/podcast'
import { downloads } from '../services/api'
import EpisodeItem from '../components/EpisodeItem.vue'

const route = useRoute()
const podcastStore = usePodcastStore()

const podcast = ref(null)
const loading = ref(true)
const refreshing = ref(false)
const showSettings = ref(false)

const settingsForm = reactive({
  max_episodes_to_keep: 3,
  auto_download: true,
})

onMounted(async () => {
  await loadPodcast()
})

async function loadPodcast() {
  try {
    podcast.value = await podcastStore.fetchPodcastWithEpisodes(route.params.id)
    settingsForm.max_episodes_to_keep = podcast.value.max_episodes_to_keep
    settingsForm.auto_download = podcast.value.auto_download
  } catch (err) {
    console.error('Error loading podcast:', err)
  } finally {
    loading.value = false
  }
}

async function refreshPodcast() {
  refreshing.value = true
  try {
    await podcastStore.refreshPodcast(route.params.id)
    await loadPodcast()
    alert('Podcast refreshed!')
  } catch (err) {
    alert('Failed to refresh podcast')
  } finally {
    refreshing.value = false
  }
}

async function saveSettings() {
  try {
    await podcastStore.updatePodcast(route.params.id, settingsForm)
    podcast.value.max_episodes_to_keep = settingsForm.max_episodes_to_keep
    podcast.value.auto_download = settingsForm.auto_download
    showSettings.value = false
    alert('Settings updated!')
  } catch (err) {
    alert('Failed to update settings')
  }
}

async function handleDownload(episodeId) {
  try {
    await downloads.queue(episodeId)
    alert('Episode queued for download!')
  } catch (err) {
    // Extract error message from API response
    let errorMessage = 'Failed to queue download'

    if (err.response?.data?.detail) {
      errorMessage = err.response.data.detail
    } else if (err.response?.status === 507) {
      errorMessage = 'Insufficient disk space. Please free up storage and try again.'
    } else if (err.response?.status === 404) {
      errorMessage = 'Episode not found.'
    } else if (err.message) {
      errorMessage = `Error: ${err.message}`
    }

    alert(errorMessage)
    console.error('Download queue error:', err)
  }
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString()
}
</script>

<style scoped>
.podcast-description :deep(a) {
  @apply text-blue-600 hover:underline;
}

.podcast-description :deep(strong),
.podcast-description :deep(b) {
  @apply font-semibold;
}

.podcast-description :deep(em),
.podcast-description :deep(i) {
  @apply italic;
}

.podcast-description :deep(ul),
.podcast-description :deep(ol) {
  @apply ml-4;
}

.podcast-description :deep(li) {
  @apply list-disc;
}
</style>
