"""
PH-06: Đánh giá & Kiểm thử mô hình — AirGlobal AQI Dataset
Author: Huy

Gộp tất cả 7 nhiệm vụ PH-06 vào 1 file:
  Task 1: Weighted F1, Macro F1, Accuracy, Cohen's Kappa, ROC-AUC (OvR) — tất cả model
  Task 2: Precision / Recall / F1 per class
  Task 3: Confusion Matrix heatmap + phân tích nhãn hay nhầm
  Task 4: Calibration curve
  Task 5: Phân tích lỗi chi tiết (20 bản ghi sai nghiêm trọng)
  Task 6: Robustness theo country (top 5 quốc gia nhiều data nhất)
  Task 7: Kiểm thử với missing sensor (10%, 20%, 30%)

Chạy:
    python src/evaluate_ph06.py
"""

from __future__ import annotations

import warnings
import pickle
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

warnings.filterwarnings("ignore")

# ── Đường dẫn ────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parents[1]
MODEL_DIR   = BASE_DIR / "ph05_classification" / "models"
PH03_OUTPUT = BASE_DIR / "ph03_preprocessing" / "outputs"
OUTPUT_DIR  = BASE_DIR / "outputs" / "ph06"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_COL = "target_aqi_bucket"
RANDOM_STATE = 42

MODEL_FILES = {
    "XGBoost":               MODEL_DIR / "model_XGBoost.pkl",
    "DecisionTree":          MODEL_DIR / "model_DecisionTree.pkl",
    "RandomForest":          MODEL_DIR / "model_RandomForest.pkl",
    "ExtraTrees":            MODEL_DIR / "model_ExtraTrees.pkl",
    "LogisticRegression_SGD": MODEL_DIR / "model_LogisticRegression_SGD.pkl",
}


# ── Helpers ───────────────────────────────────────────────────────────────────
def log(msg: str) -> None:
    print(msg, flush=True)


def load_data_and_pipeline():
    """Load test set, encoder, preprocessor, tất cả models."""
    encoder   = joblib.load(MODEL_DIR / "label_encoder.pkl")
    pipeline  = joblib.load(MODEL_DIR / "best_aqi_classifier_pipeline.pkl")
    preprocessor = pipeline.named_steps["preprocessor"]

    df = pd.read_pickle(PH03_OUTPUT / "processed_airglobal_features.pkl")

    catalog = pd.read_csv(PH03_OUTPUT / "feature_catalog.csv")
    LEAKAGE = {"aqi", "aqi_bucket", "aqi_bucket_clean", TARGET_COL, "split", "date"}
    feature_cols = [c for c in catalog["feature"].tolist() if c in df.columns and c not in LEAKAGE]

    test_df = df[df["split"] == "test"].dropna(subset=[TARGET_COL]).copy()
    known   = list(encoder.classes_)
    test_df = test_df[test_df[TARGET_COL].isin(known)]

    X_test_raw = test_df[feature_cols]
    X_test     = preprocessor.transform(X_test_raw)
    y_test     = encoder.transform(test_df[TARGET_COL].astype(str))
    labels     = list(encoder.classes_)
    n_cls      = len(labels)

    models = {}
    for name, path in MODEL_FILES.items():
        if path.exists():
            models[name] = joblib.load(path)
        else:
            log(f"  ⚠️  Không tìm thấy {path.name}, bỏ qua.")

    return df, test_df, X_test_raw, X_test, y_test, labels, n_cls, encoder, preprocessor, models, feature_cols


