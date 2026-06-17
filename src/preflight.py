"""
Pre-flight проверки готовности пайплайна перед обработкой.

Проверяет перед запуском основной логики:
- целостность скачанных моделей (whisper, pyannote) с авто-доустановкой;
- доступность DeepSeek API;
- доступность HuggingFace Hub и валидность HF_TOKEN.

Использование:
    from src.preflight import check_all
    errors = check_all(config)
    if errors:
        sys.exit(1)
"""

import os
import threading
import urllib.error
import urllib.request
from configparser import ConfigParser
from typing import Any, Callable

from src.localization import t


_TIMEOUT_MODEL_DOWNLOAD_SEC = 1800
_TIMEOUT_API_SEC = 15

_WHISPER_REQUIRED_FILES: tuple[str, ...] = (
    "config.json",
    "preprocessor_config.json",
    "tokenizer.json",
    "vocabulary.json",
    "model.bin",
)


def _log(msg: str) -> None:
    from src.logger import get_logger
    get_logger("preflight", log_dir=_log_dir()).info(msg)


def _log_err(msg: str) -> None:
    from src.logger import get_logger
    get_logger("preflight", log_dir=_log_dir()).error(msg)


def _log_dir() -> Any:
    from src.config import PROJECT_ROOT
    return PROJECT_ROOT / "log"


def check_all(config: ConfigParser) -> list[str]:
    """
    Выполнить все pre-flight проверки и вернуть список ошибок.

    :param config: ConfigParser проекта
    :return: список строк-ошибок (пустой список = всё в порядке)
    """
    _log(t("msg.preflight_start"))

    errors: list[str] = []

    err = check_whisper_model(config)
    if err:
        errors.append(err)

    if config.getboolean("diarization", "enabled", fallback=True):
        err = check_pyannote_model(config)
        if err:
            errors.append(err)

        err = check_pyannote_segmentation_model(config)
        if err:
            errors.append(err)

        err = check_pyannote_community_model(config)
        if err:
            errors.append(err)

    err = check_deepseek_api(config)
    if err:
        errors.append(err)

    err = check_huggingface_hub(config)
    if err:
        errors.append(err)

    if errors:
        for e in errors:
            _log_err(e)
        _log_err(t("error.preflight_failed"))
    else:
        _log(t("msg.preflight_summary_ok"))

    return errors


def _missing_files(repo_id: str) -> list[str]:
    """Вернуть список отсутствующих обязательных файлов модели в кеше HF."""
    from huggingface_hub import try_to_load_from_cache

    required = _WHISPER_REQUIRED_FILES
    missing: list[str] = []
    for filename in required:
        path = try_to_load_from_cache(repo_id, filename)
        if not path:
            missing.append(filename)
    return missing


def _call_with_timeout(func: Callable[[], Any], timeout: int) -> Any:
    """
    Выполнить func в отдельном потоке с жестким таймаутом.

    :raises TimeoutError: если func не уложился в timeout
    """
    result: dict[str, Any] = {}

    def _worker() -> None:
        try:
            result["value"] = func()
        except Exception as exc:
            result["error"] = exc

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        raise TimeoutError(f"call exceeded {timeout} sec")
    if "error" in result:
        raise result["error"]
    return result.get("value")


def _download_with_timeout(repo_id: str, token: str, timeout: int) -> None:
    """
    Доустановить модель через snapshot_download с жестким таймаутом.

    Xet-бэкенд отключается принудительно, так как в huggingface_hub 1.19 он
    может зависать на крупных моделях (зависание на сетевом уровне).
    :raises TimeoutError: если скачивание не уложилось в timeout
    :raises Exception: ошибка сети/доступа
    """
    import huggingface_hub.constants
    from huggingface_hub import snapshot_download

    huggingface_hub.constants.HF_HUB_DISABLE_XET = True

    _call_with_timeout(
        lambda: snapshot_download(repo_id=repo_id, token=token or None),
        timeout,
    )


def _handle_model_download_error(
    repo_id: str, exc: Exception, is_pyannote: bool
) -> str:
    """Сформировать человекочитаемое сообщение об ошибке загрузки модели."""
    from huggingface_hub.errors import GatedRepoError

    if isinstance(exc, GatedRepoError):
        url = f"https://huggingface.co/{repo_id}"
        _log_err(t("msg.preflight_gated", repo=repo_id, url=url))
        if is_pyannote:
            _log_err(t("msg.preflight_gated_pyannote"))
        return t("msg.preflight_gated", repo=repo_id, url=url)
    _log_err(
        t(
            "msg.preflight_model_download_failed",
            model=repo_id,
            timeout=_TIMEOUT_MODEL_DOWNLOAD_SEC,
            detail=str(exc),
        )
    )
    _log(t("msg.preflight_model_manual", repo=repo_id))
    return t(
        "msg.preflight_model_download_failed",
        model=repo_id,
        timeout=_TIMEOUT_MODEL_DOWNLOAD_SEC,
        detail=str(exc),
    )


