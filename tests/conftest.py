import sys
from pathlib import Path

# los módulos de src/ se importan entre sí por su nombre (from limpieza import ...)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
