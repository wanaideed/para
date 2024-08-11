from flask import Flask, send_file, jsonify, request
import os
from datetime import datetime, timedelta
import time
import pandas as pd
import io
import shutil
from flask_cors import CORS
# Flask app setup
app = Flask(__name__)


# Enable CORS for all routes
CORS(app)

# Path to the file
file_path = 'MainWeight.txt'


# Function to get the last modification time of the file
def get_file_mod_time():
    return os.path.getmtime(file_path)


# Function to read data from the file
def read_file():
    with open(file_path, 'r') as file:
        return file.read()


@app.route('/poll', methods=['GET'])
def poll():
    start_time = time.time()
    timeout = 30  # Set timeout for the long polling

    # Get the initial modification time of the file
    last_mod_time = get_file_mod_time()

    while time.time() - start_time < timeout:
        current_mod_time = get_file_mod_time()

        if current_mod_time != last_mod_time:
            # File has changed, return the new data
            new_data = read_file()
            return jsonify({"data": new_data})

        time.sleep(1)  # Sleep to avoid busy-waiting

    # If no new data after timeout, return empty response or a default value
    return jsonify({"data": "No new data"}), 204


@app.route('/submit', methods=['POST'])
def submit_data():
    # Retrieve the form data
    merah = request.form.get('merah')
    kuning = request.form.get('kuning')
    hijau = request.form.get('hijau')
    buzzer = request.form.get('buzzer')

    # Save each value to its respective file
    save_to_file('merah.txt', merah)
    save_to_file('kuning.txt', kuning)
    save_to_file('hijau.txt', hijau)
    save_to_file('buzzer.txt', buzzer)

    # Return a status of OK
    return jsonify({"status": "OK"})


@app.route('/view-data', methods=['GET'])
def view_data():
    """Read and display the content of all the data files."""
    data = {
        "merah": read_fileTxt('merah.txt'),
        "kuning": read_fileTxt('kuning.txt'),
        "hijau": read_fileTxt('hijau.txt'),
        "buzzer": read_fileTxt('buzzer.txt')
    }

    # Return the data as JSON
    return jsonify({"status": "OK", "data": data})


def read_fileTxt(filename):
    """Read and return the content of the specified file."""
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return file.read()
    else:
        return None  # Return None if the file doesn't exist


def save_to_file(filename, value):
    """Save the given value to the specified file, creating the file if it doesn't exist."""
    # Check if the file exists
    if not os.path.exists(filename):
        # Create the file if it doesn't exist
        with open(filename, 'w') as file:
            pass  # This will create an empty file

    # Write the value to the file (overwrite any existing content)
    with open(filename, 'w') as file:
        file.write(value)


def read_csv_file(filename):
    """Read and return the content of the specified CSV file as a DataFrame."""
    if os.path.exists(filename):
        return pd.read_csv(filename)
    else:
        return pd.DataFrame(columns=['datetime', 'value'])  # Return empty DataFrame with expected columns

def filter_entries(df, start_time, end_time):
    """Filter entries based on the start and end time."""
    df['datetime'] = pd.to_datetime(df['datetime'])
    mask = (df['datetime'] >= start_time) & (df['datetime'] <= end_time)
    return df[mask]

def generate_date_range(start_date, end_date):
    """Generate a list of filenames from start_date to end_date, inclusive."""
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime('%d%m%Y') + '.csv')
        current_date += timedelta(days=1)
    return dates

