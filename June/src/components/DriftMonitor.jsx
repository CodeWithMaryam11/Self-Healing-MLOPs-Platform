import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, ReferenceLine, Tooltip } from 'recharts';
import { AlertTriangle, Sparkles, TrendingUp, CheckCircle, RefreshCw, Zap, RotateCcw, ChevronDown } from 'lucide-react';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-zinc-50 border border-zinc-200 p-2 font-mono text-xs shadow-xl">
        <p className="text-zinc-400 mb-1">Time: {label}</p>
        <p className="text-warning font-semibold">
          PSI: {payload[0]?.value?.toFixed(3)} (Threshold: 0.25)
        </p>
      </div>
    );
  }
  return null;
};

export const DriftMonitor = () => {
  const queryClient = useQueryClient();
  const [selectedRunId, setSelectedRunId] = useState('latest');

  // Drift telemetry feed (2s polling)
  const { data: driftData } = useQuery({
    queryKey: ['drift'],
    queryFn: async () => {
      const res = await api.get('/drift');
      return res.data;
    },
    refetchInterval: 2000,
  });

  // Runs feed for model selector dropdown
  const { data: runsData } = useQuery({
    queryKey: ['runs'],
    queryFn: async () => {
      const res = await api.get('/runs');
      return res.data;
    },
    refetchInterval: 3000,
  });

  const completedRuns = (runsData?.runs || []).filter(r => r.status === 'Completed');

  const injectDriftMutation = useMutation({
    mutationFn: async () => {
      const runId = selectedRunId === 'latest' ? null : selectedRunId;
      return api.post('/drift/inject', { run_id: runId });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drift'] });
      queryClient.invalidateQueries({ queryKey: ['runs'] });
    },
  });

  const resetDriftMutation = useMutation({
    mutationFn: () => api.post('/drift/reset'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drift'] });
      queryClient.invalidateQueries({ queryKey: ['runs'] });
    },
  });

  const metrics = driftData?.metrics || [];
  const currentPsi = driftData?.current_psi ?? 0;
  const currentKs = driftData?.current_ks_pvalue ?? 0.45;
  const thresholdPsi = driftData?.threshold_psi || 0.25;
  const isDrifted = driftData?.is_drifted === true;
  const selfHealingJob = driftData?.self_healing_job;

  return (
    <div
      className={`p-6 border transition-all duration-500 flex flex-col justify-between shadow-lg rounded-xl ${isDrifted
          ? 'bg-warning/10 border-warning/80 shadow-warning/20'
          : 'bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200'
        }`}
    >
      <div>
        {/* HEADER */}
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-blue-200">
          <div className="flex items-center gap-2">
            {isDrifted ? (
              <AlertTriangle className="w-6 h-6 text-warning animate-bounce" />
            ) : (
              <TrendingUp className="w-6 h-6 text-healing" />
            )}
            <h3 className="text-base font-mono font-bold uppercase tracking-wider text-blue-950">
              Evidently AI Data Drift Feed
            </h3>
          </div>
          <span
            className={`text-[10px] font-mono uppercase px-2 py-1 border rounded font-bold ${isDrifted
                ? 'bg-warning/20 border-warning/50 text-warning-900 animate-pulse'
                : 'bg-blue-200 border-blue-300 text-blue-900'
              }`}
          >
            {isDrifted ? '⚠ Statistical Drift Alert' : '● Distribution Stable'}
          </span>
        </div>

        {/* LIVE METRICS SUMMARY */}
        <div className="grid grid-cols-2 gap-4 mb-6 font-mono">
          <div className="p-4 bg-white shadow-inner border border-blue-200 rounded-lg">
            <span className="text-xs font-bold uppercase text-blue-900 tracking-wider block">Population Stability (PSI)</span>
            <span className={`text-3xl font-bold transition-colors duration-300 my-1 block ${isDrifted ? 'text-warning' : 'text-blue-950'}`}>
              {currentPsi.toFixed(3)}
            </span>
            <span className="text-[11px] font-semibold text-blue-700 block">Critical Threshold: {thresholdPsi}</span>
          </div>

          <div className="p-4 bg-white shadow-inner border border-blue-200 rounded-lg">
            <span className="text-xs font-bold uppercase text-blue-900 tracking-wider block">Kolmogorov-Smirnov p-value</span>
            <span className={`text-3xl font-bold transition-colors duration-300 my-1 block ${isDrifted ? 'text-fault' : 'text-blue-950'}`}>
              {currentKs.toFixed(3)}
            </span>
            <span className="text-[11px] font-semibold text-blue-700 block">Reject H₀ if p &lt; 0.05</span>
          </div>
        </div>

        {/* PSI TELEMETRY AREA CHART */}
        <div className="mb-4">
          <div className="flex items-center justify-between text-xs font-mono font-bold text-blue-900 mb-2">
            <span>PSI Telemetry Spectrum (Live)</span>
            <span>Safety Threshold (0.25)</span>
          </div>
          <div className="h-56 w-full bg-white shadow-inner p-2 pb-6 border border-blue-200 rounded-lg">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={metrics} margin={{ top: 10, right: 10, left: 15, bottom: 20 }}>
                <defs>
                  <linearGradient id="psiGradDrift" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={isDrifted ? '#eab308' : '#3b82f6'} stopOpacity={0.5} />
                    <stop offset="95%" stopColor={isDrifted ? '#eab308' : '#3b82f6'} stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="time"
                  stroke="#1e3a8a"
                  fontSize={11}
                  tickLine={false}
                  label={{ value: 'Time (Live Feed)', position: 'bottom', offset: 5, fill: '#1e40af', fontSize: 12, fontWeight: 'bold' }}
                />
                <YAxis
                  stroke="#1e3a8a"
                  fontSize={11}
                  domain={[0, 0.45]}
                  tickLine={false}
                  label={{ value: 'PSI Score', angle: -90, position: 'insideLeft', offset: -5, fill: '#1e40af', fontSize: 12, fontWeight: 'bold', style: { textAnchor: 'middle' } }}
                />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine y={thresholdPsi} stroke="#eab308" strokeDasharray="4 4" strokeWidth={1.5} label="" />
                <Area
                  type="monotone"
                  dataKey="psi"
                  stroke={isDrifted ? '#eab308' : '#3b82f6'}
                  fillOpacity={1}
                  fill="url(#psiGradDrift)"
                  strokeWidth={2}
                  isAnimationActive={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* SELF-HEALING BANNER / HEALTHY STATUS */}
      <div className="space-y-4">
        {selfHealingJob ? (
          <div className="p-4 bg-healing-subtle border border-healing text-healing font-mono text-xs shadow-lg rounded-lg flex items-start gap-3">
            <RefreshCw className="w-5 h-5 text-healing animate-spin mt-0.5 flex-shrink-0" />
            <div className="space-y-1.5 w-full">
              <div className="flex items-center justify-between font-bold tracking-wide uppercase">
                <div className="flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Self-Healing Retraining Active</span>
                </div>
                <span className="bg-healing/20 px-2 py-0.5 text-[10px] text-white font-mono">
                  {selfHealingJob.remaining_s}s remaining
                </span>
              </div>
              <p className="text-zinc-700 font-sans text-[11px] leading-relaxed">
                SMOTE re-balancing and Optuna re-tuning <span className="font-mono font-semibold text-white">{selfHealingJob.target_model}</span> to stabilize distribution fault.
              </p>
              {/* Progress bar */}
              <div className="w-full h-1.5 bg-white mt-1 overflow-hidden">
                <div
                  className="h-full bg-healing transition-all duration-1000 ease-linear"
                  style={{ width: `${Math.min(100, ((15 - (selfHealingJob.remaining_s || 0)) / 15) * 100)}%` }}
                ></div>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-3 bg-white shadow-sm border border-blue-200 rounded-lg font-mono text-xs font-bold text-blue-900 flex items-center justify-between">
            <span>Autonomous Self-Healing Daemon: Standing By</span>
            <CheckCircle className="w-4 h-4 text-healthy" />
          </div>
        )}

        {/* MODEL SELECTOR + INJECT CONTROLS */}
        <div className="pt-4 mt-2 border-t border-blue-200 space-y-4">
          {/* Model Selector Dropdown */}
          <div>
            <label className="block text-xs font-mono font-bold uppercase text-blue-900 tracking-wider mb-1.5">
              Target Model Registry Run (for drift injection)
            </label>
            <div className="relative">
              <select
                value={selectedRunId}
                onChange={(e) => setSelectedRunId(e.target.value)}
                disabled={isDrifted}
                className={`w-full appearance-none bg-white border text-sm font-bold font-mono px-3 py-2.5 pr-8 rounded-lg outline-none transition-colors shadow-sm ${isDrifted
                    ? 'border-zinc-200 text-zinc-400 cursor-not-allowed'
                    : 'border-blue-300 text-blue-950 hover:border-blue-400 focus:border-healing focus:ring-2 focus:ring-healing/20'
                  }`}
              >
                <option value="latest">Auto: Latest Completed Run</option>
                {completedRuns.map((run) => (
                  <option key={run.id} value={run.id}>
                    {run.models?.join(' + ')} — {run.dataset} (Acc: {typeof run.accuracy === 'number' ? (run.accuracy * 100).toFixed(1) + '%' : 'N/A'})
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-blue-600 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => injectDriftMutation.mutate()}
              disabled={isDrifted || injectDriftMutation.isPending}
              className={`flex-1 flex items-center justify-center gap-2 px-3 py-3 rounded-lg text-sm font-mono uppercase tracking-widest font-bold transition-all ${isDrifted
                  ? 'bg-zinc-100 text-zinc-500 cursor-not-allowed border border-zinc-300 shadow-sm'
                  : 'bg-warning/10 hover:bg-warning/20 text-warning-700 border border-warning/50 hover:border-warning shadow-lg shadow-warning/20 active:scale-95'
                }`}
            >
              <Zap className="w-5 h-5" />
              <span>{injectDriftMutation.isPending ? 'Injecting...' : '⚡ Inject Concept Drift'}</span>
            </button>

            <button
              onClick={() => resetDriftMutation.mutate()}
              disabled={!isDrifted || resetDriftMutation.isPending}
              className={`px-4 py-3 rounded-lg text-sm font-mono uppercase tracking-widest font-bold transition-all flex items-center gap-2 ${!isDrifted
                  ? 'bg-white text-zinc-400 border border-zinc-200 cursor-not-allowed shadow-sm'
                  : 'bg-white hover:bg-zinc-50 text-zinc-800 border border-zinc-300 shadow-md active:scale-95'
                }`}
            >
              <RotateCcw className="w-4 h-4" />
              <span>Reset</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
