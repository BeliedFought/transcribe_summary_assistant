"""
Предзагрузка CUDA-библиотек из pip-пакетов nvidia-* перед импортом ctranslate2.

ctranslate2 (бэкенд faster-whisper) динамически грузит libcublas.so.12, libcudnn
и др. при первом encode на GPU. Библиотеки ставятся в site-packages/nvidia/*/lib
и не находятся стандартным механизмом поиска (нет в LD_LIBRARY_PATH). Изменение
LD_LIBRARY_PATH в рантайме бесполезно для ld.so - он кеширует путь при старте
процесса. Поэтому грузим библиотеки явно через ctypes.CDLL с RTLD_GLOBAL до того,
как ctranslate2 попытается их загрузить.

Использование (вызывать ДО импорта faster_whisper/ctranslate2):
    from src.cuda_loader import preload_cuda_libs
    preload_cuda_libs()
"""

import ctypes
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", message=".*TensorFloat-32.*")
warnings.filterwarnings("ignore", message=".*std.*degrees of freedom.*")

_LOAD_ORDER: tuple[str, ...] = (
    "cuda_runtime",
    "cublas",
    "cudnn",
    "cuda_nvrtc",
)


def _site_packages_dirs() -> list[Path]:
    """Вернуть кандидаты директории site-packages."""
    candidates: list[Path] = []
    for entry in sys.path:
        p = Path(entry)
        if p.name == "site-packages" and p.is_dir():
            candidates.append(p)
    return candidates


def preload_cuda_libs() -> int:
    """
    Предзагрузить CUDA-библиотеки из site-packages/nvidia/*/lib.

    :return: количество загруженных библиотек
    """
    loaded = 0
    for site_pkg in _site_packages_dirs():
        nvidia_root = site_pkg / "nvidia"
        if not nvidia_root.is_dir():
            continue

        for pkg in _LOAD_ORDER:
            lib_dir = nvidia_root / pkg / "lib"
            if not lib_dir.is_dir():
                continue
            for so in sorted(lib_dir.glob("*.so*")):
                try:
                    ctypes.CDLL(str(so), mode=ctypes.RTLD_GLOBAL)
                    loaded += 1
                except OSError:
                    pass
    return loaded
