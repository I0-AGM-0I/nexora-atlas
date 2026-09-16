"""
NEXORA ATLAS - Alembic Migration Lifecycle Tests
Verifies that database migrations apply, downgrade, and re-apply cleanly.
"""

import os
import pytest
from alembic.config import Config
from alembic import command


def test_alembic_migration_lifecycle(tmp_path):
    """Verify fresh db creation -> upgrade head -> downgrade base -> re-upgrade head."""
    db_file = tmp_path / "migration_test.db"
    test_db_url = f"sqlite:///{db_file.as_posix()}"

    # Configure Alembic
    ini_path = os.path.join(os.path.dirname(__file__), "..", "alembic.ini")
    alembic_cfg = Config(ini_path)
    alembic_cfg.set_main_option("sqlalchemy.url", test_db_url)
    alembic_cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "..", "alembic"))

    # 1. Upgrade to head
    command.upgrade(alembic_cfg, "head")
    assert db_file.exists()

    # 2. Downgrade to base
    command.downgrade(alembic_cfg, "base")

    # 3. Upgrade to head again
    command.upgrade(alembic_cfg, "head")
