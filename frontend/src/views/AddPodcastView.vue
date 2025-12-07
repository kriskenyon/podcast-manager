<template>
  <div class="max-w-2xl mx-auto">
    <div class="card">
      <h1 class="text-2xl font-bold mb-6">Add New Podcast</h1>

      <form @submit.prevent="handleSubmit" class="space-y-6">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            RSS Feed URL
          </label>
          <input
            v-model="form.rssUrl"
            type="url"
            required
            placeholder="https://feeds.example.com/podcast.rss"
            class="input"
          />
          <p class="mt-1 text-sm text-gray-500">
            Enter the RSS feed URL of the podcast you want to add
          </p>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Episodes to Keep
          </label>
          <input
            v-model.number="form.maxEpisodes"
            type="number"
            min="1"
            max="100"
            required
            class="input"
          />
          <p class="mt-1 text-sm text-gray-500">
            Number of most recent episodes to keep (1-100)
          </p>
        </div>

        <div class="flex items-center">
          <input
            v-model="form.autoDownload"
            type="checkbox"
            id="auto-download-add"
            class="w-4 h-4 text-blue-600"
          />
          <label for="auto-download-add" class="ml-2 text-sm text-gray-700">
            Automatically download new episodes
          </label>
        </div>

        <div v-if="error" class="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p class="text-red-800">{{ error }}</p>
        </div>

        <div class="flex gap-3">
          <button
            type="submit"
            :disabled="loading"
            class="btn btn-primary flex-1"
          >
            {{ loading ? 'Adding Podcast...' : 'Add Podcast' }}
          </button>
          <router-link to="/" class="btn btn-secondary">
            Cancel
          </router-link>
        </div>
      </form>

      <!-- Popular Podcasts (Example) -->
      <div class="mt-8 pt-8 border-t">
        <h2 class="text-lg font-semibold mb-4">Popular Podcasts</h2>
        <div class="space-y-2">
          <div
            v-for="example in examplePodcasts"
            :key="example.url"
            class="flex items-center justify-between p-3 border rounded hover:bg-gray-50 cursor-pointer"
            @click="form.rssUrl = example.url"
          >
            <div>
              <p class="font-medium">{{ example.name }}</p>
              <p class="text-sm text-gray-500">{{ example.category }}</p>
            </div>
            <button
              type="button"
              class="text-blue-600 hover:text-blue-700 text-sm font-medium"
            >
              Use →
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { usePodcastStore } from '../stores/podcast'

const router = useRouter()
const podcastStore = usePodcastStore()

const form = reactive({
  rssUrl: '',
  maxEpisodes: 3,
  autoDownload: true,
})

const loading = ref(false)
const error = ref(null)

const examplePodcasts = [
  { name: 'The Daily (NY Times)', url: 'https://feeds.simplecast.com/54nAGcIl', category: 'News' },
  { name: 'Radiolab', url: 'https://feeds.wnyc.org/radiolab', category: 'Science' },
  { name: 'Reply All', url: 'https://feeds.gimletmedia.com/hearreplyall', category: 'Technology' },
]

async function handleSubmit() {
  loading.value = true
  error.value = null

  try {
    await podcastStore.addPodcast(
      form.rssUrl,
      form.maxEpisodes,
      form.autoDownload
    )
    router.push('/')
  } catch (err) {
    error.value = err.message || 'Failed to add podcast. Please check the RSS URL and try again.'
  } finally {
    loading.value = false
  }
}
</script>
