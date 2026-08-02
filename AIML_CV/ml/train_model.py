import os
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
import joblib

# Directory paths
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("xgboost not installed — skipping it (pip install xgboost to include)")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_RAW_DIR = os.path.join(BASE_DIR, "..", "dataset", "raw")
ML_DIR = os.path.join(BASE_DIR, "..", "ml")

WEBCAM_CSV = os.path.join(DATASET_RAW_DIR, "dataset.csv")
KAGGLE_CSV = os.path.join(DATASET_RAW_DIR, "kaggle_features.csv")
MODEL_OUT = os.path.join(ML_DIR, "sign_model.joblib")
CONFUSION_MATRIX_OUT = os.path.join(ML_DIR, "confusion_matrix.png")

WEBCAM_TARGET_SHARE = 0.35


def load_data():
    sources = {WEBCAM_CSV: "webcam", KAGGLE_CSV: "kaggle"}
    frames = []

    for path, source in sources.items():
        try:
            frame = pd.read_csv(path)
            frame["label"] = frame["label"].astype(str).str.strip()
            frame["_source"] = source
            frames.append(frame)
        except FileNotFoundError:
            print(f"Warning: {path} not found, skipping")

    if not frames:
        raise RuntimeError("No dataset files found — check your paths")

    df = pd.concat(frames, ignore_index=True)
    df = df.dropna()
    return df  # keep "_source" column — needed by oversample_webcam()


def oversample_webcam(df):
    webcam_df = df[df["_source"] == "webcam"]
    kaggle_df = df[df["_source"] == "kaggle"]

    if len(webcam_df) > 0 and len(kaggle_df) > 0:
        factor = (WEBCAM_TARGET_SHARE * len(kaggle_df)) / \
                 ((1 - WEBCAM_TARGET_SHARE) * len(webcam_df))
        factor = max(1, round(factor))

        webcam_oversampled = pd.concat([webcam_df] * factor, ignore_index=True)
        print(f"Oversampling webcam data {factor}x "
              f"({len(webcam_df)} -> {len(webcam_oversampled)} rows) so it isn't "
              f"drowned out by {len(kaggle_df)} Kaggle rows")
        df = pd.concat([webcam_oversampled, kaggle_df], ignore_index=True)

    return df.drop(columns=["_source"])


def build_models():
    models = {
        "KNN": Pipeline([
            ("scale", StandardScaler()),
            ("clf", KNeighborsClassifier(n_neighbors=5))
        ]),
        "RandomForest": Pipeline([
            ("scale", StandardScaler()),
            ("clf", RandomForestClassifier(n_estimators=200, random_state=42))
        ]),
        "SVM": Pipeline([
            ("scale", StandardScaler()),
            ("clf", SVC(kernel="rbf", probability=True, random_state=42))
        ]),
    }

    if XGBOOST_AVAILABLE:
        models["XGBoost"] = Pipeline([
            ("scale", StandardScaler()),
            ("clf", XGBClassifier(
                n_estimators=200,
                use_label_encoder=False,
                eval_metric="mlogloss",
                random_state=42
            ))
        ])

    return models


