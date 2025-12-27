# Jiffy Time Tracker Exporter

Convert Jiffy time tracker JSON to Toggl Track or Clockify CSV format.

## Quick Start

```bash
# View entries (default: last 5)
python3 jiffy_export.py

# Convert to Toggl Track CSV
python3 jiffy_export.py --email your@email.com

# Convert to Clockify CSV
python3 jiffy_export.py -m clockify --email your@email.com
```

## Usage

```bash
python3 jiffy_export.py [input_file] [options]

Options:
  -m, --mode          Mode: toggl (default), clockify, or print-only
  -o, --output        Output CSV file path
  --email             Email address (required for toggl/clockify)
  -n NUM              Number of entries to display (default: 5)
  -f, --from-date     Filter from date (YYYY-MM-DD)
  -t, --to-date       Filter to date (YYYY-MM-DD)
  --output-timezone   Output timezone (default: Asia/Bangkok)
```

## Setup

1. Export Jiffy data to JSON (Jiffy app: Settings → Export)
2. Place file at `data/jiffy_input.json`
3. Run the script

## Notes

- Converts UTC milliseconds to local time
- Filters only ACTIVE entries
- Supports timezone conversion
