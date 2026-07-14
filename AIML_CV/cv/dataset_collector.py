import cv2
import csv
import os

from camera import Camera
from hand_detector import HandDetector
from feature_extractor import FeatureExtractor

LABELS = ["A", "B", "C", "L", "Y"]

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


def main():
    ensure_dataset_dir()
    write_labels_file()

    camera = Camera()
    detector = HandDetector()
    extractor = FeatureExtractor()
    csv_file, writer = open_csv_writer(extractor)

    current_label_index = 0
    counts = {label: 0 for label in LABELS}

    print("Controls:")
    print(f"  1-{len(LABELS)} : select label ({', '.join(LABELS)})")
    print("  c     : capture current frame as a labeled sample")
    print("  q     : quit\n")

    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                print("Failed to get frame")
                break

            results = detector.detect_hands(frame)
            frame = detector.draw_landmarks(frame, results)

            current_label = LABELS[current_label_index]
            overlay = f"Label: {current_label}  |  Count: {counts[current_label]}  |  1-{len(LABELS)}=select  c=capture  q=quit"
            cv2.putText(
                frame, overlay, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
            )

            cv2.imshow("Dataset Collector", frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break

            if ord('1') <= key <= ord(str(len(LABELS))):
                current_label_index = key - ord('1')

            if key == ord('c'):
                if results.hand_landmarks:
                    hand = results.hand_landmarks[0]
                    features = extractor.extract(hand)
                    writer.writerow(features + [current_label])
                    csv_file.flush()
                    counts[current_label] += 1
                    print(f"Captured '{current_label}' (total: {counts[current_label]})")
                else:
                    print("No hand detected — sample not saved")

    finally:
        csv_file.close()
        camera.release()
        detector.close() if hasattr(detector, "close") else None
        cv2.destroyAllWindows()

        print("\nSamples collected this session:")
        for label, count in counts.items():
            print(f"  {label}: {count}")


if __name__ == "__main__":
    main()
