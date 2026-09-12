import os
from dotenv import load_dotenv

load_dotenv()

MIRO_API_KEY = os.environ.get("MIRO_API_KEY", "")
MIRO_BOARD_ID = os.environ.get("MIRO_BOARD_ID", "")

if not MIRO_API_KEY:
    raise RuntimeError("MIRO_API_KEY is missing or empty. Please check your .env file.")

if not MIRO_BOARD_ID:
    raise RuntimeError("MIRO_BOARD_ID is missing or empty. Please check your .env file.")