# ── Task 1: Summary metrics tất cả model ─────────────────────────────────────
def task1_summary(models, X_test, y_test, labels, n_cls, encoder):
    log("\n" + "="*70)
    log("TASK 1 — Summary Metrics (All Models)")
    log("="*70)

    rows = []
    for name, model in models.items():
        pred = model.predict(X_test)
        row = {
            "Model":          name,
            "Accuracy":       round(accuracy_score(y_test, pred), 4),
            "Weighted F1":    round(f1_score(y_test, pred, average="weighted", zero_division=0), 4),
            "Macro F1":       round(f1_score(y_test, pred, average="macro",    zero_division=0), 4),
            "Cohen Kappa":    round(cohen_kappa_score(y_test, pred), 4),
            "ROC-AUC (OvR)":  float("nan"),
        }
        if hasattr(model, "predict_proba"):
            try:
                proba = model.predict_proba(X_test)
                if proba.shape[1] == n_cls:
                    row["ROC-AUC (OvR)"] = round(
                        roc_auc_score(y_test, proba, multi_class="ovr",
                                      average="macro", labels=np.arange(n_cls)), 4)
            except Exception as e:
                log(f"  ⚠️  ROC-AUC lỗi {name}: {e}")
        rows.append(row)

    summary = pd.DataFrame(rows).sort_values("Weighted F1", ascending=False).reset_index(drop=True)
    summary.index += 1
    log(summary.to_string())
    summary.to_csv(OUTPUT_DIR / "task1_summary_metrics.csv", index_label="Rank", encoding="utf-8-sig")
    log("  ✅ Saved: task1_summary_metrics.csv")
    return summary


# ── Task 2: Precision / Recall / F1 per class ────────────────────────────────
def task2_per_class(models, X_test, y_test, labels, encoder):
    log("\n" + "="*70)
    log("TASK 2 — Precision / Recall / F1 per Class (Best Model: XGBoost)")
    log("="*70)

    best = models.get("XGBoost", list(models.values())[0])
    pred = best.predict(X_test)

    report_dict = classification_report(
        y_test, pred, target_names=labels, zero_division=0, output_dict=True)
    report_df = pd.DataFrame(report_dict).T
    log(classification_report(y_test, pred, target_names=labels, zero_division=0))

    report_df.to_csv(OUTPUT_DIR / "task2_per_class_report.csv", encoding="utf-8-sig")
    log("  ✅ Saved: task2_per_class_report.csv")

    # Xác định nhãn khó nhất
    per_class = report_df.loc[labels].sort_values("f1-score")
    hardest = per_class.index[0]
    log(f"  📌 Nhãn khó phân loại nhất: {hardest} (F1={per_class.loc[hardest,'f1-score']:.4f})")
    log(f"     Lý do: ít mẫu (support={int(per_class.loc[hardest,'support'])}) và dễ bị nhầm với nhãn lân cận.")

    return pred, report_df


# ── Task 3: Confusion Matrix ──────────────────────────────────────────────────
def task3_confusion_matrix(models, X_test, y_test, labels, pred_best):
    log("\n" + "="*70)
    log("TASK 3 — Confusion Matrix Heatmap + Phân tích")
    log("="*70)

    cm = confusion_matrix(y_test, pred_best, labels=list(range(len(labels))))

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(cm, interpolation="nearest", cmap="Blues")
    ax.figure.colorbar(im, ax=ax)
    ax.set(
        xticks=np.arange(len(labels)),
        yticks=np.arange(len(labels)),
        xticklabels=labels,
        yticklabels=labels,
        ylabel="True label",
        xlabel="Predicted label",
        title="Confusion Matrix — XGBoost (Test Set)",
    )
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    thresh = cm.max() / 2
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], "d"), ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "task3_confusion_matrix.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    log("  ✅ Saved: task3_confusion_matrix.png")

    # Phân tích nhãn hay bị nhầm
    log("\n  📌 Phân tích nhầm lẫn:")
    cm_df = pd.DataFrame(cm, index=labels, columns=labels)
    insights = []
    for i, true_label in enumerate(labels):
        row = cm[i].copy()
        row[i] = 0  # bỏ đường chéo
        if row.max() > 0:
            pred_label = labels[row.argmax()]
            count = row.max()
            total = cm[i].sum()
            pct = count / total * 100
            msg = f"    {true_label} → bị nhầm thành {pred_label}: {count} lần ({pct:.1f}%)"
            log(msg)
            insights.append({"true": true_label, "predicted_as": pred_label,
                              "count": int(count), "pct": round(pct, 2)})

    pd.DataFrame(insights).to_csv(OUTPUT_DIR / "task3_confusion_analysis.csv",
                                   index=False, encoding="utf-8-sig")
    log("  ✅ Saved: task3_confusion_analysis.csv")


