#!/usr/bin/env python
"""
Convert Jiffy time tracker JSON export to Toggl Track CSV format
"""

import json
import csv
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


def parse_jiffy_timestamp(timestamp_ms, tz_name='Asia/Bangkok'):
    """Convert Jiffy timestamp (milliseconds) to datetime object in local timezone
    
    Jiffy stores timestamps in UTC milliseconds, but displays them in local time.
    Handles both IANA timezone names (e.g., 'Asia/Bangkok') and GMT offset formats (e.g., 'GMT+07:00').
    """
    dt_utc = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
    
    # Handle GMT offset format (e.g., 'GMT+07:00' or 'GMT-05:00')
    if tz_name.startswith('GMT'):
        # Extract the offset part (e.g., '+07:00')
        offset_str = tz_name[3:]  # Remove 'GMT' prefix
        if offset_str:
            # Parse hours and minutes
            sign = 1 if offset_str[0] == '+' else -1
            parts = offset_str[1:].split(':')
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            offset = timedelta(hours=sign * hours, minutes=sign * minutes)
            dt_local = dt_utc + offset
            return dt_local.replace(tzinfo=None)
    
    # Use ZoneInfo for IANA timezone names
    try:
        dt_local = dt_utc.astimezone(ZoneInfo(tz_name))
        return dt_local.replace(tzinfo=None)
    except Exception:
        # Fallback to UTC if timezone is not recognized
        return dt_utc.replace(tzinfo=None)


def convert_to_output_timezone(timestamp_ms, input_tz_name, output_tz_name='Asia/Bangkok'):
    """Convert Jiffy timestamp to a specific output timezone
    
    Args:
        timestamp_ms: Jiffy timestamp in milliseconds
        input_tz_name: Original timezone of the entry
        output_tz_name: Target timezone for conversion
    
    Returns:
        datetime object in the output timezone (timezone-naive)
    """
    # First convert to UTC
    dt_utc = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
    
    # Then convert to output timezone
    if output_tz_name.startswith('GMT'):
        # Handle GMT offset format
        offset_str = output_tz_name[3:]
        if offset_str:
            sign = 1 if offset_str[0] == '+' else -1
            parts = offset_str[1:].split(':')
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            offset = timedelta(hours=sign * hours, minutes=sign * minutes)
            dt_output = dt_utc + offset
            return dt_output.replace(tzinfo=None)
    
    # Use ZoneInfo for IANA timezone names
    try:
        dt_output = dt_utc.astimezone(ZoneInfo(output_tz_name))
        return dt_output.replace(tzinfo=None)
    except Exception:
        # Fallback to UTC if timezone is not recognized
        return dt_utc.replace(tzinfo=None)


