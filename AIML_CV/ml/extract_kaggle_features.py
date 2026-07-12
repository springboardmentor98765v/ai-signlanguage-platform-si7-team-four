
import os
import cv2
from tqdm import tqdm

from hand_detector import HandDetector
from feature_extractor import FeatureExtractor

DATASET_ROOT = "/content/asl_alphabet_train" 
OUTPUT_CSV = "/content/kaggle_features.csv"
TARGET_LABELS = ["A", "B", "C", "L", "Y"]      # <-- labels come from these folder names
MAX_IMAGES_PER_CLASS = 500                      # cap so this finishes in reasonable time


def main():
    detector = HandDetector()
    extractor = FeatureExtractor()

    header_already_written = os.path.exists(OUTPUT_CSV)
    out_file = open(OUTPUT_CSV, "a")

    if not header_already_written:
        header = extractor.get_feature_names() + ["label"]
        out_file.write(",".join(header) + "\n")

    total_written = 0
    total_skipped = 0

    for label in TARGET_LABELS:
        class_dir = os.path.join(DATASET_ROOT, label)

        if not os.path.isdir(class_dir):
            print(f"Skipping '{label}': folder not found at {class_dir}")
            continue

        image_files = sorted(os.listdir(class_dir))[:MAX_IMAGES_PER_CLASS]

        for filename in tqdm(image_files, desc=f"Class {label}"):
            path = os.path.join(class_dir, filename)
            frame = cv2.imread(path)

            if frame is None:
                total_skipped += 1
                continue

            results = detector.detect_hands(frame)

            if not results.hand_landmarks:
                total_skipped += 1
                continue

            hand = results.hand_landmarks[0]
            features = extractor.extract(hand)

            row = features + [label]
            out_file.write(",".join(str(v) for v in row) + "\n")
            total_written += 1

    out_file.close()

    print(f"\nDone. Rows written: {total_written}")
    print(f"Images skipped (no hand detected / unreadable): {total_skipped}")
    print(f"Saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
