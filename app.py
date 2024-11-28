from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from flask import Flask, jsonify
import psycopg2

app = Flask(__name__)

# Initialize OpenTelemetry
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Configure Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Instrument Flask
FlaskInstrumentor().instrument_app(app)

# PostgreSQL connection details
DB_HOST = "localhost"
DB_NAME = "pgdb"
DB_USER = "leesa"
DB_PASS = "1234"

@app.route("/data")
def get_data():
    with tracer.start_as_current_span("get_data_span"):
        try:
            # Connect to the PostgreSQL database
            conn = psycopg2.connect(
                host=DB_HOST,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
            cur = conn.cursor()
            cur.execute("SELECT * FROM item")
            rows = cur.fetchall()
            cur.close()
            conn.close()

            # Return the result as JSON
            return jsonify(rows)
        except Exception as e:
            return str(e), 500

if __name__ == "__main__":
    app.run(port=5000)
