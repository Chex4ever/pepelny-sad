"""Bootstrap art files from catalog if missing."""
import os

from src import constants


def ensure_art_files():
    from src.data.art._catalog import ART

    base = constants.DATA_DIR or os.path.join(os.path.dirname(os.path.abspath(__file__)))
    for rel, content in ART.items():
        path = os.path.join(base, "art", rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.isfile(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
