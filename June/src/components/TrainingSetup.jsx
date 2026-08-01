import React, { useState, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { Upload, FileSpreadsheet, CheckSquare, Square, Cpu, Sliders, Play, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

const AVAILABLE_MODELS = [
  { id: 'Random Forest', name: 'Random Forest Engine', desc: 'Custom ensemble bagging trees with SMOTE auto-balancing' },
  { id: 'XGBoost', name: 'XGBoost Engine', desc: 'Extreme gradient boosted decision trees optimized for GPU acceleration' },
  { id: 'LightGBM', name: 'LightGBM Engine', desc: 'Lightweight histogram-based gradient boosting for high-dimensional tabular data' },
];

const METRIC_TARGETS = ['F1-Score', 'Accuracy', 'ROC-AUC', 'Precision', 'Recall'];

export const TrainingSetup = () => {
  const [file, setFile] = useState(null);
  const [selectedModels, setSelectedModels] = useState(['Random Forest', 'XGBoost']);
  const [targetMetric, setTargetMetric] = useState('F1-Score');
  const [dragActive, setDragActive] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');

  const fileInputRef = useRef(null);
  const queryClient = useQueryClient();

  // TanStack Query Mutation for POST /models/train
  const trainMutation = useMutation({
    mutationFn: async (formData) => {
      const response = await api.post('/models/train', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    },
    onSuccess: (data) => {
      setStatusMsg(`Pipeline dispatched successfully. Job Reference: ${data.run_id}`);
      // Invalidate live runs cache to force immediate dashboard refresh
      queryClient.invalidateQueries({ queryKey: ['runs'] });
      setFile(null);
    },
    onError: (err) => {
      setStatusMsg(`Pipeline fault: ${err.response?.data?.detail || err.message}`);
    },
  });

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.name.endsWith('.csv')) {
        setFile(droppedFile);
        setStatusMsg('');
      } else {
        setStatusMsg('Invalid payload format. Only .csv tabular datasets accepted.');
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setStatusMsg('');
    }
  };

  const toggleModel = (modelId) => {
    setSelectedModels((prev) =>
      prev.includes(modelId) ? prev.filter((m) => m !== modelId) : [...prev, modelId]
    );
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setStatusMsg('');

    if (selectedModels.length === 0) {
      setStatusMsg('Validation Error: Select at least one custom ML model engine.');
      return;
    }

    const formData = new FormData();
    if (file) {
      formData.append('file', file);
    } else {
      // Create mock dummy file if user wants to run quick demonstration
      const dummyBlob = new Blob(['col1,col2,target\n1,0,1\n0,1,0'], { type: 'text/csv' });
      formData.append('file', dummyBlob, 'synthetic_telemetry_demo.csv');
    }

    selectedModels.forEach((model) => {
      formData.append('models', model);
    });
    formData.append('target_metric', targetMetric);

    trainMutation.mutate(formData);
  };

  return (
    <div className="bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 p-6 shadow-lg rounded-xl">
      <div className="flex items-center justify-between pb-4 mb-6 border-b border-blue-200">
        <div className="flex items-center gap-2">
          <Cpu className="w-6 h-6 text-healing" />
          <h3 className="text-base font-mono font-bold uppercase tracking-wider text-blue-950">
            Concurrent Model Training Setup
          </h3>
        </div>
        <span className="text-[10px] font-mono uppercase bg-blue-200 text-blue-900 font-bold px-2 py-1 rounded">
          Custom Python Lifecycle
        </span>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* SECTION 1: DATASET INGESTION */}
        <div>
          <label className="block text-sm font-mono font-bold uppercase tracking-wider text-blue-950 mb-2">
            1. Tabular Dataset Ingestion (.CSV Payload)
          </label>
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed transition-all p-8 rounded-lg flex flex-col items-center justify-center cursor-pointer ${
              dragActive
                ? 'border-healing bg-white shadow-inner'
                : file
                ? 'border-healthy/50 bg-white shadow-inner'
                : 'border-blue-300 hover:border-blue-400 bg-white/60 hover:bg-white'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
            />
            {file ? (
              <div className="flex items-center gap-3 text-healthy font-mono text-sm">
                <FileSpreadsheet className="w-6 h-6 flex-shrink-0" />
                <div className="text-left">
                  <p className="font-bold text-blue-950">{file.name}</p>
                  <p className="text-xs font-semibold text-blue-700">{(file.size / 1024).toFixed(1)} KB // Tabular CSV Parsed</p>
                </div>
              </div>
            ) : (
              <div className="text-center font-mono space-y-2">
                <Upload className="w-8 h-8 text-blue-500 mx-auto" />
                <p className="text-sm font-semibold text-blue-900">
                  Drag and drop raw dataset CSV here, or <span className="text-healing underline cursor-pointer">browse local drive</span>
                </p>
                <p className="text-xs font-bold text-blue-600/80 uppercase tracking-widest">
                  Auto-SMOTE Feature Engineering Triggered On Upload
                </p>
              </div>
            )}
          </div>
        </div>

        {/* SECTION 2: MULTI-MODEL ENGINE SELECTION */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-mono font-bold uppercase tracking-wider text-blue-950">
              2. Target ML Engines (Concurrent Execution)
            </label>
            <span className="text-[11px] font-mono font-bold text-blue-700 bg-blue-200/50 px-2 py-1 rounded">
              {selectedModels.length} of {AVAILABLE_MODELS.length} selected
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {AVAILABLE_MODELS.map((model) => {
              const isSelected = selectedModels.includes(model.id);
              return (
                <div
                  key={model.id}
                  onClick={() => toggleModel(model.id)}
                  className={`p-4 border rounded-lg cursor-pointer transition-all flex flex-col justify-between ${
                    isSelected
                      ? 'border-healing bg-healing text-white shadow-md'
                      : 'border-blue-300 bg-white/60 text-blue-900 hover:border-blue-400 hover:bg-white'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <span className={`font-mono text-xs font-bold ${isSelected ? 'text-white' : 'text-blue-950'}`}>{model.id}</span>
                    {isSelected ? (
                      <CheckSquare className="w-4 h-4 text-white flex-shrink-0" />
                    ) : (
                      <Square className="w-4 h-4 text-blue-400 flex-shrink-0" />
                    )}
                  </div>
                  <p className={`text-xs font-medium leading-relaxed ${isSelected ? 'text-blue-50' : 'text-blue-800'}`}>{model.desc}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* SECTION 3: METRIC TARGET CONFIGURATION */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-blue-200">
          <div>
            <label className="block text-sm font-mono font-bold uppercase tracking-wider text-blue-950 mb-2 flex items-center gap-1.5">
              <Sliders className="w-4 h-4 text-blue-700" />
              3. Evaluation Optimization Target
            </label>
            <select
              value={targetMetric}
              onChange={(e) => setTargetMetric(e.target.value)}
              className="w-full bg-white border border-blue-300 px-3 py-2 rounded text-sm font-bold font-mono text-blue-950 focus:outline-none focus:border-healing focus:ring-2 focus:ring-healing/20 transition-colors shadow-sm"
            >
              {METRIC_TARGETS.map((metric) => (
                <option key={metric} value={metric}>
                  Maximize: {metric}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={trainMutation.isPending}
              className="w-full bg-healing rounded text-white hover:bg-blue-600 px-4 py-2 text-sm font-mono uppercase tracking-widest font-bold flex items-center justify-center gap-2 transition-all disabled:opacity-50 cursor-pointer h-[42px] shadow-lg shadow-healing/30"
            >
              {trainMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-white" />
                  Ingesting & Training...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  Dispatch Concurrent Job
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* STATUS NOTIFICATION BANNER */}
      {statusMsg && (
        <div
          className={`mt-6 p-3 border rounded font-mono text-sm font-bold flex items-center gap-2.5 shadow-sm ${
            trainMutation.isError
              ? 'bg-red-50 border-fault text-fault'
              : 'bg-green-50 border-healthy text-healthy'
          }`}
        >
          {trainMutation.isError ? (
            <AlertCircle className="w-5 h-5 flex-shrink-0 text-fault" />
          ) : (
            <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-healthy" />
          )}
          <span>{statusMsg}</span>
        </div>
      )}
    </div>
  );
};
