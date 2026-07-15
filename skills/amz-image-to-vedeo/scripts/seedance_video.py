#!/usr/bin/env python3
"""CLI wrapper for a Seedance-compatible video generation API."""

from __future__ import annotations

import argparse
import base64
from datetime import datetime
import json
import mimetypes
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any
from urllib import error, parse, request


DEFAULT_BASE_URL = os.environ.get("VIDEO_API_BASE_URL", "")
SKILL_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATHS = [
    Path.cwd() / ".env",
    Path.home() / ".config" / "amz-image-to-vedeo" / "env",
    Path.home() / ".config" / "amz-image-to-vedeo" / ".env",
    Path.home() / ".config" / "cross-border-product-video" / "env",
    Path.home() / ".config" / "cross-border-product-video" / ".env",
    Path.home() / ".config" / "seedance-video" / "env",
    Path.home() / ".config" / "seedance-video" / ".env",
    SKILL_DIR / ".env",
]

VALID_MODELS = {"seedance-2", "seedance-2-fast"}
VALID_ASPECT_RATIOS = {"21:9", "16:9", "4:3", "1:1", "3:4", "9:16"}
VALID_RESOLUTIONS = {"720p", "1080p"}
TERMINAL_STATUSES = {"completed", "failed"}
PRICE_PER_CREDIT_CNY = 0.035
KNOWN_CREDIT_RATES_PER_SECOND = {
    ("seedance-2", "720p"): 28.57,
    ("seedance-2", "1080p"): 71.43,
}


class SeedanceError(RuntimeError):
    """User-facing CLI error."""


def load_env_files(paths: list[Path] = CONFIG_PATHS) -> None:
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"'")
            if key and key not in os.environ:
                os.environ[key] = value


def get_api_key(args: argparse.Namespace) -> str:
    load_env_files()
    args.base_url = args.base_url or os.environ.get("VIDEO_API_BASE_URL", "")
    if not args.base_url:
        raise SeedanceError("Missing VIDEO_API_BASE_URL for a compatible video API.")
    api_key = args.api_key or os.environ.get("VIDEO_API_KEY")
    if not api_key:
        raise SeedanceError(
            "Missing VIDEO_API_KEY. Set it in the environment, "
            "~/.config/amz-image-to-vedeo/env, "
            "~/.config/cross-border-product-video/env, or "
            "~/.config/seedance-video/env."
        )
    return api_key


