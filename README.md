# Jiffy to Toggl Track Converter

Convert Jiffy time tracker JSON export to Toggl Track CSV format.

## Folder Structure

```
jiffy/
├── convert_jiffy_toggl.py    # Main script
├── README.md                  # This file
└── data/
    ├── jiffy_input.json       # Your Jiffy export (place here)
```

## Quick Start

```bash
# View last 5 entries
python3 convert_jiffy_toggl.py

# View entries for specific date
python3 convert_jiffy_toggl.py -d 2025-12-24

# View last 10 entries
python3 convert_jiffy_toggl.py -n 10
```

## Options

```bash
python3 convert_jiffy_toggl.py [input_file] [-n NUM] [-d DATE]

Arguments:
  input_file          Input file (default: data/jiffy_input.json)
  -n NUM              Number of entries to show (default: 5)
  -d DATE             Filter by date (format: YYYY-MM-DD)
  -h, --help          Show help
```

## Setup

1. Export your Jiffy data to JSON (from Jiffy app: Settings → Export)
2. Place the file in `data/jiffy_input.json`
3. Run the script

## Notes

- Jiffy stores times in UTC milliseconds
- Script converts to Bangkok time (UTC+7)
- Only shows ACTIVE entries (not deleted ones)
