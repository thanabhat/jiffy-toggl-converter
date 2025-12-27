#!/usr/bin/env python3
"""
Convert Jiffy time tracker JSON export to Toggl Track CSV format
"""

import json
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path


def parse_jiffy_timestamp(timestamp_ms, tz_name='Asia/Bangkok'):
    """Convert Jiffy timestamp (milliseconds) to datetime object in local timezone
    
    Jiffy stores timestamps in UTC milliseconds, but displays them in local time.
    For Asia/Bangkok, we need to add 7 hours to UTC.
    """
    dt_utc = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
    
    # Convert to Bangkok time (UTC+7)
    if tz_name == 'Asia/Bangkok':
        dt_local = dt_utc + timedelta(hours=7)
        return dt_local.replace(tzinfo=None)  # Remove tzinfo for cleaner display
    
    return dt_utc


def format_duration(start_ms, stop_ms):
    """Calculate and format duration in HH:MM:SS format"""
    duration_seconds = (stop_ms - start_ms) / 1000
    hours = int(duration_seconds // 3600)
    minutes = int((duration_seconds % 3600) // 60)
    seconds = int(duration_seconds % 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}"


def get_owner_name(owner_id, time_owners):
    """Get the owner name from owner_id"""
    for owner in time_owners:
        if owner['id'] == owner_id:
            return owner.get('name', 'Unknown')
    return 'Unknown'


def load_jiffy_data(json_file):
    """Load and parse Jiffy JSON file"""
    with open(json_file, 'r') as f:
        return json.load(f)


def print_examples(data, num_examples=5, filter_date=None):
    """Print example entries from Jiffy data
    
    Args:
        data: Jiffy data dictionary
        num_examples: Number of examples to show
        filter_date: Optional date string in format 'YYYY-MM-DD' to filter entries
    """
    time_entries = data.get('time_entries', [])
    time_owners = data.get('time_owners', [])
    
    print(f"\n{'='*80}")
    print(f"Jiffy Data Summary")
    print(f"{'='*80}")
    print(f"Total time entries: {len(time_entries)}")
    print(f"Total time owners (categories): {len(time_owners)}")
    
    print(f"\n{'='*80}")
    print(f"Time Owners (Categories)")
    print(f"{'='*80}")
    for owner in time_owners[:10]:  # Show first 10 categories
        parent_id = owner.get('parent_id', '')
        parent_info = f" (parent: {parent_id[:8]}...)" if parent_id else " (top-level)"
        print(f"  - {owner['name']:<30} | ID: {owner['id'][:8]}... | Status: {owner['status']}{parent_info}")
    
    if len(time_owners) > 10:
        print(f"  ... and {len(time_owners) - 10} more")
    
    # Filter active entries
    active_entries = [e for e in time_entries if e.get('status') == 'ACTIVE']
    
    # Filter by date if specified
    if filter_date:
        try:
            target_date = datetime.strptime(filter_date, '%Y-%m-%d').date()
            filtered_entries = []
            for entry in active_entries:
                start_dt = parse_jiffy_timestamp(entry['start_time'], entry['start_time_zone'])
                if start_dt.date() == target_date:
                    filtered_entries.append(entry)
            active_entries = filtered_entries
            print(f"\n{'='*80}")
            print(f"Time Entries for {filter_date} ({len(active_entries)} entries)")
            print(f"{'='*80}")
        except ValueError:
            print(f"\nWarning: Invalid date format '{filter_date}'. Use YYYY-MM-DD format.")
            print(f"Showing last {num_examples} entries instead.\n")
            active_entries = active_entries[-num_examples:]
    else:
        print(f"\n{'='*80}")
        print(f"Example Time Entries (last {num_examples})")
        print(f"{'='*80}")
        active_entries = active_entries[-num_examples:]
    
    for i, entry in enumerate(active_entries, 1):
        start_dt = parse_jiffy_timestamp(entry['start_time'], entry['start_time_zone'])
        stop_dt = parse_jiffy_timestamp(entry['stop_time'], entry['stop_time_zone'])
        duration = format_duration(entry['start_time'], entry['stop_time'])
        owner_name = get_owner_name(entry['owner_id'], time_owners)
        note = entry.get('note', '-')
        
        print(f"\nEntry {i}:")
        print(f"  Category: {owner_name}")
        print(f"  Note: {note}")
        print(f"  Start: {start_dt.strftime('%Y-%m-%d %H:%M:%S')} ({entry['start_time_zone']})")
        print(f"  Stop:  {stop_dt.strftime('%Y-%m-%d %H:%M:%S')} ({entry['stop_time_zone']})")
        print(f"  Duration: {duration}")
        print(f"  Status: {entry['status']}")
    
    # Show some statistics
    print(f"\n{'='*80}")
    print(f"Statistics")
    print(f"{'='*80}")
    active_count = sum(1 for e in time_entries if e.get('status') == 'ACTIVE')
    deleted_count = sum(1 for e in time_entries if e.get('status') == 'DELETED')
    with_notes = sum(1 for e in time_entries if e.get('note'))
    
    print(f"  Active entries: {active_count}")
    print(f"  Deleted entries: {deleted_count}")
    print(f"  Entries with notes: {with_notes}")
    
    if time_entries:
        oldest = min(time_entries, key=lambda e: e['start_time'])
        newest = max(time_entries, key=lambda e: e['start_time'])
        oldest_dt = parse_jiffy_timestamp(oldest['start_time'], oldest['start_time_zone'])
        newest_dt = parse_jiffy_timestamp(newest['start_time'], newest['start_time_zone'])
        print(f"  Date range: {oldest_dt.strftime('%Y-%m-%d')} to {newest_dt.strftime('%Y-%m-%d')}")


def main():
    parser = argparse.ArgumentParser(
        description='Convert Jiffy time tracker JSON to Toggl Track CSV format'
    )
    parser.add_argument(
        'input_file',
        nargs='?',
        default='data/jiffy_input.json',
        help='Input Jiffy JSON file (default: data/jiffy_input.json)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output CSV file (default: auto-generated based on input filename)'
    )
    parser.add_argument(
        '-n', '--num-examples',
        type=int,
        default=5,
        help='Number of example entries to print (default: 5)'
    )
    parser.add_argument(
        '-d', '--date',
        help='Filter entries by date (format: YYYY-MM-DD, e.g., 2025-12-24)'
    )
    
    args = parser.parse_args()
    
    # Check if input file exists
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file '{args.input_file}' not found")
        return 1
    
    print(f"Loading Jiffy data from: {args.input_file}")
    data = load_jiffy_data(args.input_file)
    
    # Print examples
    print_examples(data, args.num_examples, args.date)
    
    print(f"\n{'='*80}")
    print("Data loaded successfully!")
    print(f"{'='*80}\n")
    
    return 0


if __name__ == '__main__':
    exit(main())
