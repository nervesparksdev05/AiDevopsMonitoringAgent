# Metrics Observability Frontend

Modern React dashboard for real-time metrics monitoring, anomaly detection, and RCA visualization.

## Tech Stack

- **React 18** - UI library
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **JavaScript** - No TypeScript

## Features

- 📊 **Dashboard** - Real-time stats and system health
- 🚨 **Anomalies** - View and filter detected anomalies
- 🔍 **RCA Results** - AI-powered root cause analysis
- 📈 **Metrics** - Raw Prometheus metrics data
- 🎨 **Modern UI** - Dark theme with glassmorphism
- 🔄 **Auto-refresh** - Live data updates

## Setup

### Install Dependencies

```bash
cd frontend
npm install
```

### Start Development Server

```bash
npm run dev
```

Frontend will run on: **http://localhost:5173**

### Build for Production

```bash
npm run build
```

## Configuration

The frontend connects to the FastAPI backend at:
```javascript
API_BASE_URL = 'http://localhost:8081'
```

To change this, edit `src/services/api.js`.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard.jsx      # Stats and system health
│   │   ├── Anomalies.jsx      # Anomalies list with filters
│   │   ├── RCAResults.jsx     # RCA results display
│   │   └── Metrics.jsx        # Metrics table
│   ├── services/
│   │   └── api.js             # API client
│   ├── App.jsx                # Main app with navigation
│   ├── index.css              # Tailwind CSS
│   └── main.jsx               # Entry point
├── tailwind.config.js         # Tailwind configuration
├── postcss.config.js          # PostCSS configuration
└── package.json               # Dependencies
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

## API Endpoints Used

- `GET /stats` - System statistics
- `GET /anomalies` - List anomalies
- `GET /rca` - List RCA results
- `GET /prom-metrics` - Prometheus metrics

## Screenshots

### Dashboard
Real-time stats with system health indicators

### Anomalies
Filterable list with severity badges and AI analysis

### RCA Results
Root cause analysis with recommended actions

### Metrics
Tabular view of raw Prometheus data

## Development

### Hot Module Replacement (HMR)
Vite provides instant feedback during development.

### Tailwind CSS
All styles use Tailwind utility classes for consistency.

### Component Structure
- Each page is a separate component
- API calls are centralized in `services/api.js`
- Reusable UI patterns (cards, badges, etc.)

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
