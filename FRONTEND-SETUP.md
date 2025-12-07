# Vue Frontend Setup Guide

## 🎨 Modern Vue 3 Frontend for Podcast Manager

A beautiful, responsive web interface built with Vue 3, Vite, and Tailwind CSS.

## Features

✅ **Podcast Management** - View, add, edit, and delete podcasts
✅ **Episode Browsing** - View all episodes for each podcast
✅ **Download Monitoring** - Real-time download progress tracking
✅ **Background Jobs** - Monitor and control scheduled tasks
✅ **Responsive Design** - Works on desktop, tablet, and mobile
✅ **Auto-refresh** - Optional auto-refresh for downloads
✅ **Modern UI** - Clean, intuitive interface with Tailwind CSS

## Prerequisites

- Node.js 18+ and npm/yarn
- Running backend server (see main README.md)

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

This will install:
- Vue 3
- Vite
- Vue Router
- Pinia (state management)
- Axios (HTTP client)
- Tailwind CSS

### 2. Start Development Server

```bash
npm run dev
```

The frontend will start on **http://localhost:5173**

The Vite dev server is configured to proxy API requests to the backend at `http://localhost:8000`

### 3. Build for Production

```bash
npm run build
```

Built files will be in `dist/` directory.

### 4. Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable Vue components
│   │   ├── PodcastCard.vue     # Podcast card display
│   │   ├── EpisodeItem.vue     # Episode list item
│   │   └── DownloadItem.vue    # Download status item
│   ├── views/               # Page components
│   │   ├── HomeView.vue        # Podcast list page
│   │   ├── PodcastDetailView.vue   # Podcast detail page
│   │   ├── AddPodcastView.vue  # Add podcast form
│   │   ├── DownloadsView.vue   # Downloads monitor
│   │   └── JobsView.vue        # Background jobs
│   ├── services/            # API services
│   │   └── api.js              # API client configuration
│   ├── stores/              # Pinia stores
│   │   └── podcast.js          # Podcast state management
│   ├── router/              # Vue Router
│   │   └── index.js            # Route definitions
│   ├── App.vue              # Root component
│   ├── main.js              # App entry point
│   └── style.css            # Global styles + Tailwind
├── index.html               # HTML template
├── package.json             # Dependencies
├── vite.config.js           # Vite configuration
├── tailwind.config.js       # Tailwind configuration
└── postcss.config.js        # PostCSS configuration
```

## Pages & Features

### Home Page (`/`)
- Grid view of all podcasts
- Podcast cards with artwork
- Quick actions: Refresh, Delete
- Add podcast button
- Empty state for new users

### Podcast Detail (`/podcast/:id`)
- Full podcast information
- All episodes list
- Download individual episodes
- Edit podcast settings (episode limit, auto-download)
- Refresh feed button

### Add Podcast (`/add-podcast`)
- RSS feed URL input
- Configure episodes to keep
- Toggle auto-download
- Example podcasts for quick start

### Downloads (`/downloads`)
- Filter by status (All, Pending, Downloading, Completed, Failed)
- Real-time progress bars
- Auto-refresh toggle
- Process queue button
- Retry failed downloads

### Jobs (`/jobs`)
- View all scheduled jobs
- Manually trigger jobs
- Pause/resume jobs
- Next run times

## API Integration

The frontend communicates with the backend via the `/api` proxy:

```javascript
// All API calls are proxied to http://localhost:8000
// Example: /api/podcasts → http://localhost:8000/api/podcasts
```

### API Service (`src/services/api.js`)

Provides organized access to all backend endpoints:

```javascript
import { podcasts, episodes, downloads, jobs } from '@/services/api'

// Get all podcasts
const response = await podcasts.getAll()

// Add a podcast
await podcasts.create({ rss_url: 'https://...', max_episodes_to_keep: 3 })

// Queue a download
await downloads.queue(episodeId)

// Trigger a job
await jobs.trigger('refresh_podcasts')
```

## State Management

Uses Pinia for state management:

```javascript
import { usePodcastStore } from '@/stores/podcast'

