"""
Local LLM wrapper.
- Prefer structured, synchronous call for now.
- Adapt this to your chosen local model runtime (gpt4all/ollama/ggml wrapper).
- Returns string output (assistant reply).
"""

import shlex
import subprocess
import time
from typing import Optional
from ..core.config import settings

DEFAULT_TIMEOUT = 30  # seconds

def call_local_llm(prompt: str, max_tokens: int = 512, timeout: int = DEFAULT_TIMEOUT) -> str:
    """
    Basic CLI wrapper that invokes a model runner command.
    Expected that settings.MODEL_CLI_CMD is an installed CLI that accepts:
      --model "<path_or_name>" --prompt "<text>" --n_predict <int>
    Modify the `cmd` formation per your actual runner.
    """
    cmd_template = settings.MODEL_CLI_CMD or "gpt4all"
    model_path = settings.MODEL_PATH or ""

    # Build safe shell command; note: you MAY need to adjust flags for your runner.
    # Example for gpt4all: gpt4all --model "path" --prompt "..." --n_predict 200
    # Example for ollama: ollama run <model> --prompt "..."
    if "ollama" in cmd_template.lower():
        # ollama run <model> --prompt "<prompt>"
        cmd = f'{shlex.quote(cmd_template)} run {shlex.quote(model_path)} --prompt {shlex.quote(prompt)}'
    else:
        # default take generic CLI form
        cmd = f'{shlex.quote(cmd_template)} --model {shlex.quote(model_path)} --prompt {shlex.quote(prompt)} --n_predict {int(max_tokens)}'

    try:
        start = time.time()
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True, timeout=timeout)
        elapsed = time.time() - start
        return out.strip()
    except subprocess.TimeoutExpired:
        return "[LLM timeout]"
    except Exception as e:
        return f"[LLM error] {str(e)}"