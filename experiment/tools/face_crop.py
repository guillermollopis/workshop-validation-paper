"""
Face cropping utilities using MediaPipe face detection.

Two-pass approach:
  1. Detect face bounding boxes in all frames
  2. Smooth bounding boxes temporally, then crop + resize to target size

Falls back to center crop if face detection rate is below threshold.
"""

import os
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np


# ---------- Constants ----------
_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite"
_MODEL_DIR = Path(__file__).resolve().parent / "models"
_MODEL_PATH = _MODEL_DIR / "blaze_face_short_range.tflite"

DEFAULT_PADDING = 1.5
DEFAULT_SMOOTH_WINDOW = 7
DEFAULT_TARGET_SIZE = (512, 512)
MIN_DETECTION_RATE = 0.3


def _ensure_model():
    """Download the mediapipe face detection model if not present."""
    if _MODEL_PATH.exists():
        return _MODEL_PATH
    _MODEL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"  Downloading mediapipe face detector to {_MODEL_PATH}...")
    import urllib.request
    urllib.request.urlretrieve(_MODEL_URL, str(_MODEL_PATH))
    return _MODEL_PATH


def _create_detector():
    """Create a MediaPipe face detector using the Tasks API."""
    import mediapipe as mp

    model_path = str(_ensure_model())
    base_options = mp.tasks.BaseOptions(model_asset_path=model_path)
    options = mp.tasks.vision.FaceDetectorOptions(
        base_options=base_options,
        min_detection_confidence=0.5,
    )
    return mp.tasks.vision.FaceDetector.create_from_options(options)


def _smooth_boxes(boxes, window=DEFAULT_SMOOTH_WINDOW):
    """Apply moving-average smoothing to bounding box coordinates.

    boxes: list of (x, y, w, h) or None for frames with no detection.
    Returns: list of (x, y, w, h) with Nones interpolated/smoothed.
    """
    if not boxes:
        return boxes

    # Convert to array, mark missing frames
    n = len(boxes)
    arr = np.zeros((n, 4), dtype=np.float64)
    valid = np.zeros(n, dtype=bool)

    for i, box in enumerate(boxes):
        if box is not None:
            arr[i] = box
            valid[i] = True

    if not np.any(valid):
        return [None] * n

    # Interpolate missing frames
    valid_indices = np.where(valid)[0]
    for dim in range(4):
        arr[:, dim] = np.interp(
            np.arange(n),
            valid_indices,
            arr[valid_indices, dim],
        )

    # Moving average smoothing
    half_w = window // 2
    smoothed = np.zeros_like(arr)
    for i in range(n):
        lo = max(0, i - half_w)
        hi = min(n, i + half_w + 1)
        smoothed[i] = arr[lo:hi].mean(axis=0)

    return [tuple(smoothed[i]) for i in range(n)]


def _detect_faces_pass(video_path, detector):
    """Pass 1: Detect face bounding boxes in every frame.

    Returns list of (x_center, y_center, w, h) or None per frame,
    plus the video dimensions (frame_w, frame_h) and fps.
    """
    import mediapipe as mp

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    boxes = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = detector.detect(mp_image)

        if result.detections:
            # Use the first (highest-confidence) detection
            det = result.detections[0]
            bbox = det.bounding_box
            cx = bbox.origin_x + bbox.width / 2
            cy = bbox.origin_y + bbox.height / 2
            boxes.append((cx, cy, bbox.width, bbox.height))
        else:
            boxes.append(None)

    cap.release()
    return boxes, frame_w, frame_h, fps


def _crop_frame(frame, cx, cy, size, frame_w, frame_h, padding):
    """Crop a square region centered at (cx, cy) with given padding, then resize."""
    target_w, target_h = size
    # Square side = max(w, h) * padding — but we use a fixed square from the bbox
    half = int(max(frame_w, frame_h) * 0.5)  # will be overridden below

    # We receive the smoothed bbox center; compute crop radius from bbox size embedded in caller
    # Actually, use the provided size directly
    x1 = int(cx - half)
    y1 = int(cy - half)
    x2 = int(cx + half)
    y2 = int(cy + half)

    # Clamp to frame
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(frame_w, x2)
    y2 = min(frame_h, y2)

    crop = frame[y1:y2, x1:x2]
    if crop.size == 0:
        crop = frame  # fallback
    return cv2.resize(crop, (target_w, target_h))


