#importing libraries
import cv2
import csv
import os
import string

from camera import Camera
from hand_detector import HandDetector
from feature_extractor import FeatureExtractor

# adding labels for all the 26 letters
LABELS = list(string.ascii_uppercase)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "..", "dataset")
RAW_DIR = os.path.join(DATASET_DIR, "raw")
DATASET_PATH = os.path.join(RAW_DIR, "dataset.csv")
LABELS_PATH = os.path.join(DATASET_DIR, "labels.txt")


def ensure_dataset_dir():
    os.makedirs(RAW_DIR, exist_ok=True)


def write_labels_file():
    with open(LABELS_PATH, "w") as f:
        for label in LABELS:
            f.write(label + "\n")


def open_csv_writer(extractor):
    file_exists = os.path.exists(DATASET_PATH)
    csv_file = open(DATASET_PATH, "a", newline="")
    writer = csv.writer(csv_file)

    if not file_exists:
        header = extractor.get_feature_names() + ["label"]
        writer.writerow(header)

    return csv_file, writer