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