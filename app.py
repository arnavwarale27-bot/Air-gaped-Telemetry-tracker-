import csv
from flask import (
    Flask, jsonify, send_file,
    request, redirect, url_for, session
)
from copilot import analyze, load_sop

app = Flask(__name__)
app.secret_key = "noc-copilot-offline-key"

# ── Credentials (offline / air-gapped — no DB needed) ──────────────
USERS = {"admin": "noc123"}


def logged_in():
    return session.get("user") is not None


# ── Login ───────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip() or "admin"
        session["user"] = username
        return redirect(url_for("home"))
    return send_file("noc_login.html")


# ── Logout ──────────────────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Dashboard ────────────────────────────────────────────────────────
@app.route("/")
def home():
    if not logged_in():
        return redirect(url_for("login"))
    return send_file("noc_dashboard.html")


# ── API ──────────────────────────────────────────────────────────────
@app.route("/analyze")
def run_analysis():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    results = []
    try:
        sop = load_sop()
        with open("telemetry.csv") as f:
            for row in csv.DictReader(f):
                results.append({"link": row["link"], "result": analyze(row, sop)})
    except Exception as e:
        return jsonify({"error": f"Failed reading telemetry or SOP: {str(e)}"}), 500
    return jsonify(results)


@app.route("/telemetry")
def get_telemetry():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401

    rows = []
    try:
        with open("telemetry.csv") as f:
            for r in csv.DictReader(f):
                rows.append({
                    "link": r["link"],
                    "latency_ms": r["latency_ms"],
                    "packet_loss": r["packet_loss"],
                    "jitter_ms": r["jitter_ms"],
                    "status": r["status"]
                })
        sat_data = {
            "satellite_id": "SATCOM-4B (NORAD #43921)",
            "orbit": "GEO (35,786 km / 74.0°E)",
            "downlink_freq": "11.742 GHz (Ku-Band)",
            "uplink_freq": "14.238 GHz",
            "rf_snr_db": 14.8,
            "bus_voltage_v": 34.2,
            "bus_current_a": 14.6,
            "battery_soc": 94.2,
            "payload_temp_c": 21.4,
            "adcs_state": "NOMINAL_POINTING",
            "frame_lock": True
        }
        return jsonify({"status": "ok", "telemetry": rows, "satellite": sat_data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/chat", methods=["POST"])
def chat():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401

    import ollama
    data = request.get_json(silent=True) or {}
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"reply": "Please enter a question or instruction."})

    # Read current telemetry and SOP for full local context
    telemetry_rows = []
    try:
        with open("telemetry.csv") as f:
            for row in csv.DictReader(f):
                telemetry_rows.append(
                    f"- {row['link']}: Latency={row['latency_ms']}ms, Loss={row['packet_loss']}%, Jitter={row['jitter_ms']}ms, Status={row['status']}"
                )
    except Exception as e:
        telemetry_rows.append(f"Error loading telemetry: {e}")

    try:
        with open("sop.txt") as f:
            sop_text = f.read().strip()
    except Exception as e:
        sop_text = f"Error loading SOP: {e}"

    system_prompt = f"""You are the offline AI NOC Copilot assistant for a network operations center.
You run 100% locally on this air-gapped machine using Phi-3 via Ollama.
Analyze telemetry and SOP rules directly to help the NOC engineer.
Be concise, technical, precise, and actionable.

CURRENT NETWORK TELEMETRY:
{chr(10).join(telemetry_rows)}

SOP RULES:
{sop_text}"""

    try:
        response = ollama.chat(
            model="phi3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ],
            options={"temperature": 0.2}
        )
        reply = response["message"]["content"].strip()
        return jsonify({"reply": reply})
    except Exception as err:
        return jsonify({"error": f"Local LLM error: {str(err)}. Ensure Ollama is running."}), 500


if __name__ == "__main__":
    app.run(port=5001)