# ── Task 4: Calibration Curve ─────────────────────────────────────────────────
def task4_calibration(models, X_test, y_test, labels, n_cls):
    log("\n" + "="*70)
    log("TASK 4 — Calibration Curve")
    log("="*70)

    best = models.get("XGBoost", list(models.values())[0])
    if not hasattr(best, "predict_proba"):
        log("  ⚠️  Model không có predict_proba. Bỏ qua calibration.")
        return

    proba = best.predict_proba(X_test)
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    for i, label in enumerate(labels):
        if i >= len(axes):
            break
        y_binary = (y_test == i).astype(int)
        prob_pos  = proba[:, i]
        try:
            fraction_pos, mean_pred = calibration_curve(y_binary, prob_pos, n_bins=10)
            axes[i].plot(mean_pred, fraction_pos, "s-", label="XGBoost")
            axes[i].plot([0, 1], [0, 1], "k--", label="Perfect")
            axes[i].set_title(f"Calibration — {label}")
            axes[i].set_xlabel("Mean predicted probability")
            axes[i].set_ylabel("Fraction of positives")
            axes[i].legend()

            # Đánh giá overconfident
            gap = float(np.mean(np.abs(fraction_pos - mean_pred)))
            status = "✅ Well-calibrated" if gap < 0.05 else "⚠️  Overconfident" if mean_pred.mean() > fraction_pos.mean() else "⚠️  Underconfident"
            log(f"  {label}: {status} (mean gap={gap:.4f})")
        except Exception as e:
            log(f"  ⚠️  {label}: calibration lỗi ({e})")

    # Ẩn subplot thừa
    for j in range(len(labels), len(axes)):
        axes[j].set_visible(False)

    fig.suptitle("Calibration Curves — XGBoost (per class)", fontsize=14)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "task4_calibration_curves.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    log("  ✅ Saved: task4_calibration_curves.png")


# ── Task 5: Phân tích lỗi chi tiết ───────────────────────────────────────────
def task5_error_analysis(models, X_test_raw, X_test, y_test, test_df, labels, encoder):
    log("\n" + "="*70)
    log("TASK 5 — Phân tích lỗi chi tiết (sai nghiêm trọng)")
    log("="*70)

    best  = models.get("XGBoost", list(models.values())[0])
    pred  = best.predict(X_test)

    # Lỗi nghiêm trọng: Hazardous predict là Good hoặc ngược lại
    label_arr = np.array(labels)
    hazardous_idx = list(labels).index("Hazardous") if "Hazardous" in labels else None
    good_idx      = list(labels).index("Good")      if "Good"      in labels else None

    serious_mask = np.zeros(len(y_test), dtype=bool)
    if hazardous_idx is not None and good_idx is not None:
        serious_mask = (
            ((y_test == hazardous_idx) & (pred == good_idx)) |
            ((y_test == good_idx)      & (pred == hazardous_idx))
        )

    # Nếu không đủ lỗi nghiêm trọng thì lấy tất cả sai
    error_mask = y_test != pred
    if serious_mask.sum() < 5:
        log(f"  ℹ️  Chỉ có {serious_mask.sum()} lỗi Hazardous↔Good. Lấy thêm lỗi cross-class.")
        serious_mask = error_mask

    serious_idx = np.where(serious_mask)[0][:20]

    test_reset = test_df.reset_index(drop=True)
    error_records = []
    for i in serious_idx:
        record = {
            "index":        int(i),
            "true_label":   labels[y_test[i]],
            "pred_label":   labels[pred[i]],
            "country":      test_reset.iloc[i].get("country", "N/A"),
            "city":         test_reset.iloc[i].get("city", "N/A"),
            "date":         test_reset.iloc[i].get("date", "N/A"),
            "pm25":         test_reset.iloc[i].get("pm25", float("nan")),
            "aqi":          test_reset.iloc[i].get("aqi",  float("nan")),
            "humidity":     test_reset.iloc[i].get("humidity", float("nan")),
            "wind_speed":   test_reset.iloc[i].get("wind_speed", float("nan")),
        }
        error_records.append(record)

    error_df = pd.DataFrame(error_records)
    log(error_df.to_string(index=False))
    error_df.to_csv(OUTPUT_DIR / "task5_error_analysis.csv", index=False, encoding="utf-8-sig")
    log(f"\n  📌 Tổng lỗi: {error_mask.sum():,} / {len(y_test):,} ({error_mask.mean()*100:.2f}%)")
    log(f"  📌 Lỗi nghiêm trọng (Hazardous↔Good): {((y_test == hazardous_idx) & (pred == good_idx)).sum() + ((y_test == good_idx) & (pred == hazardous_idx)).sum() if hazardous_idx else 0}")
    log("  ✅ Saved: task5_error_analysis.csv")


