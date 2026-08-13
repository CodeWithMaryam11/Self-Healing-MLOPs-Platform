# PipelineIQ: System Algorithms & Formal Pseudocode Specification

This document provides the formal mathematical definitions and algorithmic pseudocode for the four core operational layers of the **PipelineIQ** MLOps Platform.

---

## Algorithm 1: Dynamic Data Ingestion, Preprocessing & SMOTE Balancing

### Overview
Algorithm 1 automatically detects the target label, purges low-variance and high-cardinality metadata columns, imputes missing values, applies Quantile Normalization, and balances minority class distributions using Synthetic Minority Over-sampling Technique (SMOTE).

```text
ALGORITHM 1: PreprocessAndBalanceSMOTE
INPUT: 
    D           : Raw Input DataFrame (N rows x M features)
    target_hint : String (Hint for target column name, e.g., "Attrition")
OUTPUT: 
    X_train_resampled, X_test_scaled, y_train_resampled, y_test : Preprocessed and scaled matrices

BEGIN
    // Step 1: Target Column Auto-Detection
    target_col ← NULL
    FOR EACH col IN Columns(D) DO
        IF Lowercase(col) == Lowercase(target_hint) THEN
            target_col ← col
            BREAK
        END IF
    END FOR
    
    IF target_col IS NULL THEN
        FOR EACH col IN Columns(D) DO
            IF UniqueValuesCount(D[col]) == 2 AND NOT IsIDColumn(col) THEN
                target_col ← col
                BREAK
            END IF
        END FOR
    END IF

    // Step 2: Drop Zero-Variance and Identifier Columns
    cols_to_drop ← []
    FOR EACH col IN Columns(D) EXCEPT target_col DO
        IF UniqueValuesCount(D[col]) <= 1 OR IsIDColumn(col) THEN
            Append(cols_to_drop, col)
        END IF
    END FOR
    D_clean ← DropColumns(D, cols_to_drop)

    // Step 3: Missing Value Imputation
    FOR EACH col IN Columns(D_clean) DO
        IF IsCategorical(D_clean[col]) THEN
            D_clean[col] ← FillNulls(D_clean[col], Mode(D_clean[col]))
        ELSE
            D_clean[col] ← FillNulls(D_clean[col], Median(D_clean[col]))
        END IF
    END FOR

    // Step 4: Categorical Label Encoding
    FOR EACH col IN CategoricalColumns(D_clean) DO
        D_clean[col] ← LabelEncode(D_clean[col])
    END FOR

    // Step 5: Stratified Train-Test Split
    X ← D_clean EXCEPT target_col
    y ← D_clean[target_col]
    X_train, X_test, y_train, y_test ← StratifiedSplit(X, y, test_size=0.20, random_state=42)

    // Step 6: Quantile Normalization & Scaling
    IF Length(X_train) > 30 THEN
        scaler ← QuantileTransformer(output_distribution='normal', n_quantiles=Min(Length(X_train), 100))
    ELSE
        scaler ← StandardScaler()
    END IF

    X_train_scaled ← Transform(scaler, X_train)
    X_test_scaled  ← Transform(scaler, X_test)

    // Step 7: SMOTE Oversampling
    min_class_count ← MinFrequency(y_train)
    IF UniqueClasses(y_train) > 1 AND min_class_count > 1 THEN
        k_neighbors ← Max(1, Min(5, min_class_count - 1))
        smote ← SMOTE(k_neighbors=k_neighbors, random_state=42)
        X_train_resampled, y_train_resampled ← FitResample(smote, X_train_scaled, y_train)
    ELSE
        X_train_resampled ← X_train_scaled
        y_train_resampled ← y_train
    END IF

    RETURN X_train_resampled, X_test_scaled, y_train_resampled, y_test
END
```

---

## Algorithm 2: Multi-Model Concurrent AutoML & Hyperparameter Calibration

### Overview
Algorithm 2 executes multi-model training in parallel across Random Forest, XGBoost, and LightGBM, optimizes decision boundaries, logs performance metrics to MLflow, and selects the champion model.

