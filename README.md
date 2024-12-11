# Dam Levels Tracker

This script automatically scrapes dam level data from the Department of Water and Sanitation website for all regions in South Africa.

## Setup

1. Install the required packages:
```
pip install -r requirements.txt
```

2. The script is set up to run automatically through Windows Task Scheduler.

## Features

- Scrapes dam level data for all South African regions
- Creates an Excel file with separate sheets for each region
- Includes a master sheet with average levels for each region
- Generates dated output files (format: dam_levels_YYYYMMDD.xlsx)
- Includes logging for tracking execution and debugging

## Output

The script generates:
- An Excel file named `dam_levels_YYYYMMDD.xlsx` (where YYYYMMDD is the current date)
- A log file `dam_levels.log` tracking execution details and any errors

## Scheduling

The script is scheduled to run automatically through Windows Task Scheduler. You can modify the schedule through the Task Scheduler interface.
