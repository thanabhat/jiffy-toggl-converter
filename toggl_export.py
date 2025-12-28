#!/usr/bin/env python
"""
Convert Toggl Track CSV export to Clockify CSV format
"""

import csv
import argparse
import json
from datetime import datetime
from pathlib import Path


def parse_toggl_duration(duration_str):
    """Parse Toggl duration string (HH:MM:SS) to seconds"""
    parts = duration_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2])
    return hours * 3600 + minutes * 60 + seconds


def format_duration_hms(seconds):
    """Convert seconds to HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours}:{minutes:02d}:{secs:02d}"


def load_toggl_csv(csv_file):
    """Load and parse Toggl CSV file"""
    entries = []
    with open(csv_file, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize the row by removing quotes from keys
            normalized_row = {}
            for key, value in row.items():
                clean_key = key.strip('"')
                normalized_row[clean_key] = value
            entries.append(normalized_row)
    return entries


def load_projects_json(json_file):
    """Load Toggl projects JSON file and create project to client mapping
    
    Args:
        json_file: Path to the projects JSON file
        
    Returns:
        Dictionary mapping project name to client name
    """
    with open(json_file, 'r', encoding='utf-8') as f:
        projects = json.load(f)
    
    # Create mapping from project name to client name
    project_to_client = {}
    for project in projects:
        project_name = project.get('name', '')
        client_name = project.get('client_name', '')
        if project_name:
            project_to_client[project_name] = client_name
    
    return project_to_client


def convert_to_clockify(entries, output_file, from_date=None, to_date=None, project_to_client=None):
    """Convert Toggl data to Clockify CSV format
    
    Args:
        entries: List of Toggl entries from CSV
        output_file: Output CSV file path
        from_date: Optional start date string in format 'YYYY-MM-DD'
        to_date: Optional end date string in format 'YYYY-MM-DD'
        project_to_client: Optional dictionary mapping project names to client names
    """
    # Filter by date range if specified
    if from_date or to_date:
        start_date = datetime.strptime(from_date, '%Y-%m-%d').date() if from_date else None
        end_date = datetime.strptime(to_date, '%Y-%m-%d').date() if to_date else None
        
        filtered_entries = []
        for entry in entries:
            entry_date = datetime.strptime(entry['Start date'], '%Y-%m-%d').date()
            
            if start_date and entry_date < start_date:
                continue
            if end_date and entry_date > end_date:
                continue
            filtered_entries.append(entry)
        
        entries = filtered_entries
    
    # Write to Clockify CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Project', 'Client', 'Description', 'Task', 'Email', 'Tags', 'Billable',
                      'Start Date', 'Start Time', 'Duration (h)']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_NONNUMERIC)
        
        writer.writeheader()
        
        for entry in entries:
            # Parse duration
            duration_seconds = parse_toggl_duration(entry['Duration'])
            duration_hms = format_duration_hms(duration_seconds)
            
            # Parse start date/time and convert to Clockify format
            start_date = datetime.strptime(entry['Start date'], '%Y-%m-%d')
            start_time = datetime.strptime(entry['Start time'], '%H:%M:%S')
            
            # Get client name from project mapping if available
            project_name = entry.get('Project', '')
            client_name = ''
            if project_to_client and project_name:
                client_name = project_to_client.get(project_name, '')
            
            row = {
                'Project': project_name,
                'Client': client_name,
                'Description': entry.get('Description', ''),
                'Task': '',
                'Email': entry.get('Email', ''),
                'Tags': '',
                'Billable': entry.get('Billable', 'No'),
                'Start Date': start_date.strftime('%m/%d/%Y'),
                'Start Time': start_time.strftime('%-I:%M %p'),
                'Duration (h)': duration_hms
            }
            
            writer.writerow(row)
    
    print(f"\nConverted {len(entries)} entries to {output_file}")
    if from_date or to_date:
        date_range = f" from {from_date or 'beginning'}" if from_date else ""
        date_range += f" to {to_date or 'now'}" if to_date else ""
        print(f"Date range:{date_range}")


def print_examples(entries, num_examples=5, from_date=None, to_date=None):
    """Print example entries from Toggl data
    
    Args:
        entries: List of Toggl entries from CSV
        num_examples: Number of examples to show
        from_date: Optional start date string in format 'YYYY-MM-DD' to filter entries
        to_date: Optional end date string in format 'YYYY-MM-DD' to filter entries
    """
    print(f"\n{'='*80}")
    print(f"Toggl Data Summary")
    print(f"{'='*80}")
    print(f"Total time entries: {len(entries)}")
    
    # Filter by date range if specified
    display_entries = entries
    if from_date or to_date:
        try:
            start_date = datetime.strptime(from_date, '%Y-%m-%d').date() if from_date else None
            end_date = datetime.strptime(to_date, '%Y-%m-%d').date() if to_date else None
            
            filtered_entries = []
            for entry in entries:
                entry_date = datetime.strptime(entry['Start date'], '%Y-%m-%d').date()
                
                if start_date and entry_date < start_date:
                    continue
                if end_date and entry_date > end_date:
                    continue
                filtered_entries.append(entry)
            
            display_entries = filtered_entries
            print(f"\n{'='*80}")
            if from_date and to_date:
                print(f"Time Entries from {from_date} to {to_date} ({len(display_entries)} entries)")
            elif from_date:
                print(f"Time Entries from {from_date} onwards ({len(display_entries)} entries)")
            else:
                print(f"Time Entries up to {to_date} ({len(display_entries)} entries)")
            print(f"{'='*80}")
        except ValueError as e:
            print(f"\nWarning: Invalid date format. Use YYYY-MM-DD format.")
            print(f"Showing last {num_examples} entries instead.\n")
            display_entries = entries[-num_examples:]
    else:
        print(f"\n{'='*80}")
        print(f"Example Time Entries (last {num_examples})")
        print(f"{'='*80}")
        display_entries = entries[-num_examples:]
    
    for i, entry in enumerate(display_entries[-num_examples:], 1):
        print(f"\nEntry {i}:")
        print(f"  Project: {entry.get('Project', '-')}")
        print(f"  Description: {entry.get('Description', '-')}")
        print(f"  Start: {entry['Start date']} {entry['Start time']}")
        if 'Stop date' in entry and 'Stop time' in entry:
            print(f"  Stop:  {entry['Stop date']} {entry['Stop time']}")
        print(f"  Duration: {entry['Duration']}")
        print(f"  Billable: {entry.get('Billable', '-')}")
        if entry.get('Tags') and entry['Tags'] != '-':
            print(f"  Tags: {entry['Tags']}")
    
    # Show some statistics
    print(f"\n{'='*80}")
    print(f"Statistics")
    print(f"{'='*80}")
    
    # Count unique projects
    projects = set(entry.get('Project', '') for entry in entries if entry.get('Project'))
    print(f"  Unique projects: {len(projects)}")
    
    # Count billable vs non-billable
    billable_count = sum(1 for e in entries if e.get('Billable', '').lower() == 'yes')
    print(f"  Billable entries: {billable_count}")
    print(f"  Non-billable entries: {len(entries) - billable_count}")
    
    # Calculate total duration
    total_seconds = sum(parse_toggl_duration(e['Duration']) for e in entries)
    total_hours = total_seconds / 3600
    print(f"  Total time tracked: {total_hours:.2f} hours")


def main():
    parser = argparse.ArgumentParser(
        description='Convert Toggl Track CSV to Clockify CSV format'
    )
    parser.add_argument(
        'input_file',
        nargs='?',
        default='data/toggl_input.csv',
        help='Input Toggl CSV file (default: data/toggl_input.csv)'
    )
    parser.add_argument(
        '-m', '--mode',
        choices=['clockify', 'print-only'],
        default='print-only',
        help='Operation mode: clockify (default, convert to Clockify CSV) or print-only (display data without conversion)'
    )
    parser.add_argument(
        '-o', '--output',
        default=None,
        help='Output CSV file (default: data/clockify_output.csv)'
    )
    parser.add_argument(
        '-p', '--projects',
        default='data/toggl_projects.json',
        help='Toggl projects JSON file for client mapping (default: data/toggl_projects.json)'
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
    
    print(f"Loading Toggl data from: {args.input_file}")
    entries = load_toggl_csv(args.input_file)
    
    # Load projects mapping if file exists
    project_to_client = None
    projects_path = Path(args.projects)
    if projects_path.exists():
        print(f"Loading projects mapping from: {args.projects}")
        project_to_client = load_projects_json(args.projects)
        print(f"Loaded {len(project_to_client)} project-to-client mappings")
    else:
        print(f"Projects file not found: {args.projects} (client names will be blank)")
    
    # Handle print-only mode
    if args.mode == 'print-only':
        print_examples(entries, args.num_examples, args.from_date, args.to_date)
        print(f"\n{'='*80}")
        print("Data loaded successfully!")
        print(f"{'='*80}\n")
        return 0
    
    # Handle clockify mode (default)
    if args.mode == 'clockify':
        # Set default output file if not specified
        output_file = args.output if args.output else 'data/clockify_output.csv'
        
        convert_to_clockify(entries, output_file, args.from_date, args.to_date, project_to_client)
        print(f"\n{'='*80}")
        print("Conversion completed successfully!")
        print(f"{'='*80}\n")
        return 0
    
    return 0


if __name__ == '__main__':
    exit(main())
