#!/usr/bin/env python3
"""
Validate Hitch profile structure.

Run from the repository root:
    python scripts/validate_profile.py

Exit codes:
    0 — all checks passed
    1 — one or more checks failed (details printed to stderr)
"""
import sys
import os
from pathlib import Path

# Resolve repo root (parent of this script's directory)
REPO_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "README.md",
    "SOUL.md",
    "config.yaml",
    ".env.example",
]

REQUIRED_SKILLS = [
    ("skills/research/automobile-report/SKILL.md", "automobile-report"),
    ("skills/research/automobile-value-rubric/SKILL.md", "automobile-value-rubric"),
    ("skills/research/visor-vin-api/SKILL.md", "visor-vin-api"),
]

REQUIRED_PYTHON_SCRIPTS = [
    "skills/research/automobile-value-rubric/scripts/rubric-score.py",
]


def check_file(path: str) -> bool:
    """Return True if file exists and is non-empty."""
    full = REPO_ROOT / path
    if not full.exists():
        print(f"  ❌ Missing: {path}")
        return False
    if full.stat().st_size == 0:
        print(f"  ⚠️  Empty:   {path}")
        return False
    print(f"  ✓ Found: {path} ({full.stat().st_size} bytes)")
    return True


def check_python_compile(path: str) -> bool:
    """Return True if the Python file compiles without syntax errors."""
    full = REPO_ROOT / path
    import py_compile
    try:
        py_compile.compile(str(full), doraise=True)
        print(f"  ✓ Compiles: {path}")
        return True
    except py_compile.PyCompileError as e:
        print(f"  ❌ Syntax error in {path}: {e}")
        return False


def check_env_example() -> bool:
    """Check .env.example contains required variables."""
    env_path = REPO_ROOT / ".env.example"
    if not env_path.exists():
        print("  ❌ Missing: .env.example")
        return False

    content = env_path.read_text()
    required_vars = ["VISOR_API_KEY", "TARGET_MAKE", "TARGET_MODEL"]
    all_found = True
    for var in required_vars:
        if f"{var}=" not in content:
            print(f"  ❌ Missing variable: {var}")
            all_found = False

    if all_found:
        print("  ✓ .env.example contains all required variables")
    return all_found


def check_gitignore() -> bool:
    """Check .gitignore excludes secrets and archives."""
    gitignore_path = REPO_ROOT / ".gitignore"
    if not gitignore_path.exists():
        print("  ❌ Missing: .gitignore")
        return False

    content = gitignore_path.read_text()
    required_entries = [".env", "archives/", "*.pyc"]
    all_found = True
    for entry in required_entries:
        if entry not in content:
            print(f"  ⚠️  .gitignore missing: {entry}")
            # Not a hard failure, just a warning
            all_found = False

    if all_found:
        print("  ✓ .gitignore excludes secrets and build artifacts")
    return True


def check_no_absolute_paths() -> bool:
    """Scan Python scripts for hardcoded absolute Windows paths."""
    import re
    pattern = re.compile(r'[A-Z]:\\Users', re.IGNORECASE)

    bad_files = []
    scripts_dir = REPO_ROOT / "skills"
    if not scripts_dir.exists():
        print("  ✓ No skills/scripts directory to scan")
        return True

    for py_file in scripts_dir.rglob("*.py"):
        content = py_file.read_text()
        matches = pattern.findall(content)
        # Filter out comments that mention paths only as examples
        lines_with_paths = []
        for line in content.splitlines():
            if pattern.search(line) and not line.strip().startswith("# >>> PERSONALIZE"):
                lines_with_paths.append(line.strip())

        if lines_with_paths:
            bad_files.append((py_file, lines_with_paths))

    if bad_files:
        for py_file, lines in bad_files:
            print(f"  ⚠️  Hardcoded path(s) in {py_file.relative_to(REPO_ROOT)}:")
            for line in lines[:3]:
                print(f"      → {line}")
        # Not a hard failure — just warn
        return True

    print("  ✓ No hardcoded absolute paths found in Python scripts")
    return True


def main():
    print("=" * 60)
    print("Hitch Profile Validation")
    print(f"Repo root: {REPO_ROOT}")
    print("=" * 60)

    all_passed = True

    # Check required files
    print("\n[1/5] Required files:")
    for f in REQUIRED_FILES:
        if not check_file(f):
            all_passed = False

    # Check skill directories and SKILL.md files
    print("\n[2/5] Skills:")
    for path, name in REQUIRED_SKILLS:
        full = REPO_ROOT / path
        if not full.exists():
            print(f"  ❌ Missing skill: {name} ({path})")
            all_passed = False
        else:
            size = full.stat().st_size
            print(f"  ✓ Found skill: {name} (SKILL.md, {size} bytes)")

    # Check Python scripts compile
    print("\n[3/5] Python compilation:")
    for script in REQUIRED_PYTHON_SCRIPTS:
        if not check_python_compile(script):
            all_passed = False

    # Check .env.example
    print("\n[4/5] Environment configuration:")
    if not check_env_example():
        all_passed = False

    # Check .gitignore and hardcoded paths
    print("\n[5/5] Repository hygiene:")
    if not check_gitignore():
        pass  # warnings only
    check_no_absolute_paths()

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All checks passed!")
        return 0
    else:
        print("❌ Some checks failed. See output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())