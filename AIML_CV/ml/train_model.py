#importing libraries
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

#Directory paths
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

# model training : model parameter specification
def load_data():
    frames = []
    for path in [WEBCAM_CSV, KAGGLE_CSV]:
        try:
            frames.append(pd.read_csv(path))
        except FileNotFoundError:
            print(f"Warning: {path} not found, skipping")

    if not frames:
        raise RuntimeError("No dataset files found — check your paths")

    df = pd.concat(frames, ignore_index=True)
    df = df.dropna()   # drop any rows with invalid/missing values
    return df


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

# model comparrision and selection 
def main():
    df = load_data()
    print("Total samples:", len(df))
    print(df["label"].value_counts())
    print()

    X = df.drop(columns=["label"])

    encoder = LabelEncoder()
    y = encoder.fit_transform(df["label"])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

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

    # Confusion matrix
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

    joblib.dump({
        "pipeline": best["pipeline"],
        "label_encoder": encoder
    }, MODEL_OUT)
    print(f"Saved to {MODEL_OUT}")


if __name__ == "__main__":
    main()

    try:
        from google.colab import files
        files.download(MODEL_OUT)
    except ImportError:
        pass