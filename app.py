from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import psycopg2
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource

# Initialize Flask application
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize OpenTelemetry with service name
resource = Resource(attributes={"service.name": "my-flask-app"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

# Configure Jaeger exporter (use localhost if Jaeger is running locally)
jaeger_exporter = JaegerExporter(agent_host_name="localhost", agent_port=6831)  # Update the host if needed
span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Instrument Flask for OpenTelemetry tracing
FlaskInstrumentor().instrument_app(app)

# PostgreSQL connection details
DB_HOST = "localhost"
DB_NAME = "pgdb"
DB_USER = "leesa"
DB_PASS = "1234"

# Serve the HTML frontend with Flask
@app.route('/')
def index():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Items List</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                padding: 20px;
            }

            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }

            table, th, td {
                border: 1px solid #ddd;
            }

            th, td {
                padding: 8px;
                text-align: left;
            }

            h1 {
                color: #4CAF50;
            }

            .error {
                color: red;
            }
        </style>
    </head>
    <body>

        <h1>Items List</h1>
        <table id="items-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Quantity</th>
                    <th>Price</th>
                </tr>
            </thead>
            <tbody>
                <!-- Data will be inserted here -->
            </tbody>
        </table>

        <p id="error-message" class="error" style="display: none;">Failed to load data. Please try again later.</p>

        <script>
            // Fetch data from the Flask API
            function fetchData() {
                fetch('/data')  // Flask API endpoint
                    .then(response => response.json())  // Parse JSON response
                    .then(data => {
                        const tableBody = document.querySelector('#items-table tbody');
                        tableBody.innerHTML = '';  // Clear previous data

                        // Insert each item into the table
                        data.forEach(item => {
                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td>${item.id}</td>
                                <td>${item.name}</td>
                                <td>${item.quantity}</td>
                                <td>${item.price}</td>
                            `;
                            tableBody.appendChild(row);
                        });
                    })
                    .catch(error => {
                        document.getElementById('error-message').style.display = 'block';
                        console.error('Error fetching data:', error);
                    });
            }

            // Call fetchData when the page loads
            window.onload = fetchData;
        </script>

    </body>
    </html>
    """
    return render_template_string(html_content)


# Route to get data from PostgreSQL database
@app.route("/data")
def get_data():
    with tracer.start_as_current_span("get_data_span"):
        try:
            # Connect to PostgreSQL
            conn = psycopg2.connect(
                host=DB_HOST,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
            cur = conn.cursor()
            cur.execute("SELECT * FROM item")  # Assuming you have an 'item' table
            rows = cur.fetchall()

            # Format the rows into JSON response
            formatted_rows = [
                {"id": row[0], "name": row[1], "quantity": row[2], "price": float(row[3])}
                for row in rows
            ]
            cur.close()
            conn.close()
            return jsonify(formatted_rows)
        except Exception as e:
            return str(e), 500


if __name__ == "__main__":
    app.run(port=5000)
