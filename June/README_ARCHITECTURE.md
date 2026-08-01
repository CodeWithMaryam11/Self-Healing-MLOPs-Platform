# PipelineIQ - Frontend Architectural Blueprint

## 1. Production Folder Hierarchy

PipelineIQ adopts a domain-driven, layer-isolated architecture tailored for high-scale MLOps telemetry and complex model lifecycle monitoring.

```text
src/
├── assets/                  # Static assets (fonts, industrial icons, logos)
├── components/              # Reusable UI presentation layers & complex widgets
│   ├── common/              # Minimalist industrial primitives (Button, Card, Badge, Table)
│   ├── ProtectedRoute.jsx   # Auth guard HOC intercepting unauthenticated traffic
│   ├── TrainingSetup.jsx    # Module 3: Multipart dataset upload & multi-model execution
│   └── DriftMonitor.jsx     # Module 5: Evidently AI drift feed & self-healing indicator
├── hooks/                   # Custom domain hooks & query wrappers
│   ├── useRunsQuery.js      # Live polling wrapper for MLflow model runs
│   ├── useDriftQuery.js     # Polling wrapper for Evidently AI telemetry
│   └── useHealthQuery.js    # Global backend & PostgreSQL health strip hook
├── services/                # Infrastructure & Network access layer
│   └── api.js               # Module 2: Axios client with JWT Bearer & demo simulation mode
├── stores/                  # Global client state management
│   └── useAuthStore.js      # Module 2: Zustand auth store (Tokens, User session, Logout)
├── views/                   # Top-level page containers & route layouts
│   ├── Login.jsx            # Module 2: Minimalist industrial login interface
│   └── DashboardOverview.jsx# Module 4: Real-time MLflow registry & system overview
├── types/                   # TypeScript / JSDoc schema definitions
├── utils/                   # Helper utilities (formatting, chart scales, calculations)
├── App.jsx                  # Root router & TanStack QueryClient provider setup
├── index.css                # Minimalist design system tokens & Tailwind CSS imports
└── main.jsx                 # Application DOM entry point
```

---

## 2. Server-State Synchronization & Polling Strategy

PipelineIQ relies on **TanStack Query (React Query)** to bridge the gap between our fully custom asynchronous FastAPI backend and the reactive React UI.

### A. Query Key Factory Pattern
To ensure atomic cache invalidation and prevent stale cache collisions across datasets and model runs, all queries strictly adhere to hierarchical tuple query keys:
* `['health']`: System telemetry (API status, PostgreSQL connectivity).
* `['runs', { datasetId, status }]`: MLflow concurrent training runs filtered by active state.
* `['drift', { pipelineId }]`: Statistical Kolmogorov-Smirnov & PSI drift calculations.

### B. Automated Live Polling Lifecycle
In MLOps environments, training models (Random Forest, XGBoost, LightGBM) run asynchronously on background worker threads. Instead of forcing manual browser refreshes or maintaining fragile WebSockets for simple status pings, we implement **deterministic polling** via `refetchInterval`:

```javascript
const { data, isRefetching } = useQuery({
  queryKey: ['runs', 'live'],
  queryFn: () => api.get('/runs').then(res => res.data),
  refetchInterval: 5000, // 5-second deterministic heartbeat
  refetchIntervalInBackground: true, // Maintain telemetry while operator switches tabs
  staleTime: 4000, // Mark data stale right before next tick
  gcTime: 1000 * 60 * 15, // Retain inactive run logs in memory for 15 minutes
});
```

### C. Optimistic Cache Updates on Training Trigger
When an operator submits a new dataset via `TrainingSetup.jsx`, TanStack Query's `useMutation` immediately injects a temporary "placeholder" run into the `['runs', 'live']` cache. This provides zero-latency UI feedback (yellow `Training...` badge) before the FastAPI server finishes parsing the multipart payload.

### D. Intelligent Backoff & Self-Healing Sync
If backend endpoints experience temporary latency spikes during heavy feature engineering (e.g., SMOTE generation), React Query's `retryDelay` applies exponential backoff (`Math.min(1000 * 2 ** attemptIndex, 30000)`). Once retraining completes autonomously, the cache automatically synchronizes state, triggering UI transitions without component remounting.