def format_duration(start_ms, stop_ms):
    """Calculate and format duration in HH:MM:SS format"""
    duration_seconds = (stop_ms - start_ms) / 1000
    hours = int(duration_seconds // 3600)
    minutes = int((duration_seconds % 3600) // 60)
    seconds = int(duration_seconds % 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}"


def format_duration_hours(start_ms, stop_ms):
    """Calculate and format duration in decimal hours for Clockify"""
    duration_seconds = (stop_ms - start_ms) / 1000
    hours = duration_seconds / 3600
    return f"{hours:.2f}"


def get_owner_name(owner_id, time_owners):
    """Get the owner name from owner_id"""
    for owner in time_owners:
        if owner['id'] == owner_id:
            return owner.get('name', 'Unknown')
    return 'Unknown'


def get_parent_owner_name(owner_id, time_owners):
    """Get the parent owner name (client) from owner_id"""
    for owner in time_owners:
        if owner['id'] == owner_id:
            parent_id = owner.get('parent_id')
            if parent_id:
                # Find parent name
                for parent_owner in time_owners:
                    if parent_owner['id'] == parent_id:
                        return parent_owner.get('name', '')
            return ''  # No parent
    return ''


def load_jiffy_data(json_file):
    """Load and parse Jiffy JSON file"""
    with open(json_file, 'r') as f:
        return json.load(f)


def convert_to_toggl(data, output_file, email, from_date=None, to_date=None, output_timezone='Asia/Bangkok'):
    """Convert Jiffy data to Toggl Track CSV format
    
    Args:
        data: Jiffy data dictionary
        output_file: Output CSV file path
        email: Email address for the CSV
        from_date: Optional start date string in format 'YYYY-MM-DD'
        to_date: Optional end date string in format 'YYYY-MM-DD'
        output_timezone: Timezone for output timestamps (default: 'Asia/Bangkok')
    """
    time_entries = data.get('time_entries', [])
    time_owners = data.get('time_owners', [])
    
    # Filter active entries
    active_entries = [e for e in time_entries if e.get('status') == 'ACTIVE']
    
    # Filter by date range if specified
    if from_date or to_date:
        start_date = datetime.strptime(from_date, '%Y-%m-%d').date() if from_date else None
        end_date = datetime.strptime(to_date, '%Y-%m-%d').date() if to_date else None
        
        filtered_entries = []
        for entry in active_entries:
            entry_dt = parse_jiffy_timestamp(entry['start_time'], entry['start_time_zone'])
            entry_date = entry_dt.date()
            
            if start_date and entry_date < start_date:
                continue
            if end_date and entry_date > end_date:
                continue
            filtered_entries.append(entry)
        
        active_entries = filtered_entries
    
    # Sort entries by start time
    active_entries.sort(key=lambda e: e['start_time'])
    
    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Description', 'Billable', 'Duration', 'Email', 'Project', 
                      'Start date', 'Start time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        
        writer.writeheader()
        
        for entry in active_entries:
            start_dt = convert_to_output_timezone(entry['start_time'], entry['start_time_zone'], output_timezone)
            stop_dt = convert_to_output_timezone(entry['stop_time'], entry['stop_time_zone'], output_timezone)
            duration = format_duration(entry['start_time'], entry['stop_time'])
            project = get_owner_name(entry['owner_id'], time_owners)
            description = entry.get('note', '-')
            
            row = {
                'Description': description or '',
                'Billable': 'No',
                'Duration': duration,
                'Email': email,
                'Project': project,
                'Start date': start_dt.strftime('%Y-%m-%d'),
                'Start time': start_dt.strftime('%H:%M:%S')
            }
            
            writer.writerow(row)
    
    print(f"\nConverted {len(active_entries)} entries to {output_file}")
    if from_date or to_date:
        date_range = f" from {from_date or 'beginning'}" if from_date else ""
        date_range += f" to {to_date or 'now'}" if to_date else ""
        print(f"Date range:{date_range}")
    print(f"Email: {email}")
    print(f"Output timezone: {output_timezone}")


def convert_to_clockify(data, output_file, email, from_date=None, to_date=None, output_timezone='Asia/Bangkok'):
    """Convert Jiffy data to Clockify CSV format
    
    Args:
        data: Jiffy data dictionary
        output_file: Output CSV file path
        email: Email address for the CSV
        from_date: Optional start date string in format 'YYYY-MM-DD'
        to_date: Optional end date string in format 'YYYY-MM-DD'
        output_timezone: Timezone for output timestamps (default: 'Asia/Bangkok')
    """
    time_entries = data.get('time_entries', [])
    time_owners = data.get('time_owners', [])
    
    # Filter active entries
    active_entries = [e for e in time_entries if e.get('status') == 'ACTIVE']
    
    # Filter by date range if specified
    if from_date or to_date:
        start_date = datetime.strptime(from_date, '%Y-%m-%d').date() if from_date else None
        end_date = datetime.strptime(to_date, '%Y-%m-%d').date() if to_date else None
        
        filtered_entries = []
        for entry in active_entries:
            entry_dt = parse_jiffy_timestamp(entry['start_time'], entry['start_time_zone'])
            entry_date = entry_dt.date()
            
            if start_date and entry_date < start_date:
                continue
            if end_date and entry_date > end_date:
                continue
            filtered_entries.append(entry)
        
        active_entries = filtered_entries
    
    # Sort entries by start time
    active_entries.sort(key=lambda e: e['start_time'])
    
    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Project', 'Client', 'Description', 'Task', 'Email', 'Tags', 'Billable',
                      'Start Date', 'Start Time', 'Duration (h)']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_NONNUMERIC)
        
        writer.writeheader()
        
        for entry in active_entries:
            start_dt = convert_to_output_timezone(entry['start_time'], entry['start_time_zone'], output_timezone)
            stop_dt = convert_to_output_timezone(entry['stop_time'], entry['stop_time_zone'], output_timezone)
            duration = format_duration(entry['start_time'], entry['stop_time'])
            project = get_owner_name(entry['owner_id'], time_owners)
            client = get_parent_owner_name(entry['owner_id'], time_owners)
            description = entry.get('note', '')
            
            row = {
                'Project': project,
                'Client': client,
                'Description': description or '',
                'Task': '',
                'Email': email,
                'Tags': '',
                'Billable': 'No',
                'Start Date': start_dt.strftime('%m/%d/%Y'),
                'Start Time': start_dt.strftime('%-I:%M %p'),
                'Duration (h)': duration
            }
            
            writer.writerow(row)
    
    print(f"\nConverted {len(active_entries)} entries to {output_file}")
    if from_date or to_date:
        date_range = f" from {from_date or 'beginning'}" if from_date else ""
        date_range += f" to {to_date or 'now'}" if to_date else ""
        print(f"Date range:{date_range}")
    print(f"Email: {email}")
    print(f"Output timezone: {output_timezone}")


