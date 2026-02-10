"""Device detection utility for GPU/CPU services.

Replaces duplicated get_device() across OCR and Embedding services.
"""
import logging

logger = logging.getLogger(__name__)

_device: str | None = None


def get_device() -> str:
    """Get compute device (GPU if available, else CPU). Cached after first call."""
    global _device
    if _device is None:
        try:
            import torch
            _device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            _device = "cpu"
        logger.info(f"Using device: {_device}")
    return _device


def get_torch_dtype():
    """Get appropriate torch dtype based on device.

    Returns float16 for GPU (faster inference), float32 for CPU.
    """
    import torch
    return torch.float16 if get_device() == "cuda" else torch.float32


def is_gpu_available() -> bool:
    """Check if GPU is available without caching the device choice."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False