def parse_json_value(raw: str | None, label: str) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SeedanceError(f"{label} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SeedanceError(f"{label} must be a JSON object.")
    return data


def read_json_file(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise SeedanceError(f"Could not read body file: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SeedanceError(f"Body file is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SeedanceError("Body file must contain a JSON object.")
    return data


def default_output_dir() -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return str(Path.home() / "Desktop" / "amz-image-to-vedeo-output" / stamp)


def write_json_artifact(output_dir: str, filename: str, data: dict[str, Any]) -> str:
    out_dir = Path(output_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / filename
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return str(target)


def estimate_cost(
    model: str | None,
    resolution: str | None,
    duration: int | None,
) -> dict[str, Any]:
    if duration is None or duration <= 0:
        return {
            "available": False,
            "reason": "duration must be a positive fixed number of seconds",
            "model": model,
            "resolution": resolution,
            "duration_seconds": duration,
            "price_per_credit_cny": PRICE_PER_CREDIT_CNY,
        }

    credits_per_second = KNOWN_CREDIT_RATES_PER_SECOND.get((model or "", resolution or ""))
    if credits_per_second is None:
        return {
            "available": False,
            "reason": "no configured price rate for this model/resolution",
            "model": model,
            "resolution": resolution,
            "duration_seconds": duration,
            "price_per_credit_cny": PRICE_PER_CREDIT_CNY,
        }

    estimated_credits = credits_per_second * duration
    return {
        "available": True,
        "model": model,
        "resolution": resolution,
        "duration_seconds": duration,
        "credits_per_second": credits_per_second,
        "estimated_credits": round(estimated_credits, 2),
        "price_per_credit_cny": PRICE_PER_CREDIT_CNY,
        "estimated_cny": round(estimated_credits * PRICE_PER_CREDIT_CNY, 2),
        "pricing_note": "Configured from the user-provided Seedance price table.",
    }


def estimate_cost_from_body(body: dict[str, Any]) -> dict[str, Any]:
    duration = body.get("duration")
    if not isinstance(duration, int):
        duration = None
    return estimate_cost(
        str(body.get("model") or ""),
        str(body.get("resolution") or ""),
        duration,
    )


def is_remote_or_asset(value: str) -> bool:
    return value.startswith(("http://", "https://", "asset://"))


def local_file_to_data_uri(value: str, expected_prefix: str) -> str:
    path = Path(value).expanduser()
    if not path.exists():
        raise SeedanceError(f"Local file does not exist: {value}")
    mime_type, _ = mimetypes.guess_type(str(path))
    if not mime_type or not mime_type.startswith(expected_prefix + "/"):
        raise SeedanceError(
            f"Expected a {expected_prefix} file, got MIME type "
            f"{mime_type or 'unknown'} for {value}."
        )
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def upload_image_file(value: str, api_key: str, base_url: str, timeout: float) -> str:
    path = Path(value).expanduser()
    if not path.exists():
        raise SeedanceError(f"Local image does not exist: {value}")
    mime_type, _ = mimetypes.guess_type(str(path))
    if not mime_type or not mime_type.startswith("image/"):
        raise SeedanceError(
            f"Expected an image file, got MIME type "
            f"{mime_type or 'unknown'} for {value}."
        )

    boundary = f"----seedance-video-cli-{int(time.time() * 1000)}"
    filename = path.name
    file_bytes = path.read_bytes()
    head = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {mime_type}\r\n\r\n"
    ).encode("utf-8")
    tail = f"\r\n--{boundary}--\r\n".encode("utf-8")
    body = head + file_bytes + tail
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "User-Agent": "seedance-video-cli/0.1",
    }
    upload_url = f"{base_url.rstrip()}/v1/uploads/images"
    req = request.Request(upload_url, data=body, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw_body)
        except json.JSONDecodeError:
            parsed = {"message": raw_body}
        raise SeedanceError(
            f"HTTP {exc.code} uploading image: {json.dumps(parsed, ensure_ascii=False)}"
        ) from exc
    except error.URLError as exc:
        raise SeedanceError(f"Network error uploading image: {exc}") from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SeedanceError(f"Upload returned non-JSON response: {raw[:500]}") from exc
    data = parsed.get("data") if isinstance(parsed, dict) else None
    image_url = data.get("url") if isinstance(data, dict) else None
    if not image_url:
        raise SeedanceError(
            f"Upload response did not include data.url: {json.dumps(parsed, ensure_ascii=False)}"
        )
    return image_url


def normalize_image(value: str, api_key: str, base_url: str, timeout: float) -> str:
    if is_remote_or_asset(value):
        return value
    if value.startswith("data:"):
        raise SeedanceError(
            "Base64 image data is no longer accepted by configured video API. "
            "Use a public image URL or a local image file so the CLI can upload it first."
        )
    return upload_image_file(value, api_key, base_url, timeout)


def normalize_audio(value: str) -> str:
    if is_remote_or_asset(value):
        return value
    return local_file_to_data_uri(value, "audio")


def normalize_video(value: str) -> str:
    if value.startswith(("http://", "https://", "asset://")):
        return value
    raise SeedanceError("Reference videos must be a public URL or asset:// URI.")


def http_json(
    method: str,
    url: str,
    api_key: str,
    body: dict[str, Any] | None = None,
    timeout: float = 60.0,
) -> dict[str, Any]:
    data = None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "seedance-video-cli/0.1",
    }
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw_body)
        except json.JSONDecodeError:
            parsed = {"message": raw_body}
        raise SeedanceError(
            f"HTTP {exc.code} from configured video API: {json.dumps(parsed, ensure_ascii=False)}"
        ) from exc
    except error.URLError as exc:
        raise SeedanceError(f"Network error calling configured video API: {exc}") from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SeedanceError(f"configured video API returned non-JSON response: {raw[:500]}") from exc
    if not isinstance(parsed, dict):
        raise SeedanceError("configured video API returned JSON, but not an object.")
    return parsed