# ── Task 6: Robustness theo country ──────────────────────────────────────────
def task6_robustness_by_country(models, preprocessor, feature_cols, df, labels, n_cls, encoder):
    log("\n" + "="*70)
    log("TASK 6 — Robustness theo Country (Top 5)")
    log("="*70)

    best = models.get("XGBoost", list(models.values())[0])
    LEAKAGE = {"aqi", "aqi_bucket", "aqi_bucket_clean", TARGET_COL, "split", "date"}

    test_df = df[df["split"] == "test"].dropna(subset=[TARGET_COL]).copy()
    known   = list(encoder.classes_)
    test_df = test_df[test_df[TARGET_COL].isin(known)]

    top_countries = test_df["country"].value_counts().head(5).index.tolist()
    rows = []

    for country in top_countries:
        sub = test_df[test_df["country"] == country]
        if len(sub) < 30:
            continue
        cols = [c for c in feature_cols if c in sub.columns and c not in LEAKAGE]
        X_sub = preprocessor.transform(sub[cols])
        y_sub = encoder.transform(sub[TARGET_COL].astype(str))
        pred  = best.predict(X_sub)

        row = {
            "Country":      country,
            "N":            len(sub),
            "Accuracy":     round(accuracy_score(y_sub, pred), 4),
            "Weighted F1":  round(f1_score(y_sub, pred, average="weighted", zero_division=0), 4),
            "Macro F1":     round(f1_score(y_sub, pred, average="macro",    zero_division=0), 4),
            "Cohen Kappa":  round(cohen_kappa_score(y_sub, pred), 4),
        }
        rows.append(row)

    result = pd.DataFrame(rows).sort_values("Weighted F1", ascending=False)
    log(result.to_string(index=False))
    result.to_csv(OUTPUT_DIR / "task6_robustness_by_country.csv", index=False, encoding="utf-8-sig")

    # Plot
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(result))
    width = 0.25
    ax.bar(x - width, result["Weighted F1"], width, label="Weighted F1")
    ax.bar(x,         result["Macro F1"],    width, label="Macro F1")
    ax.bar(x + width, result["Accuracy"],    width, label="Accuracy")
    ax.set_xticks(x)
    ax.set_xticklabels(result["Country"], rotation=15)
    ax.set_ylim(0, 1.1)
    ax.set_title("Robustness by Country — XGBoost")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "task6_robustness_by_country.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    # Kiểm tra bias
    f1_std = result["Weighted F1"].std()
    bias_note = "✅ Không có bias rõ ràng" if f1_std < 0.05 else f"⚠️  Có bias theo country (std F1={f1_std:.4f})"
    log(f"\n  📌 {bias_note}")
    log("  ✅ Saved: task6_robustness_by_country.csv + .png")


