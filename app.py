import csv
from flask import Flask, jsonify, send_file
from copilot import analyze, load_sop

app = Flask(__name__)


@app.route("/")
def home():
    return send_file("noc_dashboard.html")


@app.route("/analyze")
def run_analysis():
    sop = load_sop()
    results = []
    with open("telemetry.csv") as f:
        for row in csv.DictReader(f):
            results.append({"link": row["link"], "result": analyze(row, sop)})
    return jsonify(results)


if __name__ == "__main__":
    app.run(port=5001)
