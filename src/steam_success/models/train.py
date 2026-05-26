from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from steam_success.config import ProjectSettings, SETTINGS
from steam_success.features.build_features import FEATURE_COLUMNS, make_xy


def _split(x: pd.DataFrame, y: pd.Series, settings: ProjectSettings):
    stratify = y if y.nunique() > 1 and y.value_counts().min() >= 2 else None
    test_size = settings.test_size_large_sample if len(y) >= settings.small_sample_cutoff else settings.test_size_small_sample
    return train_test_split(x, y, test_size=test_size, random_state=settings.random_state, stratify=stratify)


def _metrics(name: str, y_true, y_pred, y_prob) -> dict[str, object]:
    result = {
        "model": name,
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
        "classification_report": classification_report(y_true, y_pred, zero_division=0),
    }
    if len(set(y_true)) > 1:
        result["roc_auc"] = float(roc_auc_score(y_true, y_prob))
    else:
        result["roc_auc"] = None
    return result


def train_and_evaluate(dataset: pd.DataFrame, model_dir: Path, report_dir: Path, settings: ProjectSettings = SETTINGS) -> dict[str, object]:
    x, y = make_xy(dataset)
    if y.nunique() < 2:
        raise RuntimeError("Collected data has only one class; increase max_apps or adjust labeling thresholds.")
    x_train, x_test, y_train, y_test = _split(x, y, settings)
    models = {}
    if settings.use_logistic_regression:
        models["logistic_regression"] = Pipeline([
            ("scale", StandardScaler()),
            ("model", LogisticRegression(max_iter=settings.logistic_max_iter, class_weight="balanced", random_state=settings.random_state)),
        ])
    if settings.use_random_forest:
        models["random_forest"] = RandomForestClassifier(
            n_estimators=settings.random_forest_n_estimators,
            max_depth=settings.random_forest_max_depth,
            min_samples_leaf=settings.random_forest_min_samples_leaf,
            class_weight="balanced",
            random_state=settings.random_state,
        )
    if not models:
        raise RuntimeError("At least one model must be enabled in ProjectSettings.")
    results = []
    trained = {}
    for name, model in models.items():
        model.fit(x_train, y_train)
        pred = model.predict(x_test)
        prob = model.predict_proba(x_test)[:, 1]
        results.append(_metrics(name, y_test, pred, prob))
        trained[name] = model
    best = sorted(results, key=lambda row: (row["f1"], row["recall"], row["accuracy"]), reverse=True)[0]
    best_model = trained[best["model"]]
    model_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_model, model_dir / "steam_success_model.joblib")
    metrics_df = pd.DataFrame([{k: v for k, v in row.items() if k not in {"classification_report", "confusion_matrix"}} for row in results])
    metrics_df.to_csv(report_dir / "model_metrics.csv", index=False)
    (report_dir / "model_metrics.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    importances = _feature_importance(best_model)
    importances.to_csv(report_dir / "feature_importance.csv", index=False)
    scored = dataset[["appid", "name", "success", "total_reviews", "positive_rate"]].copy()
    scored["predicted_success_probability"] = best_model.predict_proba(x)[:, 1]
    scored.sort_values("predicted_success_probability", ascending=False).to_csv(report_dir / "predictions.csv", index=False)
    return {
        "best_model": best["model"],
        "metrics": results,
        "feature_importance": importances,
        "train_size": int(len(y_train)),
        "test_size": int(len(y_test)),
        "class_counts": y.value_counts().sort_index().to_dict(),
    }


def _feature_importance(model) -> pd.DataFrame:
    if isinstance(model, Pipeline):
        estimator = model.named_steps["model"]
        values = abs(estimator.coef_[0])
    else:
        values = model.feature_importances_
    return pd.DataFrame({"feature": FEATURE_COLUMNS, "importance": values}).sort_values("importance", ascending=False)