# ── Task 7: Missing sensor robustness ────────────────────────────────────────
def task7_missing_sensor(models, preprocessor, X_test_raw, y_test, feature_cols):
    log("\n" + "="*70)
    log("TASK 7 — Robustness với Missing Sensor (10%, 20%, 30%)")
    log("="*70)

    best = models.get("XGBoost", list(models.values())[0])

    # Baseline trên data gốc
    X_baseline = preprocessor.transform(X_test_raw)
    baseline   = f1_score(y_test, best.predict(X_baseline), average="weighted", zero_division=0)
    log(f"  Baseline Weighted F1 (no missing): {baseline:.4f}")

    # Chỉ simulate missing trên numeric columns
    numeric_cols = [c for c in X_test_raw.columns
                    if pd.api.types.is_numeric_dtype(X_test_raw[c])]

    rows = []
    for missing_pct in [0.10, 0.20, 0.30]:
        rng      = np.random.default_rng(RANDOM_STATE)
        X_noisy  = X_test_raw.copy()

        # Set NaN ngẫu nhiên trên numeric cols
        for col in numeric_cols:
            mask = rng.random(len(X_noisy)) < missing_pct
            X_noisy.loc[mask, col] = np.nan

        # Fill NaN bằng median của từng cột trước khi transform
        col_medians = X_test_raw[numeric_cols].median()
        X_noisy[numeric_cols] = X_noisy[numeric_cols].fillna(col_medians)

        # Transform và predict
        X_transformed = preprocessor.transform(X_noisy)
        pred  = best.predict(X_transformed)
        f1    = f1_score(y_test, pred, average="weighted", zero_division=0)
        drop  = baseline - f1
        status = "✅ OK" if drop < 0.05 else "⚠️  Vượt ngưỡng 5%"
        log(f"  Missing {int(missing_pct*100)}%: Weighted F1={f1:.4f} | Drop={drop:.4f} | {status}")
        rows.append({
            "Missing %":   f"{int(missing_pct*100)}%",
            "Weighted F1": round(f1, 4),
            "F1 Drop":     round(drop, 4),
            "Drop %":      round(drop / baseline * 100, 2),
            "Status":      status,
        })

    result = pd.DataFrame(rows)
    result.to_csv(OUTPUT_DIR / "task7_missing_sensor.csv", index=False, encoding="utf-8-sig")

    fig, ax = plt.subplots(figsize=(7, 5))
    pcts = [0, 10, 20, 30]
    f1s  = [baseline] + result["Weighted F1"].tolist()
    ax.plot(pcts, f1s, "o-", color="steelblue", linewidth=2)
    ax.axhline(baseline * 0.95, color="red", linestyle="--", label="Ngưỡng -5%")
    ax.set_xlabel("Missing sensor (%)")
    ax.set_ylabel("Weighted F1")
    ax.set_title("F1 vs Missing Sensor Rate — XGBoost")
    ax.set_ylim(0, 1.05)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "task7_missing_sensor.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    log("  ✅ Saved: task7_missing_sensor.csv + .png")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("PH-06 EVALUATION — AirGlobal AQI Dataset")
    print("=" * 70)

    df, test_df, X_test_raw, X_test, y_test, labels, n_cls, encoder, preprocessor, models, feature_cols = load_data_and_pipeline()
    log(f"\n✅ Test set: {len(test_df):,} rows | Classes: {labels} | Models loaded: {list(models.keys())}")

    summary   = task1_summary(models, X_test, y_test, labels, n_cls, encoder)
    pred_best, report_df = task2_per_class(models, X_test, y_test, labels, encoder)
    task3_confusion_matrix(models, X_test, y_test, labels, pred_best)
    task4_calibration(models, X_test, y_test, labels, n_cls)
    task5_error_analysis(models, X_test_raw, X_test, y_test, test_df, labels, encoder)
    task6_robustness_by_country(models, preprocessor, feature_cols, df, labels, n_cls, encoder)
    task7_missing_sensor(models, preprocessor, X_test_raw, y_test, feature_cols)


    print("\n" + "=" * 70)
    print("✅ PH-06 DONE")
    print(f"Output folder: {OUTPUT_DIR.relative_to(BASE_DIR)}")
    print("Files saved:")
    for f in sorted(OUTPUT_DIR.glob("*")):
        print(f"  - {f.name}")
    print("=" * 70)


if __name__ == "__main__":
    main()