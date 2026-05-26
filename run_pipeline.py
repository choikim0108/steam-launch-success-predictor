from pathlib import Path

from steam_success.pipeline import run


if __name__ == "__main__":
    run(Path(__file__).resolve().parent)