def build_video_body(args: argparse.Namespace, api_key: str | None = None) -> dict[str, Any]:
    body = {}
    body.update(read_json_file(args.body_file))
    body.update(parse_json_value(args.body_json, "--body-json"))

    if args.model:
        body["model"] = args.model
    elif "model" not in body:
        body["model"] = "seedance-2"

    if args.prompt is not None:
        body["prompt"] = args.prompt
    if args.duration is not None:
        body["duration"] = args.duration
    if args.aspect_ratio is not None:
        body["aspect_ratio"] = args.aspect_ratio
    if args.resolution is not None:
        body["resolution"] = args.resolution
    if args.generate_audio is not None:
        body["generate_audio"] = args.generate_audio
    if "generate_audio" not in body:
        body["generate_audio"] = False
    if args.seed is not None:
        body["seed"] = args.seed
    if args.callback_url is not None:
        body["callback_url"] = args.callback_url
    if args.trace_id is not None:
        body["trace_id"] = args.trace_id
    if args.client_business_id is not None:
        body["client_business_id"] = args.client_business_id

    image_with_roles = list(body.get("image_with_roles") or [])
    if args.first_frame:
        if not api_key:
            raise SeedanceError("Local first-frame images require VIDEO_API_KEY for upload.")
        image_with_roles.append(
            {
                "url": normalize_image(
                    args.first_frame, api_key, args.base_url, args.timeout
                ),
                "role": "first_frame",
            }
        )
    if args.last_frame:
        if not api_key:
            raise SeedanceError("Local last-frame images require VIDEO_API_KEY for upload.")
        image_with_roles.append(
            {
                "url": normalize_image(
                    args.last_frame, api_key, args.base_url, args.timeout
                ),
                "role": "last_frame",
            }
        )
    for value in args.reference_image or []:
        if not api_key:
            raise SeedanceError("Local reference images require VIDEO_API_KEY for upload.")
        image_with_roles.append(
            {
                "url": normalize_image(value, api_key, args.base_url, args.timeout),
                "role": "reference_image",
            }
        )
    if image_with_roles:
        body["image_with_roles"] = image_with_roles

    video_with_roles = list(body.get("video_with_roles") or [])
    for value in args.reference_video or []:
        video_with_roles.append(
            {"url": normalize_video(value), "role": "reference_video"}
        )
    if video_with_roles:
        body["video_with_roles"] = video_with_roles

    audio_with_roles = list(body.get("audio_with_roles") or [])
    for value in args.reference_audio or []:
        audio_with_roles.append(
            {"url": normalize_audio(value), "role": "reference_audio"}
        )
    if audio_with_roles:
        body["audio_with_roles"] = audio_with_roles

    metadata = parse_json_value(args.metadata_json, "--metadata-json")
    if metadata:
        existing = body.get("metadata")
        if existing is not None and not isinstance(existing, dict):
            raise SeedanceError("metadata must be a JSON object.")
        merged = dict(existing or {})
        merged.update(metadata)
        body["metadata"] = merged

    extra = parse_json_value(args.extra_json, "--extra-json")
    body.update(extra)

    validate_body(body)
    return body


def count_roles(items: list[dict[str, Any]], role: str) -> int:
    return sum(1 for item in items if item.get("role") == role)