def print_examples(data, num_examples=5, from_date=None, to_date=None):
    """Print example entries from Jiffy data
    
    Args:
        data: Jiffy data dictionary
        num_examples: Number of examples to show
        from_date: Optional start date string in format 'YYYY-MM-DD' to filter entries
        to_date: Optional end date string in format 'YYYY-MM-DD' to filter entries
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
    
    # Filter by date range if specified
    if from_date or to_date:
        try:
            start_date = datetime.strptime(from_date, '%Y-%m-%d').date() if from_date else None
            end_date = datetime.strptime(to_date, '%Y-%m-%d').date() if to_date else None
            
            filtered_entries = []
            for entry in active_entries:
                entry_dt = parse_jiffy_timestamp(entry['start_time'], entry['start_time_zone'])
                entry_date = entry_dt.date()
                
                # Check if entry falls within the date range
                if start_date and entry_date < start_date:
                    continue
                if end_date and entry_date > end_date:
                    continue
                filtered_entries.append(entry)
            
            active_entries = filtered_entries
            print(f"\n{'='*80}")
            if from_date and to_date:
                print(f"Time Entries from {from_date} to {to_date} ({len(active_entries)} entries)")
            elif from_date:
                print(f"Time Entries from {from_date} onwards ({len(active_entries)} entries)")
            else:
                print(f"Time Entries up to {to_date} ({len(active_entries)} entries)")
            print(f"{'='*80}")
        except ValueError as e:
            print(f"\nWarning: Invalid date format. Use YYYY-MM-DD format.")
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
        '-m', '--mode',
        choices=['toggl', 'clockify', 'print-only'],
        default='print-only',
        help='Operation mode: toggl (default, convert to Toggl CSV), clockify (convert to Clockify CSV), or print-only (display data without conversion)'
    )
    parser.add_argument(
        '-o', '--output',
        default=None,
        help='Output CSV file (default: data/toggl_output.csv for toggl mode, data/clockify_output.csv for clockify mode)'
    )
    parser.add_argument(
        '--email',
        required=False,
        help='Email address for Toggl CSV (required for convert mode)'
    )
    parser.add_argument(
        '--output-timezone',
        default='Asia/Bangkok',
        help='Timezone for output CSV timestamps (default: Asia/Bangkok)'
    )
    parser.add_argument(
        '-n', '--num-examples',
        type=int,
        default=5,
        help='Number of example entries to print (default: 5)'
    )
    parser.add_argument(
        '-f', '--from-date',
        help='Filter entries from this date (format: YYYY-MM-DD, e.g., 2025-12-24)'
    )
    parser.add_argument(
        '-t', '--to-date',
        help='Filter entries to this date (format: YYYY-MM-DD, e.g., 2025-12-27)'
    )
    
    args = parser.parse_args()
    
    # Check if input file exists
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file '{args.input_file}' not found")
        return 1
    
    print(f"Loading Jiffy data from: {args.input_file}")
    data = load_jiffy_data(args.input_file)
    
    # Handle print-only mode
    if args.mode == 'print-only':
        print_examples(data, args.num_examples, args.from_date, args.to_date)
        print(f"\n{'='*80}")
        print("Data loaded successfully!")
        print(f"{'='*80}\n")
        return 0
    
    # Handle toggl mode (default)
    if args.mode == 'toggl':
        # Check required parameters for toggl mode
        if not args.email:
            print("Error: --email is required for toggl mode")
            print("Example: python convert_jiffy_toggl.py --email 'your@email.com'")
            return 1
        
        # Set default output file if not specified
        output_file = args.output if args.output else 'data/toggl_output.csv'
        
        convert_to_toggl(data, output_file, args.email, args.from_date, args.to_date, args.output_timezone)
        print(f"\n{'='*80}")
        print("Conversion completed successfully!")
        print(f"{'='*80}\n")
        return 0
    
    # Handle clockify mode
    if args.mode == 'clockify':
        # Check required parameters for clockify mode
        if not args.email:
            print("Error: --email is required for clockify mode")
            print("Example: python convert_jiffy_toggl.py -m clockify --email 'your@email.com'")
            return 1
        
        # Set default output file if not specified
        output_file = args.output if args.output else 'data/clockify_output.csv'
        
        convert_to_clockify(data, output_file, args.email, args.from_date, args.to_date, args.output_timezone)
        print(f"\n{'='*80}")
        print("Conversion completed successfully!")
        print(f"{'='*80}\n")
        return 0
    
    return 0


if __name__ == '__main__':
    exit(main())
