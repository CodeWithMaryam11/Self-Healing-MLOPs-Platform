import axios from 'axios';
import { useAuthStore } from '../stores/useAuthStore';

// Default FastAPI server base URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ==========================================
// REQUEST INTERCEPTOR: JWT TOKEN INJECTION
// ==========================================
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token || localStorage.getItem('pipelineiq_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ==========================================
// MOCK / SIMULATION ENGINE FOR STANDALONE DEMO
// ==========================================
let mockRuns = [
  {
    id: 'run_89a1bf',
    dataset: 'ibm_hr_attrition_v1.csv',
    models: ['Random Forest', 'XGBoost', 'LightGBM'],
    hyperparameters: { n_estimators: 250, max_depth: 12, smote_ratio: 1.0 },
    status: 'Completed',
    targetMetric: 'F1-Score',
    score: 0.964,
    accuracy: 0.958,
    f1_score: 0.964,
    best_model: 'XGBoost',
    model_scores: {
      'Random Forest': { accuracy: 0.945, f1_score: 0.942 },
      'XGBoost':       { accuracy: 0.958, f1_score: 0.964 },
      'LightGBM':      { accuracy: 0.889, f1_score: 0.882 },
    },
    timestamp: '12 mins ago',
  },
  {
    id: 'run_33c90e',
    dataset: 'ibm_hr_attrition_batch2.csv',
    models: ['LightGBM', 'XGBoost'],
    hyperparameters: { learning_rate: 0.03, num_leaves: 31, smote_ratio: 1.0 },
    status: 'Completed',
    targetMetric: 'Accuracy',
    score: 0.912,
    accuracy: 0.912,
    f1_score: 0.908,
    best_model: 'XGBoost',
    model_scores: {
      'LightGBM': { accuracy: 0.889, f1_score: 0.882 },
      'XGBoost':  { accuracy: 0.912, f1_score: 0.908 },
    },
    timestamp: '45 mins ago',
  }
];

// ---- DRIFT STATE MACHINE ----
let driftState = {
  isDrifted: false,
  currentPsi: 0.08,
  currentKs: 0.45,
  retrainingStartTime: null,
  selectedRunId: null,      // which run the drift was injected against
  selectedRunLabel: null,   // human-readable label for the run
};
const HEALING_DURATION_S = 15;

let mockDriftHistory = [
  { time: '10:00', psi: 0.06, ks_pvalue: 0.52 },
  { time: '10:05', psi: 0.07, ks_pvalue: 0.48 },
  { time: '10:10', psi: 0.08, ks_pvalue: 0.45 },
  { time: '10:15', psi: 0.07, ks_pvalue: 0.47 },
  { time: '10:20', psi: 0.08, ks_pvalue: 0.42 },
];

// Helper to resolve URL path from full/relative URL
function matchPath(url, path) {
  if (!url) return false;
  // Handle both full URL and relative path
  const urlLower = url.toLowerCase();
  const pathLower = path.toLowerCase();
  return urlLower.endsWith(pathLower) || urlLower.includes(pathLower + '?') || urlLower.includes(pathLower + '&');
}

if (USE_MOCK) {
  api.defaults.adapter = async (config) => {
    await new Promise((res) => setTimeout(res, 250));

    const { url, method, data } = config;

    // POST /auth/login
    if (matchPath(url, '/auth/login') && method === 'post') {
      const parsed = typeof data === 'string' ? JSON.parse(data || '{}') : data;
      if (parsed.email && parsed.password) {
        return {
          data: {
            token: 'mock_jwt_token_fastapi_secret_99812',
            user: { email: parsed.email, name: 'Principal MLOps Architect', role: 'Admin' },
          },
          status: 200, statusText: 'OK', headers: {}, config,
        };
      }
      return Promise.reject({ response: { status: 401, data: { detail: 'Invalid credentials' } } });
    }

    // GET /health
    if (matchPath(url, '/health') && method === 'get') {
      return {
        data: {
          status: 'Online',
          database: 'Connected (PostgreSQL / SMOTE Engine)',
          mlflow_registry: 'Active (v2.11.0)',
          evidently_engine: 'Ready',
        },
        status: 200, statusText: 'OK', headers: {}, config,
      };
    }

    // GET /runs
    if (matchPath(url, '/runs') && method === 'get') {
      mockRuns = mockRuns.map((r) => {
        if (r.status === 'Training...' && Math.random() > 0.35) {
          // Engine evaluates all 3 models and picks the best
          const rfAcc = Number((0.89 + Math.random() * 0.07).toFixed(3));
          const rfF1  = Number((rfAcc + (Math.random() - 0.5) * 0.01).toFixed(3));
          const xgAcc = Number((0.89 + Math.random() * 0.07).toFixed(3));
          const xgF1  = Number((xgAcc + (Math.random() - 0.5) * 0.01).toFixed(3));
          const lgAcc = Number((0.89 + Math.random() * 0.07).toFixed(3));
          const lgF1  = Number((lgAcc + (Math.random() - 0.5) * 0.01).toFixed(3));
          const scores = {
            'Random Forest': { accuracy: rfAcc, f1_score: rfF1 },
            'XGBoost':       { accuracy: xgAcc, f1_score: xgF1 },
            'LightGBM':      { accuracy: lgAcc, f1_score: lgF1 },
          };
          // Filter to only models that were actually in this run
          const runScores = {};
          (r.models || []).forEach(m => { if (scores[m]) runScores[m] = scores[m]; });
          // Pick best by highest F1
          let best = r.models?.[0] || 'XGBoost';
          let bestF1 = 0;
          Object.entries(runScores).forEach(([model, s]) => {
            if (s.f1_score > bestF1) { bestF1 = s.f1_score; best = model; }
          });
          const champScores = runScores[best] || { accuracy: xgAcc, f1_score: xgF1 };
          return {
            ...r,
            status: 'Completed',
            score: champScores.f1_score,
            accuracy: champScores.accuracy,
            f1_score: champScores.f1_score,
            best_model: best,
            model_scores: runScores,
          };
        }
        return r;
      });

      return {
        data: { runs: mockRuns },
        status: 200, statusText: 'OK', headers: {}, config,
      };
    }

    // POST /models/train
    if (matchPath(url, '/models/train') && method === 'post') {
      let datasetName = 'ibm_hr_attrition.csv';
      let selectedModels = ['Random Forest', 'XGBoost', 'LightGBM'];
      let targetMetric = 'F1-Score';

      if (data instanceof FormData) {
        const file = data.get('file');
        if (file && file.name) datasetName = file.name;
        const models = data.getAll('models');
        if (models.length > 0) selectedModels = models;
        const tm = data.get('target_metric');
        if (tm) targetMetric = tm;
      }

      const newRun = {
        id: `run_${Math.random().toString(36).substring(2, 8)}`,
        dataset: datasetName,
        models: selectedModels,
        hyperparameters: { n_estimators: 300, max_depth: 10, smote_applied: true },
        status: 'Training...',
        targetMetric,
        score: null,
        accuracy: null,
        f1_score: null,
        timestamp: 'Just now',
      };

      mockRuns = [newRun, ...mockRuns];

      return {
        data: { message: 'Training pipeline dispatched successfully', run_id: newRun.id },
        status: 201, statusText: 'Created', headers: {}, config,
      };
    }

    // ============================================
    // POST /drift/inject  (MUST be checked BEFORE GET /drift)
    // ============================================
    if (matchPath(url, '/drift/inject') && method === 'post') {
      const parsed = typeof data === 'string' ? JSON.parse(data || '{}') : (data || {});
      const runId = parsed.run_id || null;

      // Resolve which run to retrain against
      const completedRuns = mockRuns.filter(r => r.status === 'Completed');
      let targetRun = null;
      if (runId) {
        targetRun = completedRuns.find(r => r.id === runId);
      }
      if (!targetRun && completedRuns.length > 0) {
        targetRun = completedRuns[0]; // default: latest completed run
      }

      driftState.isDrifted = true;
      driftState.currentPsi = 0.34;
      driftState.currentKs = 0.008;
      driftState.retrainingStartTime = Date.now();
      driftState.selectedRunId = targetRun?.id || null;
      driftState.selectedRunLabel = targetRun
        ? `${targetRun.models.join(' + ')} (${targetRun.dataset})`
        : 'XGBoost_Production_v5';

      const nowStr = new Date().toLocaleTimeString('en-US', { hour12: false });
      mockDriftHistory.push({ time: nowStr, psi: driftState.currentPsi, ks_pvalue: driftState.currentKs });
      if (mockDriftHistory.length > 20) mockDriftHistory.shift();

      return {
        data: {
          message: `Concept drift injected against ${driftState.selectedRunLabel}. Self-healing daemon triggered.`,
          target_run: targetRun,
        },
        status: 200, statusText: 'OK', headers: {}, config,
      };
    }

    // POST /drift/reset
    if (matchPath(url, '/drift/reset') && method === 'post') {
      driftState.isDrifted = false;
      driftState.currentPsi = 0.05;
      driftState.currentKs = 0.55;
      driftState.retrainingStartTime = null;
      driftState.selectedRunId = null;
      driftState.selectedRunLabel = null;
      const nowStr = new Date().toLocaleTimeString('en-US', { hour12: false });
      mockDriftHistory.push({ time: nowStr, psi: driftState.currentPsi, ks_pvalue: driftState.currentKs });

      return {
        data: { message: 'Baseline stabilized.' },
        status: 200, statusText: 'OK', headers: {}, config,
      };
    }

    // GET /drift  (general drift telemetry poll)
    if (url?.includes('/drift') && method === 'get') {
      const nowStr = new Date().toLocaleTimeString('en-US', { hour12: false });

      if (driftState.isDrifted && driftState.retrainingStartTime) {
        const elapsedS = (Date.now() - driftState.retrainingStartTime) / 1000;

        if (elapsedS < HEALING_DURATION_S) {
          // PSI stays high while retraining
          driftState.currentPsi = Number((0.28 + Math.random() * 0.06).toFixed(3));
          driftState.currentKs = Number((0.008 + Math.random() * 0.02).toFixed(3));
        } else {
          // ===== AUTO HEALING COMPLETE =====
          driftState.isDrifted = false;
          driftState.currentPsi = Number((0.04 + Math.random() * 0.03).toFixed(3));
          driftState.currentKs = Number((0.50 + Math.random() * 0.12).toFixed(3));

          // Insert newly retrained (self-healed) model into the registry
          const targetRun = mockRuns.find((r) => r.id === driftState.selectedRunId);
          const origDataset = targetRun ? targetRun.dataset : 'ibm_hr_attrition.csv';
          const origModels = targetRun ? targetRun.models : ['XGBoost', 'LightGBM'];
          const targetMetric = targetRun ? targetRun.targetMetric : 'F1-Score';

          // Clean base dataset if it starts with "drifted_" or "re_"
          let baseDatasetClean = origDataset
            .replace(/^drifted_/, '')
            .replace(/^re_/, '')
            .replace(/_healed\.csv$/, '.csv')
            .replace(/\.csv$/, '');
          const healedDatasetName = `${baseDatasetClean}_healed.csv`;

          const healedModels = origModels.map((m) => m.includes('(Self-Healed)') ? m : `${m} (Self-Healed)`);
          
          const modelScores = {};
          let bestMetricValue = -1;
          let bestModel = '';

          healedModels.forEach((m) => {
            let accuracy = Number((0.90 + Math.random() * 0.06).toFixed(3));
            let f1_score = Number((accuracy + (Math.random() - 0.5) * 0.01).toFixed(3));

            modelScores[m] = { accuracy, f1_score };

            const currentMetricValue = targetMetric === 'F1-Score' ? f1_score : accuracy;
            if (currentMetricValue > bestMetricValue) {
              bestMetricValue = currentMetricValue;
              bestModel = m;
            }
          });

          const healedScore = bestMetricValue;
          const healedAccuracy = modelScores[bestModel]?.accuracy ?? healedScore;
          const healedF1 = modelScores[bestModel]?.f1_score ?? healedScore;

          const healedRun = {
            id: `run_healed_${Math.floor(Math.random() * 10000)}`,
            dataset: healedDatasetName,
            models: healedModels,
            hyperparameters: { smote_balanced: true, optuna_tuned: true, self_healed: true },
            status: 'Completed',
            targetMetric: targetMetric,
            score: healedScore,
            accuracy: healedAccuracy,
            f1_score: healedF1,
            best_model: bestModel,
            model_scores: modelScores,
            timestamp: 'Just now',
          };
          mockRuns = [healedRun, ...mockRuns];

          driftState.retrainingStartTime = null;
          driftState.selectedRunId = null;
          driftState.selectedRunLabel = null;
        }
      } else {
        // Stable healthy micro-fluctuation
        driftState.currentPsi = Math.max(0.03, Math.min(0.12, driftState.currentPsi + (Math.random() - 0.5) * 0.008));
        driftState.currentKs = Math.max(0.35, Math.min(0.65, 0.5 - driftState.currentPsi / 2));
      }

      // Record sparkline history point
      const lastEntry = mockDriftHistory[mockDriftHistory.length - 1];
      if (!lastEntry || lastEntry.time !== nowStr) {
        mockDriftHistory.push({
          time: nowStr,
          psi: Number(driftState.currentPsi.toFixed(3)),
          ks_pvalue: Number(driftState.currentKs.toFixed(3)),
        });
        if (mockDriftHistory.length > 20) mockDriftHistory.shift();
      }

      const elapsed = driftState.isDrifted && driftState.retrainingStartTime
        ? Math.round((Date.now() - driftState.retrainingStartTime) / 1000)
        : 0;
      const remaining = Math.max(0, HEALING_DURATION_S - elapsed);

      return {
        data: {
          metrics: [...mockDriftHistory],
          current_psi: Number(driftState.currentPsi.toFixed(3)),
          current_ks_pvalue: Number(driftState.currentKs.toFixed(3)),
          threshold_psi: 0.25,
          threshold_ks: 0.05,
          is_drifted: driftState.isDrifted,
          self_healing_job: driftState.isDrifted
            ? {
                status: 'AUTONOMOUS_RETRAINING_IN_PROGRESS',
                trigger: `Evidently AI Concept Drift (PSI: ${driftState.currentPsi.toFixed(3)} > 0.25)`,
                target_model: driftState.selectedRunLabel || 'XGBoost_Production_v5',
                target_run_id: driftState.selectedRunId,
                started_at: `${elapsed}s ago`,
                remaining_s: remaining,
              }
            : null,
        },
        status: 200, statusText: 'OK', headers: {}, config,
      };
    }

    return Promise.reject({ response: { status: 404, data: { detail: 'Mock Endpoint Not Found' } } });
  };
}

// ==========================================
// RESPONSE INTERCEPTOR: 401 AUTH GUARD
// ==========================================
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
