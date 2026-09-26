"""Runtime settings. Credentials stay out of run metadata."""
import os
import json
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
TAU_COMMIT = "b7ea9074c1cba482b30687fecdb5c8425fd6f619"
LLM_BASE_URL = "https://api.commandcode.ai/provider/v1"
load_dotenv(ROOT / ".env")
os.environ.setdefault("TAU2_DATA_DIR", str(ROOT / ".deps/tau2-bench/data"))
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")


@dataclass(frozen=True)
class Settings:
    task_id: str
    llm_model: str
    stt_model: str
    tts_model: str
    prompt_path: Path
    llm_api_key: str = field(repr=False)

    @classmethod
    def load(cls):
        api_key = os.getenv("COMMAND_CODE_API_KEY", "").strip()
        if not api_key:
            auth_path = Path.home() / ".commandcode/auth.json"
            if auth_path.exists():
                api_key = json.loads(auth_path.read_text()).get("apiKey", "").strip()
        missing = [key for key in ("DEEPGRAM_API_KEY",)
                   if not os.getenv(key, "").strip()]
        if not api_key:
            missing.append("COMMAND_CODE_API_KEY (or Command Code CLI login)")
        if missing:
            raise ValueError("Missing credentials in .env: " + ", ".join(missing))
        return cls(
            task_id=os.getenv("TASK_ID", "0"),
            llm_model=os.getenv("LLM_MODEL", "deepseek/deepseek-v4.1-flash"),
            stt_model=os.getenv("STT_MODEL", "nova-3"),
            tts_model=os.getenv("TTS_MODEL", "aura-2-andromeda-en"),
            prompt_path=ROOT / os.getenv("PROMPT_FILE", "prompts/baseline.md"),
            llm_api_key=api_key,
        )
