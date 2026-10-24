import csv
import ollama

MODEL = "phi3"


def load_sop(path="sop.txt"):
    with open(path) as f:
        blocks = f.read().strip().split("\n\n")
    return {int(b.split(":")[0].replace("Rule", "").strip()): b for b in blocks}


def match_rule(row):
    lat = float(row["latency_ms"])
    loss = float(row["packet_loss"])
    jit = float(row["jitter_ms"])
    status = row["status"].strip().lower()

    if status == "down":
        return 4
    if loss > 10:
        return 2
    if lat > 150 and loss > 2:
        return 1
    if jit > 30:
        return 3
    if lat < 100 and loss < 1:
        return 5
    return None


def analyze(row, sop):
    rule_no = match_rule(row)
    if rule_no is None or rule_no not in sop:
        return "Matched rule: none\nAction: no SOP rule fits this reading, escalate to a senior engineer."

    prompt = f"""You are a NOC assistant. Using ONLY the rule below, explain the incident in two short lines. Do not mention any other rule or add extra steps.

RULE:
{sop[rule_no]}

TELEMETRY:
Link: {row['link']}
Latency: {row['latency_ms']} ms
Packet loss: {row['packet_loss']} %
Jitter: {row['jitter_ms']} ms
Status: {row['status']}

Answer in exactly this format:
Root cause: <one line>
Action: <one line>
"""
    try:
        response = ollama.chat(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0},
        )
        return f"Matched rule: Rule {rule_no}\n" + response["message"]["content"].strip()
    except Exception:
        sop_lines = sop[rule_no].split("\n")
        cause = next((l.replace("Cause:", "").strip() for l in sop_lines if l.startswith("Cause:")), "Anomaly matching SOP threshold")
        action = next((l.replace("Action:", "").strip() for l in sop_lines if l.startswith("Action:")), "Execute SOP remediation protocol")
        return f"Matched rule: Rule {rule_no}\nRoot cause: {cause}\nAction: {action}"


def main():
    sop = load_sop()
    with open("telemetry.csv") as f:
        for row in csv.DictReader(f):
            print("=" * 50)
            print(row["link"])
            print(analyze(row, sop))


if __name__ == "__main__":
    main()