def crop_video(input_path, output_path, target_size=DEFAULT_TARGET_SIZE,
               padding=DEFAULT_PADDING, smooth_window=DEFAULT_SMOOTH_WINDOW):
    """Crop video to face region, re-encode with ffmpeg keeping audio.

    Two-pass: detect all face bboxes, smooth temporally, then crop+resize.
    Falls back to center crop if detection rate < MIN_DETECTION_RATE.

    Args:
        input_path: Source video path
        output_path: Destination path (.mp4)
        target_size: (width, height) tuple
        padding: Multiplier on face bbox to get crop region
        smooth_window: Moving average window for bbox smoothing
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    detector = _create_detector()

    # Pass 1: detect faces
    raw_boxes, frame_w, frame_h, fps = _detect_faces_pass(input_path, detector)
    detector.close()

    n_frames = len(raw_boxes)
    if n_frames == 0:
        print(f"    [WARN] No frames read from {input_path}")
        return False

    n_detected = sum(1 for b in raw_boxes if b is not None)
    det_rate = n_detected / n_frames

    use_face_crop = det_rate >= MIN_DETECTION_RATE

    if not use_face_crop:
        print(f"    [WARN] Low face detection rate ({det_rate:.1%}), using center crop")

    # Pass 2: smooth boxes and crop frames to a temp video (no audio)
    if use_face_crop:
        smoothed = _smooth_boxes(raw_boxes, smooth_window)
    else:
        smoothed = None

    target_w, target_h = target_size

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_video = tmp.name

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(tmp_video, fourcc, fps, (target_w, target_h))

    cap = cv2.VideoCapture(str(input_path))
    idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if use_face_crop and smoothed and idx < len(smoothed) and smoothed[idx] is not None:
            cx, cy, bw, bh = smoothed[idx]
            # Square crop side = max(bw, bh) * padding
            side = max(bw, bh) * padding
            half = side / 2

            x1 = int(max(0, cx - half))
            y1 = int(max(0, cy - half))
            x2 = int(min(frame_w, cx + half))
            y2 = int(min(frame_h, cy + half))

            crop = frame[y1:y2, x1:x2]
            if crop.size == 0:
                crop = frame
            cropped = cv2.resize(crop, (target_w, target_h))
        else:
            # Center crop: take the largest centered square
            min_dim = min(frame_w, frame_h)
            x1 = (frame_w - min_dim) // 2
            y1 = (frame_h - min_dim) // 2
            crop = frame[y1:y1 + min_dim, x1:x1 + min_dim]
            cropped = cv2.resize(crop, (target_w, target_h))

        writer.write(cropped)
        idx += 1

    cap.release()
    writer.release()

    # Mux: combine cropped video with original audio using ffmpeg
    cmd = [
        "ffmpeg", "-y",
        "-i", tmp_video,
        "-i", str(input_path),
        "-map", "0:v:0",
        "-map", "1:a:0?",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        str(output_path),
    ]
    try:
        subprocess.run(cmd, capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        # If no audio stream, try video-only
        cmd_no_audio = [
            "ffmpeg", "-y", "-i", tmp_video,
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            str(output_path),
        ]
        subprocess.run(cmd_no_audio, capture_output=True, check=True)
    finally:
        os.unlink(tmp_video)

    return True


def extract_reference_frame(video_path, frame_path, timestamp_sec=2.0,
                            target_size=DEFAULT_TARGET_SIZE,
                            padding=DEFAULT_PADDING):
    """Extract a single face-cropped frame from a video at ~timestamp_sec.

    Used as the reference face image for lipsync systems that need a still.
    """
    video_path = Path(video_path)
    frame_path = Path(frame_path)
    frame_path.parent.mkdir(parents=True, exist_ok=True)

    detector = _create_detector()

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    target_frame = int(timestamp_sec * fps)
    target_w, target_h = target_size

    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        # Fallback: try frame 0
        cap = cv2.VideoCapture(str(video_path))
        ret, frame = cap.read()
        cap.release()
        if not ret:
            detector.close()
            return False

    # Detect face in this frame
    import mediapipe as mp
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = detector.detect(mp_image)
    detector.close()

    if result.detections:
        det = result.detections[0]
        bbox = det.bounding_box
        cx = bbox.origin_x + bbox.width / 2
        cy = bbox.origin_y + bbox.height / 2
        side = max(bbox.width, bbox.height) * padding
        half = side / 2

        x1 = int(max(0, cx - half))
        y1 = int(max(0, cy - half))
        x2 = int(min(frame_w, cx + half))
        y2 = int(min(frame_h, cy + half))

        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            crop = frame
    else:
        # Center crop fallback
        min_dim = min(frame_w, frame_h)
        x1 = (frame_w - min_dim) // 2
        y1 = (frame_h - min_dim) // 2
        crop = frame[y1:y1 + min_dim, x1:x1 + min_dim]

    cropped = cv2.resize(crop, (target_w, target_h))
    cv2.imwrite(str(frame_path), cropped)
    return True
