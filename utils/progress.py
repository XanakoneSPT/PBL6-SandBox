from django.conf import settings
from pathlib import Path
from typing import Dict, Any, Optional

import json
import logging

logger = logging.getLogger(__name__)

def _get_progress_file(uploaded_file_id: int) -> Path:
    progress_dir = settings.SHARED_FOLDERS['TO_VM'] / 'progress'
    progress_dir.mkdir(parents=True, exist_ok=True)

    return progress_dir / f"{uploaded_file_id}.json"

def get_progress(uploaded_file_id: int) -> Dict[str, Any]:
    file_path = _get_progress_file(uploaded_file_id)
    
    if file_path.exists():
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            return {
                "progress": data.get("progress", 0),
                "status": data.get("status", "pending")
            }
        except Exception:
            pass
    
    return {
        "progress": 0,
        "status": "pending"
    }

def _update_progress(uploaded_file_id: int, progress: int, status: Optional[str] = None) -> None:
    data = get_progress(uploaded_file_id)

    #update
    data["progress"] = max(0, min(100, int(progress)))
    if status:
        data["status"] = status

    #save
    file_path = _get_progress_file(uploaded_file_id)
    try:
        file_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as e:
        logger.error(f"Failed to save progress: {e}")

def set_progress_fields(uploaded_file_id: int, **fields: Any) -> None:
    data = get_progress(uploaded_file_id)

    data.update(fields)

    file_path = _get_progress_file(uploaded_file_id)
    try:
        file_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as e:
        logger.error(f"Failed to save progress fields: {e}")