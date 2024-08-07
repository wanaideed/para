from flask import Flask, send_file
import os
from datetime import datetime

# Flask app setup
app = Flask(__name__)


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