def validate_body(body: dict[str, Any]) -> None:
    model = body.get("model")
    if model not in VALID_MODELS:
        raise SeedanceError(f"model must be one of: {', '.join(sorted(VALID_MODELS))}")

    duration = body.get("duration")
    if duration is not None:
        if not isinstance(duration, int):
            raise SeedanceError("duration must be an integer.")
        if duration not in (0, -1):
            max_duration = 12 if model == "seedance-2-fast" else 15
            if duration < 4 or duration > max_duration:
                raise SeedanceError(
                    f"{model} duration must be 4-{max_duration}, 0, or -1."
                )

    aspect_ratio = body.get("aspect_ratio")
    if aspect_ratio is not None and aspect_ratio not in VALID_ASPECT_RATIOS:
        raise SeedanceError(
            f"aspect_ratio must be one of: {', '.join(sorted(VALID_ASPECT_RATIOS))}"
        )

    resolution = body.get("resolution")
    if resolution is not None and resolution not in VALID_RESOLUTIONS:
        raise SeedanceError(
            f"resolution must be one of: {', '.join(sorted(VALID_RESOLUTIONS))}"
        )
    if model == "seedance-2-fast" and resolution == "1080p":
        raise SeedanceError("seedance-2-fast only supports 720p.")

    image_roles = body.get("image_with_roles") or []
    video_roles = body.get("video_with_roles") or []
    audio_roles = body.get("audio_with_roles") or []
    for label, items in (
        ("image_with_roles", image_roles),
        ("video_with_roles", video_roles),
        ("audio_with_roles", audio_roles),
    ):
        if not isinstance(items, list):
            raise SeedanceError(f"{label} must be an array.")
        for item in items:
            if not isinstance(item, dict) or not item.get("url") or not item.get("role"):
                raise SeedanceError(f"{label} entries must include url and role.")

    if count_roles(image_roles, "first_frame") > 1:
        raise SeedanceError("image_with_roles can include only one first_frame.")
    if count_roles(image_roles, "last_frame") > 1:
        raise SeedanceError("image_with_roles can include only one last_frame.")
    if count_roles(image_roles, "last_frame") and not count_roles(
        image_roles, "first_frame"
    ):
        raise SeedanceError("last_frame requires first_frame.")
    if count_roles(image_roles, "reference_image") > 9:
        raise SeedanceError("reference_image supports at most 9 images.")
    if count_roles(video_roles, "reference_video") > 3:
        raise SeedanceError("reference_video supports at most 3 videos.")
    if count_roles(audio_roles, "reference_audio") > 3:
        raise SeedanceError("reference_audio supports at most 3 audio files.")
    if count_roles(image_roles, "reference_image") and (
        count_roles(image_roles, "first_frame") or count_roles(image_roles, "last_frame")
    ):
        raise SeedanceError(
            "Do not mix reference_image with first_frame or last_frame."
        )
    if audio_roles and not (image_roles or video_roles):
        raise SeedanceError(
            "audio_with_roles cannot be used alone; add an image or video reference."
        )


def submit_task(args: argparse.Namespace) -> dict[str, Any]:
    api_key = get_api_key(args)
    body = build_video_body(args, api_key)
    base_url = args.base_url.rstrip("/")
    url = f"{base_url}/v1/videos/generations"
    artifact_paths: dict[str, str] = {}
    cost_estimate = estimate_cost_from_body(body)

    if args.save_artifacts:
        artifact_paths["seedance_request"] = write_json_artifact(
            args.output_dir,
            "seedance_request.json",
            {"url": url, "body": body, "cost_estimate": cost_estimate},
        )

    if args.dry_run:
        result = {"dry_run": True, "url": url, "body": body, "cost_estimate": cost_estimate}
        if artifact_paths:
            result["artifacts"] = artifact_paths
        return result

    data = http_json("POST", url, api_key, body=body, timeout=args.timeout)
    if args.wait:
        task_id = data.get("id")
        if not task_id:
            raise SeedanceError("Submit response did not include a task id.")
        final = wait_for_task(args, task_id)
        data = {"submitted": data, "result": final}
    if args.save_artifacts:
        artifact_paths["result"] = write_json_artifact(
            args.output_dir, "result.json", data
        )
        artifact_paths["run_manifest"] = write_run_manifest(
            args.output_dir, url, body, data, cost_estimate, artifact_paths
        )
        data["artifacts"] = artifact_paths
    data["cost_estimate"] = cost_estimate
    return data


def status_task(
    args: argparse.Namespace,
    task_id: str | None = None,
    allow_download: bool = True,
) -> dict[str, Any]:
    api_key = get_api_key(args)
    resolved_id = task_id or args.task_id
    base_url = args.base_url.rstrip("/")
    encoded_task_id = parse.quote(resolved_id, safe="")
    url = f"{base_url}/v1/videos/generations/{encoded_task_id}"
    data = http_json("GET", url, api_key, timeout=args.timeout)
    if (
        allow_download
        and args.download
        and data.get("status") == "completed"
        and get_video_url(data)
    ):
        data["saved_path"] = download_url(
            get_video_url(data), args.output_dir, args.filename, args.timeout, api_key
        )
    return data


