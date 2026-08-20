from apscheduler.schedulers.blocking import BlockingScheduler

from config.scheduler_config import (
    MORNING_BRIEF_HOUR, MORNING_BRIEF_MINUTE,
    EOD_SUMMARY_HOUR, EOD_SUMMARY_MINUTE,
    PROMOTION_CHECK_HOUR, PROMOTION_CHECK_MINUTE,
    COMMITMENT_CHECK_HOUR, COMMITMENT_CHECK_MINUTE,
    WEEKLY_REPORT_DAY_OF_WEEK, WEEKLY_REPORT_HOUR, WEEKLY_REPORT_MINUTE,
)
from scheduler.morning_brief_job import run_morning_brief_job
from scheduler.eod_summary_job import run_eod_summary_job
from scheduler.promotion_job import run_promotion_check_job
from scheduler.commitment_job import run_commitment_check_job
from scheduler.weekly_report_job import run_weekly_report_job


def start_scheduler() -> None:
    """A REAL scheduler with five jobs: morning brief (+risk-gap
    detection), commitment check, blocker-promotion check, EOD
    summary (all daily), and the weekly status report."""
    scheduler = BlockingScheduler()
    scheduler.add_job(run_morning_brief_job, trigger="cron",
                       hour=MORNING_BRIEF_HOUR, minute=MORNING_BRIEF_MINUTE, id="morning_brief")
    scheduler.add_job(run_commitment_check_job, trigger="cron",
                       hour=COMMITMENT_CHECK_HOUR, minute=COMMITMENT_CHECK_MINUTE, id="commitment_check")
    scheduler.add_job(run_promotion_check_job, trigger="cron",
                       hour=PROMOTION_CHECK_HOUR, minute=PROMOTION_CHECK_MINUTE, id="promotion_check")
    scheduler.add_job(run_eod_summary_job, trigger="cron",
                       hour=EOD_SUMMARY_HOUR, minute=EOD_SUMMARY_MINUTE, id="eod_summary")
    scheduler.add_job(run_weekly_report_job, trigger="cron",
                       day_of_week=WEEKLY_REPORT_DAY_OF_WEEK, hour=WEEKLY_REPORT_HOUR,
                       minute=WEEKLY_REPORT_MINUTE, id="weekly_report")
    print("Scheduler started with 5 jobs (4 daily + 1 weekly).")
    scheduler.start()


if __name__ == "__main__":
    start_scheduler()