def check_whisper_model(config: ConfigParser) -> str | None:
    """
    Проверить целостность модели faster-whisper в кеше HF.

    При отсутствии файлов пытается доустановить модель.
    :return: строка ошибки или None
    """
    model_size = config.get("whisper", "model_size", fallback="large-v3")
    repo_id = f"Systran/faster-whisper-{model_size}"
    token = os.environ.get("HF_TOKEN", "")

    _log(t("msg.preflight_model_checking", model=repo_id))

    missing = _missing_files(repo_id)
    if not missing:
        _log(t("msg.preflight_model_ok", model=repo_id))
        return None

    _log(t("msg.preflight_model_incomplete", model=repo_id, files=", ".join(missing)))
    _log(t("msg.preflight_model_downloading", model=repo_id))

    try:
        _download_with_timeout(repo_id, token, _TIMEOUT_MODEL_DOWNLOAD_SEC)
    except Exception as exc:
        return _handle_model_download_error(repo_id, exc, is_pyannote=False)

    missing = _missing_files(repo_id)
    if missing:
        _log_err(t("msg.preflight_model_incomplete", model=repo_id, files=", ".join(missing)))
        _log(t("msg.preflight_model_manual", repo=repo_id))
        return t("msg.preflight_model_incomplete", model=repo_id, files=", ".join(missing))

    _log(t("msg.preflight_model_download_ok", model=repo_id))
    return None


def check_pyannote_model(config: ConfigParser) -> str | None:
    """
    Проверить целостность модели pyannote диаризации в кеше HF.

    При отсутствии файлов пытается доустановить модель (требуется валидный HF_TOKEN).
    :return: строка ошибки или None
    """
    repo_id = config.get("diarization", "hf_model", fallback="pyannote/speaker-diarization-3.1")
    token = os.environ.get("HF_TOKEN", "")

    _log(t("msg.preflight_model_checking", model=repo_id))

    missing = _pyannote_missing(repo_id)
    if not missing:
        _log(t("msg.preflight_model_ok", model=repo_id))
        return None

    _log(t("msg.preflight_model_incomplete", model=repo_id, files=", ".join(missing)))
    _log(t("msg.preflight_model_downloading", model=repo_id))

    try:
        _download_with_timeout(repo_id, token, _TIMEOUT_MODEL_DOWNLOAD_SEC)
    except Exception as exc:
        return _handle_model_download_error(repo_id, exc, is_pyannote=True)

    missing = _pyannote_missing(repo_id)
    if missing:
        _log_err(t("msg.preflight_model_incomplete", model=repo_id, files=", ".join(missing)))
        _log(t("msg.preflight_model_manual", repo=repo_id))
        return t("msg.preflight_model_incomplete", model=repo_id, files=", ".join(missing))

    _log(t("msg.preflight_model_download_ok", model=repo_id))
    return None


def check_pyannote_segmentation_model(config: ConfigParser) -> str | None:
    """
    Проверить целостность подмодели pyannote/segmentation-3.0 в кеше HF.

    Это gated-весовая подмодель, которую Pipeline.from_pretrained() скачивает
    отдельно при первои запуске диаризации. Проверяется до запуска, чтобы 403
    не возникал в середине пайплайна.
    :return: строка ошибки или None
    """
    repo_id = "pyannote/segmentation-3.0"
    token = os.environ.get("HF_TOKEN", "")

    _log(t("msg.preflight_model_checking", model=repo_id))

    missing = _segmentation_missing(repo_id)
    if not missing:
        _log(t("msg.preflight_model_ok", model=repo_id))
        return None

    _log(t("msg.preflight_model_incomplete", model=repo_id, files=", ".join(missing)))
    _log(t("msg.preflight_model_downloading", model=repo_id))

    try:
        _download_with_timeout(repo_id, token, _TIMEOUT_MODEL_DOWNLOAD_SEC)
    except Exception as exc:
        return _handle_model_download_error(repo_id, exc, is_pyannote=True)

    missing = _segmentation_missing(repo_id)
    if missing:
        _log_err(t("msg.preflight_model_incomplete", model=repo_id, files=", ".join(missing)))
        _log(t("msg.preflight_model_manual", repo=repo_id))
        return t("msg.preflight_model_incomplete", model=repo_id, files=", ".join(missing))

    _log(t("msg.preflight_model_download_ok", model=repo_id))
    return None


def _segmentation_missing(repo_id: str) -> list[str]:
    """Вернуть список отсутствующих ключевых фаилов подмодели segmentation."""
    from huggingface_hub import try_to_load_from_cache

    required = ("config.yaml", "pytorch_model.bin")
    missing: list[str] = []
    for filename in required:
        path = try_to_load_from_cache(repo_id, filename)
        if not path:
            missing.append(filename)
    return missing


