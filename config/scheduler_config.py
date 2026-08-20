# Configured local time for the morning brief job.
# Change this to whatever time the delivery lead wants the brief posted.
MORNING_BRIEF_HOUR = 9
MORNING_BRIEF_MINUTE = 0

# Configured local time for the end-of-day summary job.
EOD_SUMMARY_HOUR = 18
EOD_SUMMARY_MINUTE = 0

# Blocker age (in days) at or beyond which a promotion proposal is generated.
BLOCKER_PROMOTION_THRESHOLD_DAYS = 2

PROMOTION_CHECK_HOUR = 9
PROMOTION_CHECK_MINUTE = 30

COMMITMENT_CHECK_HOUR = 8
COMMITMENT_CHECK_MINUTE = 30

WEEKLY_REPORT_DAY_OF_WEEK = 'mon'
WEEKLY_REPORT_HOUR = 8
WEEKLY_REPORT_MINUTE = 0

# Sprint planning: team capacity stated as a number of items per
# sprint. This is a human-provided input, not computed - converting
# it into a candidate-slice size (capacity minus carry-over) is an
# ASSUMPTION, disclosed explicitly in the planning pack output.
TEAM_CAPACITY_ITEMS_PER_SPRINT = 12

SPRINT_PLANNING_DAY_OF_WEEK = 'fri'
SPRINT_PLANNING_HOUR = 15
SPRINT_PLANNING_MINUTE = 0


# Which implementation each adapter factory should construct.
# "mock" is the only implementation that exists today (per the
# brief: no licensed SaaS, adapters+mocks only). This is what the
# factory reads to decide - a real integration would be added as
# a new implementation class plus a new branch here, with zero
# changes to any agent logic that calls the factory.
ADAPTER_MODE = "mock"
