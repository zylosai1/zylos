"""
Trainer: collects approved training items and triggers fine-tuning (LoRA) jobs.
This is an orchestration stub. Replace training_command with your preferred training pipeline.
"""

import time
import threading
from ..database.crud import list_approved_training_sql
from ..database.base import get_session
from ..core.config import settings

def collect_training_examples(session):
    # load approved items
    items = list_approved_training_sql(session)
    dataset = []
    for it in items:
        dataset.append({"prompt": it.prompt, "response": it.response})
    return dataset

def run_training_job(dataset):
    # Placeholder: write dataset to file and call LoRA trainer (or other)
    # Example: python train_lora_script.py --data data.json --output adapters/
    print("[trainer] Starting training job (stub). Dataset size:", len(dataset))
    time.sleep(2)
    print("[trainer] Training job complete (stub).")

def schedule_training():
    # Basic single-run synchronous call suitable for scripts/train_lora.py
    print("[trainer] schedule_training invoked")
    # Acquire a DB session and collect dataset
    from sqlmodel import Session
    from ..database.base import engine
    with Session(engine) as session:
        data = collect_training_examples(session)
    if data:
        run_training_job(data)
    else:
        print("[trainer] No approved training items found.")