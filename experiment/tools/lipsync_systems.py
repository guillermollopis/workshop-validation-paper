"""
Lipsync system wrappers.

Each function takes a source video/image + driving audio and produces an output video.
All paths are resolved to absolute before subprocess calls.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


def _resolve(p):
    """Resolve a path to absolute."""
    return str(Path(p).resolve())


def _run_cmd(cmd: list[str], cwd: str = None, timeout: int = 600,
             env: dict = None) -> bool:
    """Run a shell command and return success status."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout,
            env=env,
        )
        if result.returncode != 0:
            print(f"    STDERR: {result.stderr[:500]}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"    [TIMEOUT] Command took > {timeout}s")
        return False
    except Exception as e:
        print(f"    [ERROR] {e}")
        return False


def _validate_checkpoints(paths: dict[str, str]) -> bool:
    """Check that all checkpoint files exist."""
    for name, path in paths.items():
        if not Path(path).exists():
            print(f"    [ERROR] Checkpoint not found: {name} -> {path}")
            return False
    return True


def lipsync_wav2lip(source_video: str, driving_audio: str, output_path: str,
                     gpu: bool = True, repo_dir: str = "tools/repos/Wav2Lip",
                     config: dict = None) -> bool:
    """Generate lip-synced video using Wav2Lip."""
    repo = Path(repo_dir).resolve()
    cfg = config or {}

    # Checkpoint locations
    checkpoint = Path(cfg.get("checkpoint",
                               repo / "checkpoints" / "wav2lip_gan.pth")).resolve()
    face_det = Path(cfg.get("face_det_checkpoint",
                             repo / "face_detection" / "detection" / "sfd" / "s3fd.pth")).resolve()

    if not checkpoint.exists():
        print(f"    [ERROR] Wav2Lip checkpoint not found: {checkpoint}")
        print("    Download wav2lip_gan.pth and place in checkpoints/")
        return False

    env = None
    if not gpu:
        env = {**os.environ, "CUDA_VISIBLE_DEVICES": ""}

    cmd = [
        sys.executable, str(repo / "inference.py"),
        "--checkpoint_path", str(checkpoint),
        "--face", _resolve(source_video),
        "--audio", _resolve(driving_audio),
        "--outfile", _resolve(output_path),
    ]

    return _run_cmd(cmd, cwd=str(repo), env=env)


def lipsync_sadtalker(source_image: str, driving_audio: str, output_path: str,
                       gpu: bool = True, repo_dir: str = "tools/repos/SadTalker",
                       config: dict = None) -> bool:
    """Generate talking head video using SadTalker."""
    repo = Path(repo_dir).resolve()
    cfg = config or {}
    output_path = Path(output_path).resolve()
    output_dir = output_path.parent / "sadtalker_tmp"
    output_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_dir = Path(cfg.get("checkpoint_dir",
                                   repo / "checkpoints")).resolve()
    size = cfg.get("size", 512)

    cmd = [
        sys.executable, str(repo / "inference.py"),
        "--driven_audio", _resolve(driving_audio),
        "--source_image", _resolve(source_image),
        "--result_dir", str(output_dir),
        "--checkpoint_dir", str(checkpoint_dir),
        "--size", str(size),
        "--still",
        "--preprocess", "crop",
    ]
    if not gpu:
        cmd.append("--cpu")

    success = _run_cmd(cmd, cwd=str(repo))

    if success:
        results = list(output_dir.glob("**/*.mp4"))
        if results:
            shutil.move(str(results[0]), str(output_path))
            shutil.rmtree(str(output_dir), ignore_errors=True)
            return True

    return False


def lipsync_video_retalking(source_video: str, driving_audio: str, output_path: str,
                             gpu: bool = True,
                             repo_dir: str = "tools/repos/video-retalking",
                             config: dict = None) -> bool:
    """Generate lip-synced video using VideoReTalking."""
    repo = Path(repo_dir).resolve()
    cfg = config or {}
    ckpt_dir = Path(cfg.get("checkpoint_dir", repo / "checkpoints")).resolve()

    # VideoReTalking expects specific checkpoint files
    expected_ckpts = {
        "DNet.pt": ckpt_dir / "DNet.pt",
        "LNet.pth": ckpt_dir / "LNet.pth",
        "ENet.pth": ckpt_dir / "ENet.pth",
        "face3d_net.pth": ckpt_dir / "face3d_pretrain_epoch_20.pth",
        "expression.mat": ckpt_dir / "expression.mat",
        "shape_predictor": ckpt_dir / "shape_predictor_68_face_landmarks.dat",
    }

    # Only validate critical ones
    critical = ["DNet.pt", "LNet.pth", "ENet.pth"]
    missing = [k for k in critical if not expected_ckpts[k].exists()]
    if missing:
        print(f"    [ERROR] VideoReTalking checkpoints missing: {missing}")
        print(f"    Expected in: {ckpt_dir}")
        return False

    cmd = [
        sys.executable, str(repo / "inference.py"),
        "--face", _resolve(source_video),
        "--audio", _resolve(driving_audio),
        "--outfile", _resolve(output_path),
    ]

    # Add checkpoint paths if they exist
    if expected_ckpts["DNet.pt"].exists():
        cmd.extend(["--DNet_path", str(expected_ckpts["DNet.pt"])])
    if expected_ckpts["LNet.pth"].exists():
        cmd.extend(["--LNet_path", str(expected_ckpts["LNet.pth"])])
    if expected_ckpts["ENet.pth"].exists():
        cmd.extend(["--ENet_path", str(expected_ckpts["ENet.pth"])])
    if expected_ckpts["face3d_net.pth"].exists():
        cmd.extend(["--face3d_net_path", str(expected_ckpts["face3d_net.pth"])])

    return _run_cmd(cmd, cwd=str(repo))


def lipsync_musetalk(source_video: str, driving_audio: str, output_path: str,
                      gpu: bool = True, repo_dir: str = "tools/repos/MuseTalk",
                      config: dict = None) -> bool:
    """Generate lip-synced video using MuseTalk.

    Creates a temporary inference config YAML and invokes via module (-m).
    Supports MuseTalk v1.5+ with required model path arguments.
    """
    repo = Path(repo_dir).resolve()
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a temporary inference config for MuseTalk
    inference_config = {
        "task_0": {
            "video_path": _resolve(source_video),
            "audio_path": _resolve(driving_audio),
            "bbox_shift": 0,
        }
    }

    # Write temp config
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", dir=str(repo),
                                      delete=False, prefix="inf_cfg_") as f:
        yaml.dump(inference_config, f)
        tmp_config_path = f.name

    results_dir = output_path.parent / "musetalk_tmp"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Detect model version and paths
    models_dir = repo / "models"
    unet_v15 = models_dir / "musetalkV15" / "unet.pth"
    unet_v1 = models_dir / "musetalk" / "pytorch_model.bin"

    if unet_v15.exists():
        version = "v15"
        unet_path = str(unet_v15)
        unet_config = str(models_dir / "musetalkV15" / "musetalk.json")
    elif unet_v1.exists():
        version = "v1"
        unet_path = str(unet_v1)
        unet_config = str(models_dir / "musetalk" / "musetalk.json")
    else:
        # Try HuggingFace cache location
        hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
        print(f"    [ERROR] MuseTalk model not found in {models_dir}")
        print(f"    Run: huggingface-cli download TMElyralab/MuseTalk --local-dir {models_dir}")
        os.unlink(tmp_config_path)
        return False

    # Find ffmpeg path
    ffmpeg_path = shutil.which("ffmpeg") or "ffmpeg"

    try:
        # Use module invocation (-m) for correct imports
        cmd = [
            sys.executable, "-m", "scripts.inference",
            "--inference_config", tmp_config_path,
            "--result_dir", str(results_dir),
            "--unet_model_path", unet_path,
            "--version", version,
            "--ffmpeg_path", ffmpeg_path,
        ]

        # Add unet config if it exists
        if Path(unet_config).exists():
            cmd.extend(["--unet_config", unet_config])

        success = _run_cmd(cmd, cwd=str(repo))

        if success:
            # MuseTalk saves output with auto-generated names; find and move it
            search_dirs = [results_dir, repo / "results"]
            for search_dir in search_dirs:
                if search_dir.exists():
                    results = sorted(search_dir.glob("**/*.mp4"),
                                     key=lambda p: p.stat().st_mtime, reverse=True)
                    if results:
                        shutil.move(str(results[0]), str(output_path))
                        # Cleanup temp results
                        shutil.rmtree(str(results_dir), ignore_errors=True)
                        return True

        return False

    finally:
        # Cleanup temp config
        if os.path.exists(tmp_config_path):
            os.unlink(tmp_config_path)


