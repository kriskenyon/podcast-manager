<template>
  <div class="max-w-4xl mx-auto">
    <div class="card">
      <h1 class="text-2xl font-bold mb-6">OPML Import/Export</h1>

      <div class="grid md:grid-cols-2 gap-6">
        <!-- Import Section -->
        <div class="border-r pr-6">
          <h2 class="text-xl font-semibold mb-4">Import Podcasts</h2>
          <p class="text-gray-600 mb-4">
            Upload an OPML file to import podcast subscriptions from another app.
          </p>

          <form @submit.prevent="handleImport" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                OPML File
              </label>
              <input
                type="file"
                accept=".opml,.xml"
                @change="handleFileSelect"
                class="block w-full text-sm text-gray-500
                  file:mr-4 file:py-2 file:px-4
                  file:rounded file:border-0
                  file:text-sm file:font-semibold
                  file:bg-blue-50 file:text-blue-700
                  hover:file:bg-blue-100"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Episodes to Keep
              </label>
              <input
                v-model.number="importSettings.maxEpisodes"
                type="number"
                min="1"
                max="100"
                class="input"
              />
              <p class="mt-1 text-sm text-gray-500">
                Default for all imported podcasts
              </p>
            </div>

            <div class="flex items-center">
              <input
                v-model="importSettings.autoDownload"
                type="checkbox"
                id="auto-download-import"
                class="w-4 h-4 text-blue-600"
              />
              <label for="auto-download-import" class="ml-2 text-sm text-gray-700">
                Auto-download new episodes
              </label>
            </div>

            <button
              type="button"
              @click="previewOPML"
              :disabled="!selectedFile || parsing"
              class="btn btn-secondary w-full"
            >
              {{ parsing ? 'Parsing...' : 'Preview Podcasts' }}
            </button>

            <button
              type="submit"
              :disabled="!selectedFile || importing"
              class="btn btn-primary w-full"
            >
              {{ importing ? 'Importing...' : 'Import All Podcasts' }}
            </button>
          </form>

          <div v-if="importError" class="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p class="text-red-800">{{ importError }}</p>
          </div>

          <div v-if="importSuccess" class="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <p class="text-green-800">{{ importSuccess }}</p>
          </div>
        </div>

        <!-- Export Section -->
        <div class="pl-6">
          <h2 class="text-xl font-semibold mb-4">Export Podcasts</h2>
          <p class="text-gray-600 mb-4">
            Download your current podcast subscriptions as an OPML file.
          </p>

          <div class="space-y-4">
            <div class="p-4 bg-gray-50 rounded-lg">
              <p class="text-sm text-gray-600">
                This will export all your current subscriptions in OPML format,
                which can be imported into other podcast applications like:
              </p>
              <ul class="mt-2 text-sm text-gray-600 list-disc list-inside">
                <li>Apple Podcasts</li>
                <li>Overcast</li>
                <li>Pocket Casts</li>
                <li>And many more...</li>
              </ul>
            </div>

            <button
              @click="handleExport"
              :disabled="exporting"
              class="btn btn-primary w-full"
            >
              {{ exporting ? 'Exporting...' : 'Download OPML File' }}
            </button>

            <div v-if="exportError" class="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p class="text-red-800">{{ exportError }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Preview Section -->
      <div v-if="previewPodcasts.length > 0" class="mt-8 pt-8 border-t">
        <h2 class="text-xl font-semibold mb-4">
          Preview: {{ previewPodcasts.length }} Podcasts Found
        </h2>
        <div class="max-h-96 overflow-y-auto space-y-2">
          <div
            v-for="podcast in previewPodcasts"
            :key="podcast.rss_url"
            class="p-3 border rounded hover:bg-gray-50"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <p class="font-medium">{{ podcast.title }}</p>
                <p v-if="podcast.description" class="text-sm text-gray-500 mt-1">
                  {{ podcast.description.substring(0, 100) }}{{ podcast.description.length > 100 ? '...' : '' }}
                </p>
                <p class="text-xs text-gray-400 mt-1">{{ podcast.rss_url }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const selectedFile = ref(null)
const parsing = ref(false)
const importing = ref(false)
const exporting = ref(false)
const importError = ref(null)
const importSuccess = ref(null)
const exportError = ref(null)
const previewPodcasts = ref([])

const importSettings = ref({
  maxEpisodes: 3,
  autoDownload: true,
})

function handleFileSelect(event) {
  selectedFile.value = event.target.files[0]
  previewPodcasts.value = []
  importError.value = null
  importSuccess.value = null
}

async function previewOPML() {
  if (!selectedFile.value) return

  parsing.value = true
  importError.value = null

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)

    const response = await axios.post('/api/opml/parse', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    previewPodcasts.value = response.data.podcasts
  } catch (err) {
    importError.value = err.response?.data?.detail || 'Failed to parse OPML file'
    previewPodcasts.value = []
  } finally {
    parsing.value = false
  }
}

async function handleImport() {
  if (!selectedFile.value) return

  importing.value = true
  importError.value = null
  importSuccess.value = null

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)

    const response = await axios.post(
      `/api/opml/import?max_episodes_to_keep=${importSettings.value.maxEpisodes}&auto_download=${importSettings.value.autoDownload}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )

    importSuccess.value = response.data.message
    selectedFile.value = null
    previewPodcasts.value = []

    // Clear file input
    const fileInput = document.querySelector('input[type="file"]')
    if (fileInput) fileInput.value = ''

  } catch (err) {
    importError.value = err.response?.data?.detail || 'Failed to import podcasts from OPML file'
  } finally {
    importing.value = false
  }
}

async function handleExport() {
  exporting.value = true
  exportError.value = null

  try {
    const response = await axios.get('/api/opml/export', {
      responseType: 'blob',
    })

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'podcast_subscriptions.opml')
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)

  } catch (err) {
    exportError.value = 'Failed to export podcasts to OPML file'
  } finally {
    exporting.value = false
  }
}
</script>
