from apscheduler.schedulers.blocking import BlockingScheduler

from config.scheduler_config import (
    MORNING_BRIEF_HOUR, MORNING_BRIEF_MINUTE,
    EOD_SUMMARY_HOUR, EOD_SUMMARY_MINUTE,
    PROMOTION_CHECK_HOUR, PROMOTION_CHECK_MINUTE,
)
from scheduler.morning_brief_job import run_morning_brief_job
from scheduler.eod_summary_job import run_eod_summary_job
from scheduler.promotion_job import run_promotion_check_job


def start_scheduler() -> None:
    """A REAL scheduler with three jobs: morning brief (which also
    runs risk-gap detection right after), end-of-day summary, and
    the daily blocker-promotion check."""
    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_morning_brief_job,
        trigger="cron",
        hour=MORNING_BRIEF_HOUR,
        minute=MORNING_BRIEF_MINUTE,
        id="morning_brief",
    )
    scheduler.add_job(
        run_eod_summary_job,
        trigger="cron",
        hour=EOD_SUMMARY_HOUR,
        minute=EOD_SUMMARY_MINUTE,
        id="eod_summary",
    )
    scheduler.add_job(
        run_promotion_check_job,
        trigger="cron",
        hour=PROMOTION_CHECK_HOUR,
        minute=PROMOTION_CHECK_MINUTE,
        id="promotion_check",
    )
    print(
        f"Scheduler started. Morning brief {MORNING_BRIEF_HOUR:02d}:{MORNING_BRIEF_MINUTE:02d}, "
        f"promotion check {PROMOTION_CHECK_HOUR:02d}:{PROMOTION_CHECK_MINUTE:02d}, "
        f"EOD summary {EOD_SUMMARY_HOUR:02d}:{EOD_SUMMARY_MINUTE:02d}."
    )
    scheduler.start()


if __name__ == "__main__":
    start_scheduler()
