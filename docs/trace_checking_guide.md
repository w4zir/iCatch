# Agent Trace Checking Guide

This guide explains how to check and view traces of agent calls in the Sentinel-MAS fraud detection system.

## Overview

Agent traces contain the complete reasoning and outputs from all three agents:
- **Identity Agent**: IP and device risk analysis
- **Behavioral Agent**: Transaction pattern analysis  
- **Scoring Agent**: Final fraud score and decision

## Methods to Check Traces

### 1. From API Response

When you call the `/analyze-single` endpoint, the response includes a complete trace:

```python
import httpx
from schemas import AgentTrace, IdentityAgentOutput, BehavioralAgentOutput, ScoringAgentOutput

response = httpx.post(
    "http://localhost:8000/analyze-single",
    json=transaction_data
)
result = response.json()

# Access trace
trace_dict = result["trace"]
print(f"Fraud Score: {trace_dict['scoring_agent']['fraud_score']}")
print(f"Decision: {trace_dict['scoring_agent']['decision']}")
print(f"Reasoning: {trace_dict['scoring_agent']['reasoning']}")
```

### 2. Using Trace Utilities

The `trace_utils.py` module provides several utilities for viewing traces:

#### Pretty Print to Console

```python
from agents import analyze_transaction
from trace_utils import print_trace
from schemas import Transaction

transaction = Transaction(...)
trace = await analyze_transaction(transaction)

# Print detailed trace
print_trace(trace, transaction_id=transaction.user_id, detailed=True)

# Print summary (scores only)
print_trace(trace, transaction_id=transaction.user_id, detailed=False)
```

#### Save Trace to File

```python
from trace_utils import save_trace_to_file

save_trace_to_file(trace, "my_trace.json", transaction_id="user_123")
```

#### Log Multiple Traces

```python
from trace_utils import log_trace

# Log to file (append mode)
log_trace(
    trace,
    transaction_id="user_123",
    log_file="traces.log",
    console=True  # Also print to console
)
```

#### Compare Two Traces

```python
from trace_utils import compare_traces

trace1 = await analyze_transaction(transaction1)
trace2 = await analyze_transaction(transaction2)

compare_traces(trace1, trace2, label1="Normal", label2="Suspicious")
```

#### Get Summary (Scores Only)

```python
from trace_utils import get_trace_summary

summary = get_trace_summary(trace)
print(summary)
# {
#   "identity": {"ip_risk_score": 0.3, "device_risk_score": 0.2},
#   "behavioral": {"frequency_anomaly_score": 0.1, "amount_deviation_score": 0.4},
#   "scoring": {"fraud_score": 0.25, "decision": "approve"}
# }
```

### 3. Enable Automatic Trace Logging

You can enable automatic trace logging for all transactions by setting environment variables:

```bash
# Enable trace logging
export ENABLE_TRACE_LOGGING=true

# Log to file (optional)
export TRACE_LOG_FILE=agent_traces.log

# Print to console (optional)
export TRACE_LOG_CONSOLE=true
```

Or create a `.env` file:

```env
ENABLE_TRACE_LOGGING=true
TRACE_LOG_FILE=agent_traces.log
TRACE_LOG_CONSOLE=false
```

When enabled, all traces will be automatically logged when `analyze_transaction()` is called.

### 4. From Streamlit UI

The Streamlit frontend (`app.py`) displays traces in tabs:
- Navigate to "Single Transaction Analysis"
- Submit a transaction
- View the trace in the "Agent Trace" section with three tabs:
  - Identity Agent
  - Behavioral Agent
  - Scoring Agent

### 5. Direct Access in Code

If you're calling `analyze_transaction()` directly:

```python
from agents import analyze_transaction
from schemas import Transaction

transaction = Transaction(...)
trace = await analyze_transaction(transaction)

# Access individual agent outputs
print(f"IP Risk: {trace.identity_agent.ip_risk_score}")
print(f"Fraud Score: {trace.scoring_agent.fraud_score}")
print(f"Decision: {trace.scoring_agent.decision}")
print(f"Reasoning: {trace.scoring_agent.reasoning}")
```

## Trace Structure

A trace contains three agent outputs:

```python
AgentTrace(
    identity_agent=IdentityAgentOutput(
        ip_risk_score=0.3,          # 0.0 (safe) to 1.0 (high risk)
        device_risk_score=0.2,        # 0.0 (safe) to 1.0 (high risk)
        reasoning="..."               # Explanation
    ),
    behavioral_agent=BehavioralAgentOutput(
        frequency_anomaly_score=0.1,  # 0.0 (normal) to 1.0 (highly anomalous)
        amount_deviation_score=0.4,    # 0.0 (normal) to 1.0 (highly deviant)
        reasoning="..."               # Explanation
    ),
    scoring_agent=ScoringAgentOutput(
        fraud_score=0.25,             # 0.0 (safe) to 1.0 (fraudulent)
        decision="approve",           # "approve" or "deny"
        reasoning="..."               # Comprehensive explanation
    )
)
```

## Example Script

Run the example script to see all methods in action:

```bash
python example_check_traces.py
```

This script demonstrates:
1. Single trace viewing
2. Trace comparison
3. Batch trace logging
4. Trace from API response

## Performance Notes

- Trace logging adds minimal overhead (just JSON serialization)
- Console printing can slow down batch processing
- For production, use file logging with `console=False`
- Traces are automatically included in API responses (no extra cost)

## Troubleshooting

**Q: Traces are not being logged**
- Check that `ENABLE_TRACE_LOGGING=true` is set
- Verify `trace_utils.py` is in the same directory
- Check file permissions for log file location

**Q: How to view traces from batch processing?**
- Batch API responses don't include full traces (for performance)
- Use single transaction endpoint for detailed traces
- Or enable trace logging to capture all traces automatically

**Q: Can I filter or search traces?**
- Traces are saved as JSON, so you can use `jq` or Python to filter:
  ```bash
  # Find all denied transactions
  cat agent_traces.log | jq 'select(.trace.scoring_agent.decision == "deny")'
  ```