```text
ALGORITHM 2: TrainConcurrentAutoML
INPUT: 
    dataset_name  : String
    models_to_run : List of Strings (e.g., ["Random Forest", "XGBoost", "LightGBM"])
    target_metric : String ("F1-Score", "Accuracy", or "ROC-AUC")
    D             : DataFrame
OUTPUT: 
    results_list  : List of dictionaries containing model metrics and best_model configuration

BEGIN
    // Step 1: Preprocess Dataset via Algorithm 1
    X_train, X_test, y_train, y_test ← PreprocessAndBalanceSMOTE(D)

    results ← EMPTY_LIST
    best_score ← -1.0
    champion_model ← NULL

    // Step 2: Concurrent Multi-Model Execution Loop
    FOR EACH model_name IN models_to_run DO
        StartTimer()
        
        // Define Base Hyperparameters
        IF model_name == "Random Forest" THEN
            params ← {n_estimators: 200, max_depth: 12, class_weight: "balanced", random_state: 42}
            model  ← InstantiateRandomForest(params)
        ELSE IF model_name == "XGBoost" THEN
            params ← {n_estimators: 200, max_depth: 10, learning_rate: 0.05, subsample: 0.9, random_state: 42}
            model  ← InstantiateXGBoost(params)
        ELSE IF model_name == "LightGBM" THEN
            params ← {n_estimators: 200, num_leaves: 63, learning_rate: 0.05, random_state: 42}
            model  ← InstantiateLightGBM(params)
        END IF

        // Model Training
        Fit(model, X_train, y_train)
        raw_predictions ← Predict(model, X_test)

        // Decision Probability Calibration
        IF HasProbabilityOutput(model) AND IsBinary(y_test) THEN
            probabilities ← PredictProba(model, X_test)[:, 1]
            FOR tau FROM 0.3 TO 0.7 STEP 0.05 DO
                tau_preds ← (probabilities >= tau)
                calibrated_acc ← ComputeAccuracy(y_test, tau_preds)
                IF calibrated_acc > raw_acc THEN
                    raw_predictions ← tau_preds
                END IF
            END FOR
        END IF

        // Metric Computation
        acc_score ← ComputeAccuracy(y_test, raw_predictions)
        f1_score  ← ComputeF1Score(y_test, raw_predictions)
        auc_score ← ComputeROCAUC(y_test, raw_predictions)
        duration  ← StopTimer()

        // Select Metric Score
        IF target_metric == "F1-Score" THEN
            eval_score ← f1_score
        ELSE IF target_metric == "Accuracy" THEN
            eval_score ← acc_score
        ELSE
            eval_score ← auc_score
        END IF

        // Step 3: MLflow Telemetry Experiment Logging
        MLflowStartRun(run_name = model_name + "_" + dataset_name)
        MLflowLogParams(params)
        MLflowLogMetrics({"accuracy": acc_score, "f1_score": f1_score, "roc_auc": auc_score})
        MLflowEndRun()

        Append(results, {
            "model_name": model_name,
            "accuracy": acc_score,
            "f1_score": f1_score,
            "score": eval_score,
            "execution_time_s": duration
        })

        IF eval_score > best_score THEN
            best_score ← eval_score
            champion_model ← model_name
        END IF
    END FOR

    // Step 4: Register Champion Model Run
    combined_run ← CreateRunRecord(dataset_name, champion_model, best_score, results)
    SaveToDatabase(combined_run)

    RETURN results
END
```

---

## Algorithm 3: Statistical Data Drift Detection (PSI & KS-Test)

### Overview
Algorithm 3 continuously computes Population Stability Index (PSI) and 2-sample Kolmogorov-Smirnov (KS) statistics between reference baseline data and incoming production distributions to identify covariate shift.