def check_pyannote_community_model(config: ConfigParser) -> str | None:
    """
    Проверить целостность подмодели pyannote/speaker-diarization-community-1.

    Это gated-репозитории с весами x-vector/PLDA рескоринга, который
    Pipeline.from_pretrained (pyannote.audio 4.x) скачивает отдельно. Весовая
    модель, проверяется до запуска, чтобы 403 не возникал в середине пайплайна.
    :return: строка ошибки или None
    """
    repo_id = "pyannote/speaker-diarization-community-1"
    token = os.environ.get("HF_TOKEN", "")

    _log(t("msg.preflight_model_checking", model=repo_id))

    missing = _community_missing(repo_id)
    if not missing:
        _log(t("msg.preflight_model_ok", model=repo_id))
        return None

    _log(t("msg.preflight_model_incomplete", model=repo_id, files=", ".join(missing)))
    _log(t("msg.preflight_model_downloading", model=repo_id))

    try:
        _download_with_timeout(repo_id, token, _TIMEOUT_MODEL_DOWNLOAD_SEC)
    except Exception as exc:
        return _handle_model_download_error(repo_id, exc, is_pyannote=True)

    missing = _community_missing(repo_id)
    if missing:
        _log_err(t("msg.preflight_model_incomplete", model=repo_id, files=", ".join(missing)))
        _log(t("msg.preflight_model_manual", repo=repo_id))
        return t("msg.preflight_model_incomplete", model=repo_id, files=", ".join(missing))

    _log(t("msg.preflight_model_download_ok", model=repo_id))
    return None


def _community_missing(repo_id: str) -> list[str]:
    """Вернуть список отсутствующих ключевых фаилов подмодели community-1."""
    from huggingface_hub import try_to_load_from_cache

    required = (
        "config.yaml",
        "embedding/pytorch_model.bin",
        "segmentation/pytorch_model.bin",
        "plda/plda.npz",
        "plda/xvec_transform.npz",
    )
    missing: list[str] = []
    for filename in required:
        path = try_to_load_from_cache(repo_id, filename)
        if not path:
            missing.append(filename)
    return missing


def _pyannote_missing(repo_id: str) -> list[str]:
    """
    Вернуть список отсутствующих ключевых файлов pipeline pyannote.

    pyannote/speaker-diarization-3.1 - это pipeline-репозитории: он содержит
    только config.yaml, веса подмоделей (segmentation-3.0, wespeaker)
    Pipeline.from_pretrained() скачивает отдельно при первом запуске.
    """
    from huggingface_hub import try_to_load_from_cache

    required = ("config.yaml",)
    missing: list[str] = []
    for filename in required:
        path = try_to_load_from_cache(repo_id, filename)
        if not path:
            missing.append(filename)
    return missing


def check_deepseek_api(config: ConfigParser) -> str | None:
    """
    Проверить доступность DeepSeek API (GET /models с авторизацией).

    :return: строка ошибки или None
    """
    import requests

    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    api_url = config.get("deepseek", "api_url", fallback="https://api.deepseek.com/v1")
    timeout = config.getint("deepseek", "timeout", fallback=60)

    _log(t("msg.preflight_deepseek_checking"))

    try:
        response = requests.get(
            api_url + "/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=min(timeout, _TIMEOUT_API_SEC),
        )
    except requests.RequestException as exc:
        return t("error.connection_failed", detail=str(exc))

    if response.status_code == 200:
        _log(t("msg.preflight_deepseek_ok"))
        return None
    return t("error.connection_failed", detail=f"HTTP {response.status_code}")


def check_huggingface_hub(config: ConfigParser) -> str | None:
    """
    Проверить доступность HuggingFace Hub и валидность HF_TOKEN через whoami.

    :return: строка ошибки или None
    """
    from huggingface_hub import HfApi
    from huggingface_hub.utils import HfHubHTTPError

    token = os.environ.get("HF_TOKEN", "")

    _log(t("msg.preflight_hf_checking"))

    api = HfApi()
    try:
        info = _call_with_timeout(lambda: api.whoami(token=token or None), _TIMEOUT_API_SEC)
    except HfHubHTTPError as exc:
        if exc.response is not None and exc.response.status_code in (401, 403):
            return t("msg.preflight_hf_token_invalid")
        return t("error.connection_failed", detail=str(exc))
    except Exception as exc:
        return t("error.connection_failed", detail=str(exc))

    user = ""
    if isinstance(info, dict):
        user = info.get("name", "") or info.get("fullname", "") or ""
    _log(t("msg.preflight_hf_ok", user=user or "anonymous"))
    return None