def wait_for_task(args: argparse.Namespace, task_id: str | None = None) -> dict[str, Any]:
    resolved_id = task_id or args.task_id
    start = time.monotonic()
    if args.initial_wait > 0:
        time.sleep(args.initial_wait)
    while True:
        data = status_task(args, resolved_id, allow_download=False)
        status = data.get("status")
        progress = data.get("progress", 0)
        print(f"status={status} progress={progress}%", file=sys.stderr)
        if status == "completed":
            video_url = get_video_url(data)
            if args.download and video_url:
                data["saved_path"] = download_url(
                    video_url,
                    args.output_dir,
                    args.filename,
                    args.timeout,
                    get_api_key(args),
                )
            if getattr(args, "save_artifacts", False):
                data["result_artifact"] = write_json_artifact(
                    args.output_dir, "result.json", data
                )
            return data
        if status == "failed":
            if getattr(args, "save_artifacts", False):
                data["result_artifact"] = write_json_artifact(
                    args.output_dir, "result.json", data
                )
            return data
        if time.monotonic() - start >= args.max_wait:
            raise SeedanceError(f"Task timed out after {args.max_wait} seconds.")
        time.sleep(args.interval)


def get_video_url(data: dict[str, Any]) -> str | None:
    metadata = data.get("metadata")
    if isinstance(metadata, dict) and metadata.get("url"):
        return str(metadata["url"])
    if data.get("video_url"):
        return str(data["video_url"])
    return None


def final_task_data(data: dict[str, Any]) -> dict[str, Any]:
    result = data.get("result")
    if isinstance(result, dict):
        return result
    return data


def ffprobe_media(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    media_path = Path(path).expanduser()
    if not media_path.exists():
        return {"available": False, "reason": f"file does not exist: {path}"}

    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "stream=index,codec_type,codec_name,width,height,duration:format=duration",
        "-of",
        "json",
        str(media_path),
    ]
    try:
        completed = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        return {"available": False, "reason": "ffprobe is not installed"}
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "reason": str(exc)}

    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"available": False, "reason": "ffprobe returned invalid JSON"}
    parsed["available"] = True
    return parsed


def write_run_manifest(
    output_dir: str,
    request_url: str,
    body: dict[str, Any],
    data: dict[str, Any],
    cost_estimate: dict[str, Any],
    artifact_paths: dict[str, str],
) -> str:
    task = final_task_data(data)
    saved_path = task.get("saved_path") if isinstance(task, dict) else None
    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "request": {
            "url": request_url,
            "body": body,
        },
        "cost_estimate": cost_estimate,
        "task": {
            "id": task.get("id") or task.get("task_id"),
            "status": task.get("status"),
            "progress": task.get("progress"),
            "video_url": get_video_url(task),
            "saved_path": saved_path,
        },
        "artifacts": dict(artifact_paths),
        "media_probe": ffprobe_media(saved_path),
    }
    return write_json_artifact(output_dir, "run_manifest.json", manifest)


