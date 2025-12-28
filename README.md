# Time Tracker Exporters

Convert time tracking data between formats: Jiffy → Toggl/Clockify, Toggl → Clockify.

## Jiffy Exporter to Toggl / Clockify

Convert Jiffy JSON to Toggl Track or Clockify CSV.

**Setup:**
1. Export Jiffy data (Settings → Export) to `data/jiffy_input.json`
2. Run script with desired mode

**Quick Start:**
```bash
# View entries
python jiffy_export.py

# Convert to Toggl Track
python jiffy_export.py -m toggl --email your@email.com -f 2025-01-01 -t 2025-12-31 --output-timezone Asia/Bangkok

# Convert to Clockify
python jiffy_export.py -m clockify --email your@email.com -f 2025-01-01 -t 2025-12-31 --output-timezone Asia/Bangkok
```

**Options:** `-m` mode, `-o` output, `--email`, `-n` num entries, `-f`/`-t` date range, `--output-timezone`

## Toggl Exporter to Clockify

Convert Toggl Track CSV to Clockify CSV with client mapping.

**Setup:**
1. Export Toggl data to `data/toggl_input.csv`
2. (Optional) Export Toggl projects to `data/toggl_projects.json` for client mapping
3. Run script

**Quick Start:**
```bash
# View entries
python toggl_export.py

# Convert to Clockify
python toggl_export.py -m clockify -f 2025-01-01 -t 2025-12-31
```

**Options:** `-m` mode, `-o` output, `-p` projects file, `-n` num entries, `-f`/`-t` date range
