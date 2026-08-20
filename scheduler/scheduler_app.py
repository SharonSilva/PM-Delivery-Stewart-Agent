from apscheduler.schedulers.blocking import BlockingScheduler

from config.scheduler_config import MORNING_BRIEF_HOUR, MORNING_BRIEF_MINUTE
from scheduler.morning_brief_job import run_morning_brief_job


def start_scheduler() -> None:
    """A REAL scheduler, not a manual trigger button. Runs the
    morning brief job at the configured local time, every day."""
    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_morning_brief_job,
        trigger="cron",
        hour=MORNING_BRIEF_HOUR,
        minute=MORNING_BRIEF_MINUTE,
        id="morning_brief",
    )
    print(f"Scheduler started. Morning brief will run daily at {MORNING_BRIEF_HOUR:02d}:{MORNING_BRIEF_MINUTE:02d}.")
    scheduler.start()


if __name__ == "__main__":
    start_scheduler()
