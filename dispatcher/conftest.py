# dispatcher/conftest.py
# ──────────────────────
# pytest'in src/ paketini import edebilmesi icin
# proje koku dispatcher/ dizinine eklendi.
#
# Bu dosyanin varligi pytest'e "bu dizin proje kokunun"
# sinyalini verir; sys.path'e src/ eklenmesine gerek kalmaz.

import sys
import pathlib

# dispatcher/src klasorunu Python arama yoluna ekle
sys.path.insert(0, str(pathlib.Path(__file__).parent))
