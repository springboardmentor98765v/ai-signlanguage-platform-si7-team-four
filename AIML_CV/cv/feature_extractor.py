import math
import numpy as np


class FeatureExtractor:

    def __init__(self):
        pass

    def distance(self, p1, p2):
        return math.sqrt(
            (p1.x - p2.x) ** 2 +
            (p1.y - p2.y) ** 2 +
            (p1.z - p2.z) ** 2
        )

    def angle(self, a, b, c):

        ba = np.array([a.x - b.x, a.y - b.y, a.z - b.z])
        bc = np.array([c.x - b.x, c.y - b.y, c.z - b.z])

        denom = np.linalg.norm(ba) * np.linalg.norm(bc)
        if denom == 0:
            return 0.0

        cosine = np.dot(ba, bc) / denom
        cosine = np.clip(cosine, -1.0, 1.0)

        return math.degrees(math.acos(cosine))

    def palm_orientation(self, hand):

        wrist = hand[0]
        index_base = hand[5]
        pinky_base = hand[17]

        v1 = np.array([
            index_base.x - wrist.x,
            index_base.y - wrist.y,
            index_base.z - wrist.z
        ])
        v2 = np.array([
            pinky_base.x - wrist.x,
            pinky_base.y - wrist.y,
            pinky_base.z - wrist.z
        ])

        normal = np.cross(v1, v2)
        norm = np.linalg.norm(normal)

        if norm != 0:
            normal = normal / norm

        return normal.tolist()

    def extract(self, hand):

        wrist = hand[0]

        scale = self.distance(wrist, hand[9])
        if scale < 1e-6:
            scale = 1e-6

        features = []

        for lm in hand:
            features.extend([
                (lm.x - wrist.x) / scale,
                (lm.y - wrist.y) / scale,
                (lm.z - wrist.z) / scale
            ])

        thumb = hand[4]
        index = hand[8]
        middle = hand[12]
        ring = hand[16]
        pinky = hand[20]

        fingertip_pairs = [
            (thumb, index),
            (thumb, middle),
            (thumb, ring),
            (thumb, pinky),
            (index, middle),
            (middle, ring),
            (ring, pinky)
        ]

        for p1, p2 in fingertip_pairs:
            features.append(self.distance(p1, p2) / scale)

        finger_joints = [
            (5, 6, 8),     # Index
            (9, 10, 12),   # Middle
            (13, 14, 16),  # Ring
            (17, 18, 20),  # Pinky
            (1, 2, 4)      # Thumb
        ]

        for a, b, c in finger_joints:
            features.append(self.angle(hand[a], hand[b], hand[c]))

        palm = self.palm_orientation(hand)
        features.extend(palm)

        return features

    def get_feature_names(self):
        """Column headers matching the order produced by extract()."""

        names = []

        for i in range(21):
            names.extend([f"lm{i}_x", f"lm{i}_y", f"lm{i}_z"])

        names.extend([
            "dist_thumb_index",
            "dist_thumb_middle",
            "dist_thumb_ring",
            "dist_thumb_pinky",
            "dist_index_middle",
            "dist_middle_ring",
            "dist_ring_pinky"
        ])

        names.extend([
            "angle_index",
            "angle_middle",
            "angle_ring",
            "angle_pinky",
            "angle_thumb"
        ])

        names.extend(["palm_x", "palm_y", "palm_z"])

        return names