from __future__ import annotations

import os
import time
from pathlib import Path

from thesis_generator.security import mask_pii, prune_uploads


def test_mask_pii_redacts_emails_and_numbers() -> None:
    text = "Contact alice@example.com or +1-202-555-0188 to share feedback."

    masked = mask_pii(text)

    assert "alice@example.com" not in masked
    assert "555-0188" not in masked
    assert "[REDACTED]" in masked


def test_prune_uploads_removes_files_older_than_ttl(tmp_path: Path) -> None:
    old_file = tmp_path / "old.pdf"
    recent_file = tmp_path / "recent.pdf"
    old_file.write_text("old")
    recent_file.write_text("recent")

    thirty_one_days_ago = time.time() - 31 * 24 * 60 * 60
    os.utime(old_file, (thirty_one_days_ago, thirty_one_days_ago))

    removed = prune_uploads(tmp_path, ttl_days=30)

    assert old_file not in tmp_path.iterdir()
    assert recent_file.exists()
    assert old_file in removed
