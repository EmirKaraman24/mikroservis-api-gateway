#!/usr/bin/env python3
# scripts/verify_tests.py
# ─────────────────────────────────────────────────────────────
# Commit 39 (Emir) — 5 Nisan 2026
# test: run all unit and integration tests, fix remaining failures
#
# Bu script projedeki tüm test paketlerini sırayla çalıştırır
# ve özet bir rapor basar.
#
# Kullanım:
#   python scripts/verify_tests.py
#
# Gereksinim: pytest, pytest projesinin kökünde çalışıyor olması

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

TEST_SUITES = [
    {
        "name": "Dispatcher — Birim Testleri",
        "cwd": ROOT / "dispatcher",
        "cmd": [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-q"],
    },
    {
        "name": "Auth Service — Birim Testleri",
        "cwd": ROOT / "auth-service",
        "cmd": [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-q"],
    },
    {
        "name": "Message Service — Temel Testler",
        "cwd": ROOT / "message-service",
        "cmd": [sys.executable, "-m", "pytest", "test_message.py", "-v", "--tb=short", "-q"],
    },
    {
        "name": "Message Service — Edge Case Testleri",
        "cwd": ROOT / "message-service",
        "cmd": [sys.executable, "-m", "pytest", "test_message_edge_cases.py", "-v", "--tb=short", "-q"],
    },
    {
        "name": "E2E — Tam İstek Döngüsü",
        "cwd": ROOT / "dispatcher",
        "cmd": [sys.executable, "-m", "pytest", "../tests/e2e/", "-v", "--tb=short", "-q"],
    },
]

PASS = "✅"
FAIL = "❌"
SEP = "─" * 60


def run_suite(suite: dict) -> bool:
    print(f"\n{SEP}")
    print(f"  {suite['name']}")
    print(SEP)

    result = subprocess.run(
        suite["cmd"],
        cwd=suite["cwd"],
        capture_output=False,
    )
    return result.returncode == 0


def main():
    print("=" * 60)
    print("  Dispatcher Projesi — Tam Test Doğrulama")
    print("  5 Nisan 2026")
    print("=" * 60)

    results = []
    for suite in TEST_SUITES:
        passed = run_suite(suite)
        results.append((suite["name"], passed))

    print(f"\n{'=' * 60}")
    print("  ÖZET")
    print("=" * 60)
    all_passed = True
    for name, passed in results:
        icon = PASS if passed else FAIL
        print(f"  {icon}  {name}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("  ✅  Tüm testler geçti! Proje teslime hazır.")
    else:
        print("  ❌  Bazı testler başarısız — yukarıdaki çıktıyı kontrol edin.")
    print("=" * 60)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
