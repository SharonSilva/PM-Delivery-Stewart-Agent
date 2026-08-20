from apscheduler.schedulers.blocking import BlockingScheduler

from config.scheduler_config import (
    MORNING_BRIEF_HOUR, MORNING_BRIEF_MINUTE,
    EOD_SUMMARY_HOUR, EOD_SUMMARY_MINUTE,
)
from scheduler.morning_brief_job import run_morning_brief_job
from scheduler.eod_summary_job import run_eod_summary_job


def start_scheduler() -> None:
    """A REAL scheduler with two jobs: morning brief and end-of-day
    summary, each at its configured local time."""
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
    print(
        f"Scheduler started. Morning brief at {MORNING_BRIEF_HOUR:02d}:{MORNING_BRIEF_MINUTE:02d}, "
        f"EOD summary at {EOD_SUMMARY_HOUR:02d}:{EOD_SUMMARY_MINUTE:02d}."
    )
    scheduler.start()


if __name__ == "__main__":
    start_scheduler()
