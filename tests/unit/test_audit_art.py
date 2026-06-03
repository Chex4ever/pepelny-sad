"""Tests for art audit tool."""
import os
import subprocess
import sys


def test_audit_art_script_passes():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    result = subprocess.run(
        [sys.executable, os.path.join(root, "tools", "audit_art.py")],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Art audit OK" in result.stdout
