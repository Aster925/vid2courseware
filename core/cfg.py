# -*- coding: utf-8 -*-
"""Tiny config loader shared by the core scripts.

Loads config.yaml if present; every value can be overridden by CLI flags in
the individual scripts. Keeping this minimal on purpose — no framework.
"""
import os
import sys

try:
    import yaml
except ImportError:
    yaml = None


def load_config(path="config.yaml"):
    if not os.path.exists(path):
        return {}
    if yaml is None:
        sys.exit("PyYAML not installed — run: pip install pyyaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def add_cuda_dlls():
    """Let CTranslate2 find pip-installed CUDA DLLs (cuBLAS / cuDNN) on Windows.

    Harmless no-op if the nvidia-* packages aren't installed (e.g. CPU-only).
    """
    try:
        import nvidia  # namespace package
        base = list(nvidia.__path__)[0]
        for sub in ("cublas", "cudnn"):
            d = os.path.join(base, sub, "bin")
            if os.path.isdir(d):
                os.add_dll_directory(d)
                os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
    except Exception:
        pass
