import ollama

# 1. The Fake Telemetry (Our Network Anomaly)
telemetry_data = """
Timestamp: 2026-06-28 10:15 AM
Interface: Mumbai-Hub to Branch-12 (MPLS)
Status: Latency climbed from 20ms to 180ms over the last 15 minutes. Packet loss at 4%.
"""

# 2. The Runbook (Our Internal NOC Rules)
runbook_context = """
SOP for Mumbai-Hub:
If latency exceeds 150ms and packet loss is detected, the primary cause is usually the background database replication job saturating the link.
Action Required: Throttle QoS Class 4 traffic and re-route background jobs to the secondary SD-WAN tunnel.
"""

# 3. The Copilot Prompt
prompt = f"""
You are an expert NOC Copilot. Analyze the network telemetry using ONLY the provided runbook. 

Runbook:
{runbook_context}

Telemetry Data:
{telemetry_data}

Output a short, structured response with:
1. Predicted Issue
2. Root Cause
3. Recommended Action
"""

print("Syntax Squad Copilot analyzing network offline...\n")
print("-" * 50)

# 4. Talk to the local Phi-3 model
response = ollama.chat(model='phi3', messages=[
    {'role': 'user', 'content': prompt}
])

print(response['message']['content'])
