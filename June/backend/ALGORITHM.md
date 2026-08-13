# PipelineIQ: Backend Pseudocode Specifications

Please refer to the main repository algorithm specification at [ALGORITHM.md](file:///Users/dev-momin/June/June/ALGORITHM.md) for the complete mathematical and pseudocode definitions:

1. **Algorithm 1: PreprocessAndBalanceSMOTE** — Target detection, missing value imputation, Quantile scaling, SMOTE class balancing.
2. **Algorithm 2: TrainConcurrentAutoML** — Multi-model concurrent execution (Random Forest, XGBoost, LightGBM), decision probability calibration, MLflow experiment tracking.
3. **Algorithm 3: EvaluateDataDrift** — Population Stability Index (PSI) calculation and 2-sample Kolmogorov-Smirnov (KS-test) covariate shift monitoring.
4. **Algorithm 4: TriggerSelfHealingPipeline** — Asynchronous background worker dispatch, adaptive hyperparameter scaling, and zero-downtime champion model promotion.
