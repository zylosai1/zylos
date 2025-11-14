# scripts/train_lora.py
"""
Schedule / run training tasks (LoRA or fine-tuning).
This is a safe wrapper that runs the trainer schedule.
"""
import logging
from app.ai.trainer import schedule_training

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("train_lora")

def main():
    logger.info("Invoking training scheduler...")
    schedule_training()
    logger.info("Training scheduler complete.")

if __name__ == "__main__":
    main()