@app.route('/search', methods=['POST'])
def search_data():
    # Retrieve the form data
    from_str = request.form.get('from')
    to_str = request.form.get('to')

    try:
        # Validate and parse the timestamps
        from_timestamp = datetime.strptime(from_str, '%Y-%m-%d %H:%M:%S')
        to_timestamp = datetime.strptime(to_str, '%Y-%m-%d %H:%M:%S')

        start_date = from_timestamp.date()
        end_date = to_timestamp.date()

        # Generate the list of filenames based on the date range
        filenames = generate_date_range(start_date, end_date)

        # Read and combine data from all relevant files
        combined_df = pd.DataFrame()
        for filename in filenames:
            df = read_csv_file(filename)
            combined_df = pd.concat([combined_df, df], ignore_index=True)

        # Filter data based on the date range
        filtered_df = filter_entries(combined_df, from_timestamp, to_timestamp)

        # Convert filtered DataFrame to JSON
        data = filtered_df.to_dict(orient='records')

        return jsonify({"status": "OK", "data": data})

    except ValueError as e:
        return jsonify({"error": f"Invalid date format: {e}"}), 400


@app.route('/export', methods=['POST'])
def export_data():
    USB_MOUNT_PATH = '/dev/sda1'
    """Generate a CSV file with data for the specified date range and copy it to a USB drive."""
    from_str = request.form.get('from')
    to_str = request.form.get('to')

    try:
        # Validate and parse the timestamps
        from_timestamp = datetime.strptime(from_str, '%Y-%m-%d %H:%M:%S')
        to_timestamp = datetime.strptime(to_str, '%Y-%m-%d %H:%M:%S')

        start_date = from_timestamp.date()
        end_date = to_timestamp.date()

        # Generate the list of filenames based on the date range
        filenames = generate_date_range(start_date, end_date)

        # Read and combine data from all relevant files
        combined_df = pd.DataFrame()
        for filename in filenames:
            df = read_csv_file(filename)
            combined_df = pd.concat([combined_df, df], ignore_index=True)

        # Filter data based on the date range
        filtered_df = filter_entries(combined_df, from_timestamp, to_timestamp)

        # Create a CSV in-memory buffer
        output = io.StringIO()
        filtered_df.to_csv(output, index=False)
        output.seek(0)

        # Generate the filename for the CSV file
        file_name = f"{from_timestamp.strftime('%Y%m%d_%H%M%S')}_{to_timestamp.strftime('%Y%m%d_%H%M%S')}.csv"
        local_file_path = os.path.join('/tmp', file_name)  # Temporary path to store the file

        # Save the CSV to a temporary file
        with open(local_file_path, 'w') as file:
            file.write(output.getvalue())

        # Copy the file to the USB drive
        usb_file_path = os.path.join(USB_MOUNT_PATH, file_name)
        shutil.copy(local_file_path, usb_file_path)

        # Optionally, clean up the temporary file
        os.remove(local_file_path)

        # Return status "OK" after successfully copying the file
        return jsonify({"status": "OK"})

    except ValueError as e:
        return jsonify({"error": f"Invalid date format: {e}"}), 400
    except FileNotFoundError as e:
        return jsonify({"error": f"File not found: {e}"}), 404
    except IOError as e:
        return jsonify({"error": f"File operation error: {e}"}), 500



@app.route('/download', methods=['GET'])
def download_file():
    filename = datetime.now().strftime("%d%m%Y") + ".csv"
    if os.path.exists(filename):
        return send_file(filename, as_attachment=True)
    else:
        return "File not found", 404


@app.route('/file/<name>', methods=['GET'])
def download_file_by_name(name):
    filename = name + ".csv"
    if os.path.exists(filename):
        return send_file(filename, as_attachment=True)
    else:
        return "File not found", 404


@app.route('/update_min/<value>')
def update_min(value):
    # Get the 'value' parameter from the query string
    new_value = value

    if new_value is None:
        return 'No value provided', 400

    # Ensure the new value is a string
    new_value_str = str(new_value)

    try:
        # Check if the file exists; if not, create it
        if not os.path.exists('min.txt'):
            with open('min.txt', 'w') as f:
                f.write('')

        # Open the file in write mode and replace all content with the new value
        with open('min.txt', 'w') as f:
            f.write(new_value_str)
        return f'Successfully updated min.txt with value: {new_value_str}', 200
    except Exception as e:
        return str(e), 500


if __name__ == '__main__':
    # Run the Flask app
    app.run(host='0.0.0.0',port=5000, debug=True)