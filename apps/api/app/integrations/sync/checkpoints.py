"""
NEXORA ATLAS - Synchronization Window & Checkpoints
Computes initial (90d) and incremental (14d overlap) synchronization ranges.
Captures retrospective AWS billing revisions and aligns with 14d resource CE limits.
"""

from datetime import date, timedelta
from typing import Tuple, Optional

# Bounded historical period for first-time onboarding
INITIAL_SYNC_DAYS = 90

# Retrospective overlap window for subsequent syncs to capture billing adjustments
INCREMENTAL_OVERLAP_DAYS = 14


class SyncWindowCalculator:
    """Calculates deterministic sync windows for initial and incremental ingestions."""

    @staticmethod
    def compute_sync_window(
        last_sync_date: Optional[date] = None,
        target_end_date: Optional[date] = None,
        initial_days: int = INITIAL_SYNC_DAYS,
        overlap_days: int = INCREMENTAL_OVERLAP_DAYS,
    ) -> Tuple[date, date, bool]:
        """
        Computes (start_date, end_date, is_initial).
        - Initial sync: past 90 days up to today.
        - Incremental sync: past 14 days up to today (absorbs billing revisions & CE resource limits).
        """
        end_date = target_end_date or date.today()

        if last_sync_date is None:
            start_date = end_date - timedelta(days=initial_days)
            return start_date, end_date, True

        start_date = end_date - timedelta(days=overlap_days)
        return start_date, end_date, False