def standardize_output(input_path: str, output_path: str, fps: int = 25,
                        resolution: tuple = (512, 512)):
    """Standardize generated video to consistent format."""
    w, h = resolution
    cmd = [
        "ffmpeg", "-y", "-i", _resolve(input_path),
        "-r", str(fps),
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
               f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "128k",
        _resolve(output_path),
    ]
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        return True
    except Exception:
        return False


# Registry of all lipsync systems
LIPSYNC_SYSTEMS = {
    "wav2lip": {
        "name": "Wav2Lip",
        "func": lipsync_wav2lip,
        "input_type": "video",
    },
    "sadtalker": {
        "name": "SadTalker",
        "func": lipsync_sadtalker,
        "input_type": "image",
    },
    "video_retalking": {
        "name": "VideoReTalking",
        "func": lipsync_video_retalking,
        "input_type": "video",
    },
    "musetalk": {
        "name": "MuseTalk",
        "func": lipsync_musetalk,
        "input_type": "video",
    },
}


def get_enabled_systems(config: dict) -> dict:
    """Return only enabled lipsync systems from config."""
    enabled = {}
    for key, system in LIPSYNC_SYSTEMS.items():
        if config.get("lipsync_systems", {}).get(key, {}).get("enabled", False):
            enabled[key] = system
    return enabled