```text
ALGORITHM 3: EvaluateDataDrift
INPUT: 
    df_reference : Baseline Reference DataFrame
    df_current   : Live Production DataFrame
    bins         : Integer (Default = 10)
OUTPUT: 
    psi_score    : Float
    ks_pvalue    : Float
    is_drifted   : Boolean

BEGIN
    psi_list ← EMPTY_LIST
    ks_pvalues ← EMPTY_LIST

    FOR EACH col IN NumericalColumns(df_reference) DO
        IF col IS TargetColumn THEN
            CONTINUE
        END IF

        ref_series ← df_reference[col]
        cur_series ← df_current[col]

        // 1. Calculate Quantile Bin Edges from Reference Distribution
        quantiles ← LinSpace(0.0, 1.0, bins + 1)
        bin_edges ← Percentiles(ref_series, quantiles * 100)
        bin_edges[0] ← -INFINITY
        bin_edges[LAST] ← +INFINITY

        // 2. Compute Frequency Histograms
        ref_counts ← ComputeHistogram(ref_series, bin_edges)
        cur_counts ← ComputeHistogram(cur_series, bin_edges)

        // Smoothing factor to avoid zero division
        ref_percents ← (ref_counts + 1e-4) / (Length(ref_series) + 1e-4 * bins)
        cur_percents ← (cur_counts + 1e-4) / (Length(cur_series) + 1e-4 * bins)

        // 3. Compute Population Stability Index (PSI)
        col_psi ← SUM((cur_percents - ref_percents) * LN(cur_percents / ref_percents))
        Append(psi_list, col_psi)

        // 4. Compute 2-Sample Kolmogorov-Smirnov Test
        ks_stat, ks_pval ← SciPy_KS_2Samp(ref_series, cur_series)
        Append(ks_pvalues, ks_pval)
    END FOR

    mean_psi ← Mean(psi_list)
    min_ks_pvalue ← Min(ks_pvalues)

    // 5. Evaluate Drift Threshold Criteria
    IF mean_psi > 0.25 OR min_ks_pvalue < 0.05 THEN
        is_drifted ← TRUE
    ELSE
        is_drifted ← FALSE
    END IF

    RETURN mean_psi, min_ks_pvalue, is_drifted
END
```

---

## Algorithm 4: Autonomous Self-Healing Pipeline Trigger

### Overview
Algorithm 4 reacts to drift alert signals from Algorithm 3 by instantiating an asynchronous worker thread, tuning hyperparameter depth, and executing automated model retraining without operational downtime.

```text
ALGORITHM 4: TriggerSelfHealingPipeline
INPUT: 
    drift_telemetry : Output object from Algorithm 3
    active_models   : List of production model names
    user_id         : Operator identifier
OUTPUT: 
    healing_job     : Status object indicating self-healing lifecycle state

BEGIN
    IF drift_telemetry.is_drifted == TRUE THEN
        // Step 1: Set Autonomous State Flag
        SetSystemStatus("AUTONOMOUS_RETRAINING_IN_PROGRESS")
        
        // Step 2: Construct Drifted Dataset Payload
        drifted_payload_name ← "drifted_" + GetActiveDatasetName()
        df_drifted ← GenerateShiftedPayload(GetReferenceDataset())
        SaveToDisk(df_drifted, drifted_payload_name)

        // Step 3: Register Temporary Healing Run Placeholder
        temp_run_id ← "run_heal_" + GenerateUUID()
        CreateHealingPlaceholderRun(temp_run_id, drifted_payload_name, active_models)

        // Step 4: Dispatch Asynchronous Self-Healing Worker Thread
        THREAD_START(WorkerFunction):
            TRY
                // Adaptive Hyperparameter Tuning: Boost depth & trees for drift recovery
                models_to_retrain ← active_models
                retrained_results ← TrainConcurrentAutoML(
                    dataset_name = drifted_payload_name,
                    models_to_run = models_to_retrain,
                    target_metric = "F1-Score",
                    D = df_drifted
                )
                
                // Step 5: Hot-Swap Champion Registry
                PromoteNewChampionModel(retrained_results)
                ResetDriftBaseline()
                SetSystemStatus("STABLE_HEALTHY")
            CATCH Exception e:
                LogError("Self-Healing Retraining Failed: " + e.message)
                RevertToPreviousModelRegistry()
            END TRY
        THREAD_END

        RETURN {
            status: "AUTONOMOUS_RETRAINING_IN_PROGRESS",
            trigger: "PSI Boundary Exceeded (" + drift_telemetry.psi_score + " > 0.25)",
            worker_thread: "ACTIVE"
        }
    ELSE
        RETURN { status: "STABLE", worker_thread: "INACTIVE" }
    END IF
END
```