const podcastStore = usePodcastStore()

// Fetch podcasts
await podcastStore.fetchPodcasts()

// Add podcast
await podcastStore.addPodcast(rssUrl, maxEpisodes, autoDownload)

// Access state
console.log(podcastStore.podcastList)
console.log(podcastStore.totalPodcasts)
```

## Styling

Built with Tailwind CSS utility classes:

### Custom Components (in `style.css`)

```css
.btn - Base button class
.btn-primary - Primary blue button
.btn-secondary - Secondary gray button
.btn-danger - Red danger button
.card - White card with shadow
.input - Form input styling
```

### Responsive Design

All pages are fully responsive:
- Mobile: Single column
- Tablet: 2 columns
- Desktop: 3 columns (podcasts grid)

## Development Tips

### Hot Module Replacement (HMR)

Vite provides instant HMR - changes appear immediately without page reload.

### Browser DevTools

Install Vue DevTools browser extension for easier debugging:
- Inspect component state
- View Pinia store data
- Track router navigation

### API Proxy Configuration

Edit `vite.config.js` to change backend URL:

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',  // Change this
      changeOrigin: true,
    }
  }
}
```

## Customization

### Change Theme Colors

Edit `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      primary: '#your-color',
    }
  }
}
```

### Add New Routes

Edit `src/router/index.js`:

```javascript
{
  path: '/settings',
  name: 'settings',
  component: () => import('../views/SettingsView.vue'),
}
```

### Add New API Endpoints

Edit `src/services/api.js`:

```javascript
export const settings = {
  get: () => api.get('/settings'),
  update: (data) => api.put('/settings', data),
}
```

## Production Deployment

### Build

```bash
npm run build
```

### Serve with Backend

The built frontend can be served by the FastAPI backend:

1. Build the frontend: `npm run build`
2. The backend is already configured to serve static files from `frontend/static`
3. Update backend to serve the built Vue app

Or serve separately with nginx, Apache, etc.

### Environment Variables

Create `.env.production` for production settings:

```bash
VITE_API_URL=https://your-api-domain.com
```

Use in code:

```javascript
const apiUrl = import.meta.env.VITE_API_URL || '/api'
```

## Troubleshooting

### Backend Connection Issues

**Problem**: API calls fail with network errors

**Solution**:
- Ensure backend is running on `http://localhost:8000`
- Check `vite.config.js` proxy configuration
- Verify CORS is enabled on backend

### Blank Page

**Problem**: Page loads but shows nothing

**Solution**:
- Check browser console for errors
- Verify all dependencies are installed: `npm install`
- Clear browser cache and restart dev server

### Styles Not Loading

**Problem**: Page has no styling

**Solution**:
- Ensure Tailwind is imported in `src/style.css`
- Check `postcss.config.js` and `tailwind.config.js` exist
- Restart dev server

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile browsers: iOS Safari 13+, Chrome Android

## Performance

- **Code Splitting**: Routes are lazy-loaded
- **Tree Shaking**: Unused code is eliminated
- **Optimized Build**: Minified and compressed
- **Fast Refresh**: HMR for instant updates

## Next Steps

Possible enhancements:

- [ ] Apple Podcast search integration
- [ ] OPML import/export UI
- [ ] User authentication
- [ ] Dark mode
- [ ] Advanced filtering and search
- [ ] Keyboard shortcuts
- [ ] Drag & drop for podcast organization
- [ ] PWA support for offline access

## Resources

- [Vue 3 Documentation](https://vuejs.org/)
- [Vite Documentation](https://vitejs.dev/)
- [Vue Router Documentation](https://router.vuejs.org/)
- [Pinia Documentation](https://pinia.vuejs.org/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)

## Support

For issues or questions:
- Check the browser console for errors
- Review the backend API docs at `http://localhost:8000/docs`
- Check network tab for failed API requests

Enjoy your beautiful podcast manager interface! 🎨