def download_url(
    url: str,
    output_dir: str,
    filename: str | None = None,
    timeout: float = 120.0,
    api_key: str | None = None,
) -> str:
    out_dir = Path(output_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    headers = {
        "Accept": "*/*",
        "User-Agent": "seedance-video-cli/0.1",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = request.Request(url, headers=headers, method="GET")
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            content = resp.read()
            content_type = resp.headers.get_content_type()
    except error.URLError as exc:
        raise SeedanceError(f"Could not download video: {exc}") from exc

    if filename:
        name = filename
    else:
        path_name = Path(parse.urlparse(url).path).name
        suffix = Path(path_name).suffix
        if not suffix:
            suffix = mimetypes.guess_extension(content_type) or ".mp4"
        name = f"seedance-{int(time.time())}{suffix}"
    target = out_dir / name
    target.write_bytes(content)
    return str(target)


def download_command(args: argparse.Namespace) -> dict[str, Any]:
    load_env_files()
    api_key = args.api_key or os.environ.get("VIDEO_API_KEY")
    saved_path = download_url(
        args.url, args.output_dir, args.filename, args.timeout, api_key
    )
    return {"saved_path": saved_path}


def config_check(args: argparse.Namespace) -> dict[str, Any]:
    load_env_files()
    key = args.api_key or os.environ.get("VIDEO_API_KEY")
    base_url = args.base_url or os.environ.get("VIDEO_API_BASE_URL", "")
    found_files = [str(path) for path in CONFIG_PATHS if path.exists()]
    return {
        "has_api_key": bool(key),
        "loaded_env_files": found_files,
        "base_url": base_url,
    }


def estimate_cost_command(args: argparse.Namespace) -> dict[str, Any]:
    return estimate_cost(args.model, args.resolution, args.duration)


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--api-key", help=argparse.SUPPRESS)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=float, default=60.0)


def add_wait_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--initial-wait", type=float, default=5.0)
    parser.add_argument("--interval", type=float, default=10.0)
    parser.add_argument("--max-wait", type=float, default=600.0)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--output-dir", default=default_output_dir())
    parser.add_argument("--filename")
    parser.add_argument("--save-artifacts", dest="save_artifacts", action="store_true")
    parser.add_argument("--no-save-artifacts", dest="save_artifacts", action="store_false")
    parser.set_defaults(save_artifacts=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Submit, poll, and download configured video API Seedance video tasks."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    submit = subparsers.add_parser(
        "submit", aliases=["generate"], help="Submit a Seedance video task."
    )
    add_common_args(submit)
    submit.add_argument("--prompt")
    submit.add_argument("--model", choices=sorted(VALID_MODELS), default="seedance-2")
    submit.add_argument("--duration", type=int)
    submit.add_argument("--aspect-ratio", choices=sorted(VALID_ASPECT_RATIOS))
    submit.add_argument("--resolution", choices=sorted(VALID_RESOLUTIONS))
    submit.add_argument("--generate-audio", dest="generate_audio", action="store_true")
    submit.add_argument("--no-audio", dest="generate_audio", action="store_false")
    submit.set_defaults(generate_audio=None)
    submit.add_argument("--seed", type=int)
    submit.add_argument("--callback-url")
    submit.add_argument("--trace-id")
    submit.add_argument("--client-business-id")
    submit.add_argument("--first-frame")
    submit.add_argument("--last-frame")
    submit.add_argument("--reference-image", action="append")
    submit.add_argument("--reference-video", action="append")
    submit.add_argument("--reference-audio", action="append")
    submit.add_argument("--body-json")
    submit.add_argument("--body-file")
    submit.add_argument("--metadata-json")
    submit.add_argument("--extra-json")
    submit.add_argument("--dry-run", action="store_true")
    submit.add_argument("--wait", action="store_true")
    add_wait_args(submit)
    submit.set_defaults(func=submit_task)

    status = subparsers.add_parser("status", help="Get task status.")
    add_common_args(status)
    status.add_argument("task_id")
    status.add_argument("--download", action="store_true")
    status.add_argument("--output-dir", default=default_output_dir())
    status.add_argument("--filename")
    status.set_defaults(func=status_task)

    wait = subparsers.add_parser("wait", help="Poll until task completion or failure.")
    add_common_args(wait)
    wait.add_argument("task_id")
    add_wait_args(wait)
    wait.set_defaults(func=wait_for_task)

    download = subparsers.add_parser("download", help="Download a completed video URL.")
    download.add_argument("--api-key", help=argparse.SUPPRESS)
    download.add_argument("url")
    download.add_argument("--output-dir", default=default_output_dir())
    download.add_argument("--filename")
    download.add_argument("--timeout", type=float, default=120.0)
    download.set_defaults(func=download_command)

    estimate = subparsers.add_parser("estimate-cost", help="Estimate Seedance cost.")
    estimate.add_argument("--model", choices=sorted(VALID_MODELS), default="seedance-2")
    estimate.add_argument("--duration", type=int, required=True)
    estimate.add_argument("--resolution", choices=sorted(VALID_RESOLUTIONS), required=True)
    estimate.set_defaults(func=estimate_cost_command)

    check = subparsers.add_parser("config-check", help="Check local configuration.")
    add_common_args(check)
    check.set_defaults(func=config_check)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = args.func(args)
    except SeedanceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
