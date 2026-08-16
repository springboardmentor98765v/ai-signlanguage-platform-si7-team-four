# AIML Prediction Service — API Reference

Liveness + prediction endpoints exposed by the Python AI service
(`AIML_CV/api/main.py`, runs on port **8001**).

---

## Endpoints

### `GET /health`
Liveness check.

- Returns: `{"status": "ok"}`

---

### `POST /predict`
Static letter recognition (A–Z, everything except J/Z). Multipart file upload.

**Form fields:**
- `file` — the image (multipart), **required**
- `target_sign` — expected letter (optional). Practice mode.

**Responses:**
- Without `target_sign`: returns `predicted_sign`, `confidence`, `hand_detected`.
- With `target_sign` (practice mode): also returns `correct` and `possible_issue`
  — a plain-language hint (e.g. *"Your thumb bend looks off for 'N'"*), or `null`
  if there's no meaningful issue.

---

### `POST /predict_dynamic`
Dynamic sign recognition — for **J, Z, and word signs** (hello, no, please,
thank_you, yes). Multipart file upload of **a list of frames** (`files`) captured
over a recording burst — NOT a single image.

**Form fields:**
- `files` — multiple multipart frames (the burst), **required**

**Returns:**
- `predicted_sign`, `matched`, `confidence`, `distance`,
  `hand_detected_frames`, `total_frames`.
- `predicted_sign` is `null` whenever `matched` is `false` — either no template
  matched within threshold, or too few frames had a detectable hand (< 5 frames
  or < 50% detection rate). Check `hand_detected_frames` vs. `total_frames` to
  distinguish a bad burst from a genuine no-match.
- `confidence` is derived from DTW distance (not a classifier probability like
  `/predict`'s) — 1.0 at a perfect match, 0.5 at the threshold boundary,
  decaying exponentially beyond that.

---

## Running

```bash
uvicorn main:app --reload --port 8001   # from api/
```

Port **8001** matches `docker-compose.yml`. Interactive docs at:
`http://127.0.0.1:8001/docs`