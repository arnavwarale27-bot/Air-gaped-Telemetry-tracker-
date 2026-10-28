import csv
import ollama

MODEL = "phi3"


def load_sop(path="sop.txt"):
    with open(path) as f:
        return f.read()


def analyze(row, sop):
    prompt = f"""You are a NOC assistant. Use ONLY the SOP rules below. Do not invent steps.

SOP RULES:
{sop}

TELEMETRY:
Link: {row['link']}
Latency: {row['latency_ms']} ms
Packet loss: {row['packet_loss']} %
Jitter: {row['jitter_ms']} ms
Status: {row['status']}

Answer in exactly this format:
Matched rule: <rule number>
Root cause: <one line from the SOP>
Action: <one line from the SOP>
"""
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0},
    )
    return response["message"]["content"]


def main():
    sop = load_sop()
    with open("telemetry.csv") as f:
        for row in csv.DictReader(f):
            print("=" * 50)
            print(row["link"])
            print(analyze(row, sop))


if __name__ == "__main__":
    main()