def main():
    df = load_data()
    print("Total raw samples:", len(df))
    print(df["label"].value_counts())
    print()

    X_raw = df.drop(columns=["label", "_source"])
    encoder = LabelEncoder()
    y_raw = encoder.fit_transform(df["label"])

   # splitting before oversampling to fix the leakage issue
    X_train_raw, X_test, y_train_raw, y_test = train_test_split(
        X_raw, y_raw, test_size=0.2, stratify=y_raw, random_state=42
    )

    # Reattach label + source (needed by oversample_webcam) to the
    # training portion only, then oversample just that portion.
    train_df = X_train_raw.copy()
    train_df["label"] = encoder.inverse_transform(y_train_raw)
    train_df["_source"] = df.loc[X_train_raw.index, "_source"].values

    train_df = oversample_webcam(train_df)

    X_train = train_df.drop(columns=["label"])
    y_train = encoder.transform(train_df["label"])

    print("Training samples after oversampling:", len(X_train))
    print("Test samples (untouched, no oversampling):", len(X_test))
    print()

    models = build_models()
    results = []

    for name, pipeline in models.items():
        print(f"--- {name} ---")

        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring="accuracy")

        pipeline.fit(X_train, y_train)
        preds = pipeline.predict(X_test)
        test_acc = accuracy_score(y_test, preds)

        print(f"CV accuracy (train set):  {cv_scores.mean():.4f} +/- {cv_scores.std():.4f}")
        print(f"Held-out test accuracy:   {test_acc:.4f}")
        print(classification_report(y_test, preds, target_names=encoder.classes_))
        print()

        results.append({
            "name": name,
            "pipeline": pipeline,
            "cv_mean": cv_scores.mean(),
            "test_acc": test_acc
        })

    print("=== Comparison summary ===")
    results_sorted = sorted(results, key=lambda r: r["test_acc"], reverse=True)
    for r in results_sorted:
        print(f"{r['name']:15s}  CV: {r['cv_mean']:.4f}   Test: {r['test_acc']:.4f}")

    best = results_sorted[0]
    print(f"\nBest model: {best['name']} (test accuracy {best['test_acc']:.4f})")

    os.makedirs(ML_DIR, exist_ok=True)

    # Confusion matrix (built from the untouched, honest test set)
    best_preds = best["pipeline"].predict(X_test)
    cm = confusion_matrix(y_test, best_preds, labels=encoder.transform(encoder.classes_))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=encoder.classes_)
    fig, ax = plt.subplots(figsize=(max(8, len(encoder.classes_) * 0.5),
                                     max(8, len(encoder.classes_) * 0.5)))
    disp.plot(ax=ax, xticks_rotation="vertical", colorbar=False)
    plt.title(f"Confusion matrix — {best['name']}")
    plt.tight_layout()
    plt.savefig(CONFUSION_MATRIX_OUT)
    print(f"Confusion matrix saved to {CONFUSION_MATRIX_OUT}")

    per_class_recall = cm.diagonal() / cm.sum(axis=1)
    weak_letters = sorted(
        zip(encoder.classes_, per_class_recall), key=lambda x: x[1]
    )
    print("\nWeakest letters (lowest recall):")
    for letter, recall in weak_letters[:5]:
        print(f"  {letter}: {recall:.2f}")

    
    interpretable_prefixes = ("dist_", "angle_")
    interpretable_names = [c for c in X_raw.columns if c.startswith(interpretable_prefixes)]
    interpretable_idx = [X_train_raw.columns.get_loc(c) for c in interpretable_names]

    scaler = best["pipeline"].named_steps["scale"]
    X_train_raw_scaled = scaler.transform(X_train_raw)

    centroids = {}
    for class_idx, class_label in enumerate(encoder.classes_):
        rows = X_train_raw_scaled[y_train_raw == class_idx][:, interpretable_idx]
        centroids[class_label] = dict(zip(interpretable_names, rows.mean(axis=0)))

    joblib.dump({
        "pipeline": best["pipeline"],
        "label_encoder": encoder,
        "interpretable_centroids": centroids,
        "interpretable_feature_names": interpretable_names
    }, MODEL_OUT)
    print(f"Saved to {MODEL_OUT}")


if __name__ == "__main__":
    main()

    try:
        from google.colab import drive
        import shutil
        drive.mount('/content/drive', force_remount=False)
        drive_dest = '/content/drive/MyDrive/sign_model.joblib'
        shutil.copy(MODEL_OUT, drive_dest)
        print(f"Also copied to Google Drive: {drive_dest}")
    except ImportError:
        pass  # not running in Colab
    except Exception as e:
        print(f"Could not save to Google Drive: {e}")
