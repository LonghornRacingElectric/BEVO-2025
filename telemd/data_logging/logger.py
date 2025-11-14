import csv
import os
import time
import threading
from collections import deque, defaultdict
from datetime import datetime


class CSVTimeSeriesLogger:
    """CSV-based time-series logger with timestamp rows and field columns"""
    
    def __init__(self, base_filename="telemetry_history", buffer_size=333, flush_interval=1.0):
        self.base_filename = base_filename
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.buffer = deque(maxlen=buffer_size)
        self.lock = threading.Lock()
        self.last_flush_time = time.time()
        
        # Track all fields we've seen and their latest values
        self.all_fields = set()  # Set of all field names
        self.latest_values = {}  # field_name -> (value, timestamp, value_type)
        
        # Create logs directory if it doesn't exist
        self.logs_dir = "logs"
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Create timestamped filename for this session in logs folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename = os.path.join(self.logs_dir, f"{base_filename}_{timestamp}.csv")
        
        # Initialize CSV file with headers
        self._init_csv_file()
        
    def _init_csv_file(self):
        """Initialize CSV file with timestamp and field headers"""
        with open(self.filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Write header row: timestamp, datetime, then all field names
            header = ['timestamp', 'datetime']
            writer.writerow(header)
        print(f"Created new CSV log file for this session: {self.filename}")
    
    def log_value(self, field_name, value, timestamp=None):
        """Log a telemetry value with timestamp"""
        if timestamp is None:
            timestamp = time.time()
            
        # Determine value type and convert to string
        if isinstance(value, bool):
            value_type = 'bool'
            value_str = str(value)
        elif isinstance(value, (int, float)):
            value_type = 'numeric'
            value_str = str(value)
        elif isinstance(value, list):
            value_type = 'array'
            value_str = ','.join(map(str, value))
        else:
            value_type = 'string'
            value_str = str(value)
        
        # Update latest values and track new fields
        with self.lock:
            self.latest_values[field_name] = (value_str, timestamp, value_type)
            self.all_fields.add(field_name)
            
            # Add to buffer for periodic flushing
            self.buffer.append((timestamp, field_name, value_str))
        
        # Check if we should flush
        current_time = time.time()
        if (len(self.buffer) >= self.buffer_size or 
            current_time - self.last_flush_time >= self.flush_interval):
            self._flush_buffer()
    
    def _flush_buffer(self):
        """Flush buffered data to CSV file in time-series format"""
        with self.lock:
            if not self.buffer:
                return
            
            # Group data by timestamp
            timestamp_data = defaultdict(dict)
            for timestamp, field_name, value_str in self.buffer:
                timestamp_data[timestamp][field_name] = value_str
            
            # Read existing data to merge with new data
            existing_data = {}
            if os.path.exists(self.filename) and os.path.getsize(self.filename) > 0:
                with open(self.filename, 'r', newline='') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        ts = float(row['timestamp'])
                        existing_data[ts] = {k: v for k, v in row.items() if k not in ['timestamp', 'datetime']}
            
            # Merge new data with existing data
            for timestamp in timestamp_data:
                if timestamp in existing_data:
                    existing_data[timestamp].update(timestamp_data[timestamp])
                else:
                    existing_data[timestamp] = timestamp_data[timestamp]
            
            # Write all data back to file
            with open(self.filename, 'w', newline='') as csvfile:
                # Create header with all fields
                all_fields = sorted(list(self.all_fields))
                fieldnames = ['timestamp', 'datetime'] + all_fields
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                # Write all timestamps
                for timestamp in sorted(existing_data.keys()):
                    row = {
                        'timestamp': timestamp,
                        'datetime': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    }
                    # Add field values
                    for field in all_fields:
                        row[field] = existing_data[timestamp].get(field, '')
                    writer.writerow(row)
            
            # print(f"Flushed {len(self.buffer)} data points to {self.filename}")
            
            # Clear buffer and update flush time
            self.buffer.clear()
            self.last_flush_time = time.time()
    
    def get_latest_values(self):
        """Get the latest value for each field (from memory cache)"""
        with self.lock:
            return {
                field_name: {
                    'timestamp': timestamp,
                    'datetime': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    'value': value,
                    'value_type': value_type
                }
                for field_name, (value, timestamp, value_type) in self.latest_values.items()
            }
    
    def get_field_history(self, field_name, start_time=None, end_time=None, max_rows=10000):
        """Get historical data for a specific field"""
        if start_time is None:
            start_time = time.time() - 3600  # Last hour
        if end_time is None:
            end_time = time.time()
        
        data = []
        with open(self.filename, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                timestamp = float(row['timestamp'])
                if (start_time <= timestamp <= end_time and 
                    field_name in row and row[field_name]):
                    data.append({
                        'timestamp': timestamp,
                        'datetime': row['datetime'],
                        'value': row[field_name]
                    })
                    if len(data) >= max_rows:
                        break
        
        return data
    
    def get_time_range_data(self, start_time=None, end_time=None, max_rows=10000):
        """Get all data for a time range"""
        if start_time is None:
            start_time = time.time() - 3600  # Last hour
        if end_time is None:
            end_time = time.time()
        
        data = []
        with open(self.filename, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                timestamp = float(row['timestamp'])
                if start_time <= timestamp <= end_time:
                    data.append(row)
                    if len(data) >= max_rows:
                        break
        
        return data
    
    def get_statistics(self, field_name, hours=1):
        """Get basic statistics for a field over the last N hours"""
        end_time = time.time()
        start_time = end_time - (hours * 3600)
        
        values = []
        with open(self.filename, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if field_name in row and row[field_name]:
                    timestamp = float(row['timestamp'])
                    if start_time <= timestamp <= end_time:
                        try:
                            values.append(float(row[field_name]))
                        except ValueError:
                            continue
        
        if not values:
            return {'count': 0, 'avg': 0, 'min': 0, 'max': 0}
        
        return {
            'count': len(values),
            'avg': sum(values) / len(values),
            'min': min(values),
            'max': max(values)
        }
    
    def export_time_range(self, output_filename, start_time=None, end_time=None):
        """Export a time range to a new CSV file"""
        if start_time is None:
            start_time = time.time() - 3600  # Last hour
        if end_time is None:
            end_time = time.time()
        
        data = self.get_time_range_data(start_time, end_time, max_rows=1000000)
        
        with open(output_filename, 'w', newline='') as csvfile:
            if data:
                writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        
        print(f"Exported {len(data)} data points to {output_filename}")
    
    def get_filename(self):
        """Get the current log filename"""
        return self.filename
    
    def shutdown(self):
        """Clean shutdown - flush remaining data"""
        self._flush_buffer()
        print(f"CSVTimeSeriesLogger shutdown complete. Log file: {self.filename}")


class LatestValuesCache:
    """Keeps track of latest values for all telemetry fields"""
    
    def __init__(self):
        self.latest_values = {}  # field_name -> (value, timestamp)
        self.last_update_time = time.time()
        
    def update_value(self, field_name, value, index=None, size=None):
        """Update the latest value for a field, handling repeated fields."""
        if index is not None:
            # It's a repeated field, store it in a list
            if field_name not in self.latest_values or not isinstance(self.latest_values.get(field_name), tuple) or not isinstance(self.latest_values.get(field_name)[0], list):
                if size is not None:
                    self.latest_values[field_name] = ([None] * size, time.time())
                else:
                    # Fallback if size is not provided
                    self.latest_values[field_name] = ([], time.time())

            # Ensure we have a list to update
            current_list, _ = self.latest_values[field_name]
            if index < len(current_list):
                current_list[index] = value
                self.latest_values[field_name] = (current_list, time.time())
            else:
                print(f"Warning: index {index} out of bounds for {field_name}")
        else:
            # It's a single value field
            self.latest_values[field_name] = (value, time.time())
        
    def get_latest_values(self):
        """Get all latest values with timestamps"""
        return self.latest_values.copy()
        
    def get_field_value(self, field_name):
        """Get the latest value for a specific field"""
        if field_name in self.latest_values:
            return self.latest_values[field_name][0]
        return None
        
    def get_field_timestamp(self, field_name):
        """Get the timestamp for a specific field"""
        if field_name in self.latest_values:
            return self.latest_values[field_name][1]
        return None
        
    def print_summary(self):
        """Print a summary of all latest values"""
        print(f"\n=== Latest Telemetry Values ({len(self.latest_values)} fields) ===")
        for field_name, (value, timestamp) in sorted(self.latest_values.items()):
            age = time.time() - timestamp
            print(f"{field_name}: {value} (age: {age:.3f}s)")
        print("=" * 60) 