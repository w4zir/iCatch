# How Sentinel-MAS Works: Step-by-Step Guide

This document explains how the Sentinel-MAS (Multi-Agent Fraud Detection) system works from start to end, including code snippets and API endpoints.

## System Overview

Sentinel-MAS is a high-speed fraud detection system that uses three specialized AI agents working in parallel to analyze transactions. The system architecture consists of:

1. **Frontend**: Streamlit web interface (`app.py`)
2. **Backend API**: FastAPI server (`main.py`)
3. **Agent Orchestration**: LangGraph workflow (`agents.py`)
4. **LLM Inference**: Groq API (Llama 3.1 8B)

---

## Step 1: System Initialization

### 1.1 Configuration Loading

The system starts by loading configuration from environment variables:

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")
TIMEOUT_SECONDS = float(os.getenv("TIMEOUT_SECONDS", "3.0"))
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "1000"))
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
```

### 1.2 FastAPI Server Startup

The backend server initializes with CORS middleware enabled:

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Sentinel-MAS Fraud Detection API",
    description="Multi-Agent Fraud Detection System using LangGraph and Groq",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Start Command:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 1.3 Streamlit Frontend Startup

The frontend initializes and checks API connectivity:

```python
# app.py
import streamlit as st
import httpx

def check_api_health() -> bool:
    """Check if API is available."""
    try:
        response = httpx.get(f"{API_URL}/", timeout=2.0)
        return response.status_code == 200
    except:
        return False
```

**Start Command:**
```bash
streamlit run app.py
```

---

## Step 2: User Interaction - Single Transaction Analysis

### 2.1 User Inputs Transaction Data

The user can either:
- Manually enter transaction details
- Load a random transaction from the IEEE Fraud Detection dataset

```python
# app.py - Transaction form
with st.form("transaction_form"):
    user_id = st.text_input("User ID")
    transaction_amount = st.number_input("Transaction Amount")
    ip_address = st.text_input("IP Address")
    device_id = st.text_input("Device ID")
    timestamp = st.text_input("Timestamp")
    
    submitted = st.form_submit_button("🔍 Analyze Transaction")
```

### 2.2 Frontend Sends Request to API

When the user submits the form, the frontend sends a POST request to the `/analyze-single` endpoint:

```python
# app.py
transaction_data = {
    "user_id": user_id,
    "transaction_amount": transaction_amount,
    "ip_address": ip_address,
    "device_id": device_id,
    "timestamp": timestamp,
}

response = httpx.post(
    f"{API_URL}/analyze-single",
    json=transaction_data,
    timeout=10.0
)
result = response.json()
```

---

## Step 3: API Endpoint - Single Transaction Analysis

### 3.1 Endpoint Definition

**Endpoint:** `POST /analyze-single`

**Request Body:**
```json
{
  "user_id": "user_123",
  "transaction_amount": 99.99,
  "ip_address": "192.168.1.1",
  "device_id": "device_456",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Response:**
```json
{
  "transaction": { ... },
  "trace": {
    "identity_agent": { ... },
    "behavioral_agent": { ... },
    "scoring_agent": { ... }
  },
  "latency_ms": 1234.56
}
```

### 3.2 Endpoint Implementation

```python
# main.py
@app.post("/analyze-single", response_model=SingleAnalysisResponse)
async def analyze_single(transaction: Transaction):
    """Analyze a single transaction with full agent reasoning trace."""
    start_time = time.time()
    
    try:
        trace = await analyze_transaction(transaction)
        latency_ms = (time.time() - start_time) * 1000
        
        return SingleAnalysisResponse(
            transaction=transaction,
            trace=trace,
            latency_ms=latency_ms
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
```

The endpoint:
1. Validates the transaction using Pydantic (`Transaction` schema)
2. Calls `analyze_transaction()` from `agents.py`
3. Measures latency
4. Returns the complete trace with all agent outputs

---

## Step 4: Agent Orchestration - LangGraph Workflow

### 4.1 Transaction Analysis Entry Point

```python
# agents.py
async def analyze_transaction(transaction: Transaction) -> AgentTrace:
    """Analyze a single transaction through the fraud detection pipeline."""
    graph = create_fraud_detection_graph()
    
    initial_state: AgentState = {
        "transaction": transaction,
        "transaction_data": {},
        "identity_output": None,
        "behavioral_output": None,
        "scoring_output": None,
        "error": None,
    }
    
    final_state = await asyncio.wait_for(
        graph.ainvoke(initial_state),
        timeout=config.TIMEOUT_SECONDS
    )
    
    return AgentTrace(
        identity_agent=final_state["identity_output"],
        behavioral_agent=final_state["behavioral_output"],
        scoring_agent=final_state["scoring_output"]
    )
```

### 4.2 LangGraph Workflow Definition

The workflow is defined as a state machine with three nodes:

```python
# agents.py
def create_fraud_detection_graph():
    """Create and configure the LangGraph state machine."""
    workflow = StateGraph(AgentState)
    
    # Entry node: Prepare transaction data
    def entry_node(state: AgentState) -> AgentState:
        transaction = state["transaction"]
        transaction_data = {
            "user_id": transaction.user_id,
            "transaction_amount": transaction.transaction_amount,
            "ip_address": transaction.ip_address,
            "device_id": transaction.device_id,
            "timestamp": transaction.timestamp,
            "payment_method": transaction.payment_method,
            "billing_address": transaction.billing_address,
            "shipping_address": transaction.shipping_address,
            "product_category": transaction.product_category,
        }
        return {**state, "transaction_data": transaction_data}
    
    # Add nodes
    workflow.add_node("entry", entry_node)
    workflow.add_node("parallel_agents", parallel_agents_node)
    workflow.add_node("scoring", scoring_agent_node)
    
    # Define edges
    workflow.set_entry_point("entry")
    workflow.add_edge("entry", "parallel_agents")
    workflow.add_edge("parallel_agents", "scoring")
    workflow.add_edge("scoring", END)
    
    return workflow.compile()
```

**Workflow Flow:**
```
Entry → Parallel Agents → Scoring Agent → END
```

---

## Step 5: Parallel Agent Execution

### 5.1 Parallel Execution Node

The Identity and Behavioral agents run **simultaneously** for optimal performance:

```python
# agents.py
async def parallel_agents_node(state: AgentState) -> AgentState:
    """Execute Identity and Behavioral agents in parallel."""
    identity_task = identity_agent_node(state)
    behavioral_task = behavioral_agent_node(state)
    
    identity_state, behavioral_state = await asyncio.gather(
        identity_task,
        behavioral_task,
        return_exceptions=True
    )
    
    # Merge results
    merged_state = {**state}
    merged_state["identity_output"] = identity_state.get("identity_output")
    merged_state["behavioral_output"] = behavioral_state.get("behavioral_output")
    
    return merged_state
```

### 5.2 Identity Agent

The Identity Agent analyzes IP and Device risk:

```python
# agents.py
async def identity_agent_node(state: AgentState) -> AgentState:
    """Identity Agent: Analyzes IP and Device risk."""
    transaction_data = state.get("transaction_data", {})
    
    system_prompt = "You are a fraud detection agent specializing in identity verification."
    
    prompt = f"""Analyze the following transaction for identity-based fraud indicators:

User ID: {transaction_data['user_id']}
IP Address: {transaction_data['ip_address']}
Device ID: {transaction_data['device_id']}
Timestamp: {transaction_data['timestamp']}

Assess the risk based on:
1. IP address patterns (VPN, proxy, suspicious geolocation)
2. Device ID consistency with user history
3. Unusual device or IP combinations

Return a JSON object with:
- ip_risk_score: float between 0.0 (safe) and 1.0 (high risk)
- device_risk_score: float between 0.0 (safe) and 1.0 (high risk)
- reasoning: brief explanation of your assessment"""
    
    output = await call_groq_structured(prompt, IdentityAgentOutput, system_prompt)
    return {**state, "identity_output": output}
```

**Output Schema:**
```python
# schemas.py
class IdentityAgentOutput(BaseModel):
    ip_risk_score: float = Field(..., ge=0.0, le=1.0)
    device_risk_score: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
```

### 5.3 Behavioral Agent

The Behavioral Agent analyzes transaction patterns:

```python
# agents.py
async def behavioral_agent_node(state: AgentState) -> AgentState:
    """Behavioral Agent: Analyzes transaction frequency and amount deviations."""
    transaction_data = state.get("transaction_data", {})
    
    system_prompt = "You are a fraud detection agent specializing in behavioral pattern analysis."
    
    prompt = f"""Analyze the following transaction for behavioral fraud indicators:

User ID: {transaction_data['user_id']}
Transaction Amount: {transaction_data['transaction_amount']}
Timestamp: {transaction_data['timestamp']}
Payment Method: {transaction_data.get('payment_method', 'N/A')}

Assess the risk based on:
1. Transaction frequency anomalies (too many transactions in short time)
2. Amount deviations from normal user patterns
3. Unusual transaction timing

Return a JSON object with:
- frequency_anomaly_score: float between 0.0 (normal) and 1.0 (highly anomalous)
- amount_deviation_score: float between 0.0 (normal) and 1.0 (highly deviant)
- reasoning: brief explanation of your assessment"""
    
    output = await call_groq_structured(prompt, BehavioralAgentOutput, system_prompt)
    return {**state, "behavioral_output": output}
```

**Output Schema:**
```python
# schemas.py
class BehavioralAgentOutput(BaseModel):
    frequency_anomaly_score: float = Field(..., ge=0.0, le=1.0)
    amount_deviation_score: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
```

---

## Step 6: LLM Inference - Groq API Calls

### 6.1 Structured Output Function

Both agents use the same function to call Groq with structured JSON output:

```python
# agents.py
async def call_groq_structured(
    prompt: str,
    output_schema: type[BaseModel],
    system_prompt: str = "",
) -> BaseModel:
    """Call Groq API with structured JSON output."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    # Get JSON schema from Pydantic model
    json_schema = output_schema.model_json_schema()
    
    # Create prompt that enforces JSON output
    json_prompt = f"""{prompt}

You must respond with ONLY valid JSON matching this schema:
{json.dumps(json_schema, indent=2)}

Do not include any explanatory text, markdown formatting, or code blocks. Return only the JSON object."""
    
    messages[-1]["content"] = json_prompt
    
    # Call Groq API
    response = groq_client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=messages,
        temperature=0.1,  # Low temperature for consistent structured output
        response_format={"type": "json_object"},
    )
    
    content = response.choices[0].message.content.strip()
    
    # Remove markdown code blocks if present
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    
    # Parse and validate
    data = json.loads(content)
    return output_schema(**data)
```

**Key Features:**
- Uses Pydantic schema validation
- Enforces JSON-only output
- Handles markdown code block removal
- Low temperature (0.1) for consistency

---

## Step 7: Scoring Agent - Final Decision

### 7.1 Scoring Agent Node

After both agents complete, the Scoring Agent aggregates their results:

```python
# agents.py
async def scoring_agent_node(state: AgentState) -> AgentState:
    """Scoring Agent: Aggregates results and produces final fraud score."""
    identity_output = state.get("identity_output")
    behavioral_output = state.get("behavioral_output")
    
    system_prompt = "You are a fraud detection scoring agent that makes final decisions."
    
    prompt = f"""Based on the following agent analyses, determine the final fraud risk:

IDENTITY AGENT ANALYSIS:
- IP Risk Score: {identity_output.ip_risk_score}
- Device Risk Score: {identity_output.device_risk_score}
- Reasoning: {identity_output.reasoning}

BEHAVIORAL AGENT ANALYSIS:
- Frequency Anomaly Score: {behavioral_output.frequency_anomaly_score}
- Amount Deviation Score: {behavioral_output.amount_deviation_score}
- Reasoning: {behavioral_output.reasoning}

Calculate a final fraud_score (0.0 to 1.0) that combines these factors.
Then make a decision:
- If fraud_score >= 0.5: decision = "deny"
- If fraud_score < 0.5: decision = "approve"

Return a JSON object with:
- fraud_score: float between 0.0 (safe) and 1.0 (fraudulent)
- decision: string "approve" or "deny"
- reasoning: comprehensive explanation of your decision"""
    
    output = await call_groq_structured(prompt, ScoringAgentOutput, system_prompt)
    return {**state, "scoring_output": output}
```

**Output Schema:**
```python
# schemas.py
class ScoringAgentOutput(BaseModel):
    fraud_score: float = Field(..., ge=0.0, le=1.0)
    decision: str = Field(..., pattern="^(approve|deny)$")
    reasoning: str
```

---

## Step 8: Response Assembly and Return

### 8.1 Trace Assembly

The complete trace is assembled from all agent outputs:

```python
# agents.py
return AgentTrace(
    identity_agent=final_state["identity_output"],
    behavioral_agent=final_state["behavioral_output"],
    scoring_agent=final_state["scoring_output"]
)
```

### 8.2 API Response

The API returns the complete response:

```python
# main.py
return SingleAnalysisResponse(
    transaction=transaction,
    trace=trace,
    latency_ms=latency_ms
)
```

### 8.3 Frontend Display

The frontend displays the results:

```python
# app.py
trace = result["trace"]
scoring = trace["scoring_agent"]

fraud_score = scoring["fraud_score"]
decision = scoring["decision"]

if decision == "deny":
    st.error(f"❌ DENIED (Fraud Score: {fraud_score:.2f})")
else:
    st.success(f"✅ APPROVED (Fraud Score: {fraud_score:.2f})")

# Display agent traces in tabs
tab1, tab2, tab3 = st.tabs(["Identity Agent", "Behavioral Agent", "Scoring Agent"])
```

---

## Step 9: Batch Processing Flow

### 9.1 Batch Endpoint

**Endpoint:** `POST /analyze-batch`

**Request Body:**
```json
[
  {
    "user_id": "user_123",
    "transaction_amount": 99.99,
    "ip_address": "192.168.1.1",
    "device_id": "device_456",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  {
    "user_id": "user_456",
    "transaction_amount": 199.99,
    ...
  }
]
```

**Response:**
```json
{
  "total_processed": 100,
  "fraud_detected": 5,
  "approved": 95,
  "denied": 5,
  "errors": 0,
  "latency_stats": {
    "p50_ms": 1200.0,
    "p95_ms": 2400.0,
    "avg_ms": 1350.0
  },
  "results": [ ... ]
}
```

### 9.2 Concurrent Processing

```python
# main.py
@app.post("/analyze-batch", response_model=BatchAnalysisResponse)
async def analyze_batch(transactions: List[Transaction]):
    """Analyze multiple transactions concurrently."""
    if len(transactions) > config.MAX_CONCURRENT_REQUESTS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {config.MAX_CONCURRENT_REQUESTS} transactions allowed per batch"
        )
    
    # Process transactions concurrently
    async def process_single(txn: Transaction, idx: int) -> BatchAnalysisResult:
        start_time = time.time()
        try:
            trace = await analyze_transaction(txn)
            latency_ms = (time.time() - start_time) * 1000
            
            return BatchAnalysisResult(
                transaction_id=str(idx),
                fraud_score=trace.scoring_agent.fraud_score,
                decision=trace.scoring_agent.decision,
                latency_ms=latency_ms,
                error=None
            )
        except Exception as e:
            return BatchAnalysisResult(
                transaction_id=str(idx),
                fraud_score=0.0,
                decision="error",
                latency_ms=latency_ms,
                error=str(e)
            )
    
    # Create tasks for all transactions
    tasks = [process_single(txn, idx) for idx, txn in enumerate(transactions)]
    
    # Process with asyncio.as_completed
    completed_tasks = []
    for coro in asyncio.as_completed(tasks):
        result = await coro
        completed_tasks.append(result)
    
    # Calculate statistics
    # ... (latency percentiles, fraud counts, etc.)
```

**Key Features:**
- Concurrent processing using `asyncio.as_completed()`
- Individual error handling per transaction
- Aggregate statistics (P50, P95, average latency)
- Results only included for batches ≤ 100 transactions

---

## Step 10: Dataset Integration

### 10.1 IEEE Fraud Detection Dataset Loading

The system can load and use the IEEE Fraud Detection dataset:

```python
# utils.py
def load_ieee_fraud_detection(
    transaction_path: Optional[str] = None,
    identity_path: Optional[str] = None
) -> pd.DataFrame:
    """Load IEEE Fraud Detection dataset by merging transaction and identity files."""
    trans_path = config.resolve_data_path(transaction_path or default_transaction)
    ident_path = config.resolve_data_path(identity_path or default_identity)
    
    df_trans = pd.read_csv(trans_path)
    df_identity = pd.read_csv(ident_path)
    
    # Merge on TransactionID
    df = df_trans.merge(df_identity, on="TransactionID", how="left")
    return df
```

### 10.2 Format Conversion

IEEE dataset format is converted to the Transaction schema:

```python
# utils.py
def map_ieee_to_transaction(row: pd.Series) -> Dict[str, Any]:
    """Map IEEE fraud detection dataset row to Transaction schema."""
    # Convert TransactionDT (days since epoch) to ISO timestamp
    base_date = datetime(2017, 12, 1)
    transaction_dt = float(row["TransactionDT"])
    transaction_date = base_date + timedelta(days=int(transaction_dt))
    timestamp = transaction_date.isoformat() + "Z"
    
    # Derive IP address from addr1/addr2
    addr1 = row.get("addr1")
    addr2 = row.get("addr2")
    ip_octet3 = int(float(addr1)) % 256 if pd.notna(addr1) else 0
    ip_octet4 = int(float(addr2)) % 256 if pd.notna(addr2) else 0
    ip_address = f"192.168.{ip_octet3}.{ip_octet4}"
    
    # Device ID from DeviceInfo or DeviceType
    device_id = str(row.get("DeviceInfo", "unknown"))
    
    return {
        "user_id": str(row.get("TransactionID", "unknown")),
        "transaction_amount": float(row.get("TransactionAmt", 0.0)),
        "ip_address": ip_address,
        "device_id": device_id,
        "timestamp": timestamp,
        "payment_method": str(row.get("card4", "")),
        "product_category": str(row.get("ProductCD", "")),
    }
```

---

## Complete Flow Diagram

```
┌─────────────────┐
│  User (Browser) │
└────────┬────────┘
         │
         │ 1. Submit Transaction
         ▼
┌─────────────────┐
│ Streamlit UI    │
│   (app.py)      │
└────────┬────────┘
         │
         │ 2. POST /analyze-single
         ▼
┌─────────────────┐
│  FastAPI Server │
│   (main.py)     │
└────────┬────────┘
         │
         │ 3. analyze_transaction()
         ▼
┌─────────────────┐
│  LangGraph      │
│  Workflow       │
└────────┬────────┘
         │
         │ 4. Entry Node
         ▼
┌─────────────────┐
│ Prepare Data    │
└────────┬────────┘
         │
         │ 5. Parallel Execution
         ▼
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────────┐
│Identity│ │ Behavioral   │
│ Agent  │ │ Agent        │
└───┬────┘ └──────┬───────┘
    │             │
    │ 6. Groq API │
    │             │
    └─────┬───────┘
          │
          │ 7. Merge Results
          ▼
    ┌─────────────┐
    │ Scoring     │
    │ Agent       │
    └──────┬──────┘
           │
           │ 8. Groq API
           │
           ▼
    ┌─────────────┐
    │ Final State │
    └──────┬──────┘
           │
           │ 9. Return Trace
           ▼
    ┌─────────────┐
    │ API Response│
    └──────┬──────┘
           │
           │ 10. Display Results
           ▼
    ┌─────────────┐
    │ Streamlit UI│
    └─────────────┘
```

---

## API Endpoints Summary

### Health Check
- **GET** `/`
- **Response:** `{"status": "ok", "service": "Sentinel-MAS Fraud Detection API"}`

### Single Transaction Analysis
- **POST** `/analyze-single`
- **Request Body:** `Transaction` schema
- **Response:** `SingleAnalysisResponse` with full trace
- **Timeout:** 3 seconds per transaction

### Batch Transaction Analysis
- **POST** `/analyze-batch`
- **Request Body:** `List[Transaction]` (max 1,000)
- **Response:** `BatchAnalysisResponse` with statistics
- **Processing:** Concurrent with `asyncio`

---

## Key Design Decisions

1. **Parallel Agent Execution**: Identity and Behavioral agents run simultaneously to minimize latency
2. **Structured Output**: Pydantic schemas ensure type safety and validation
3. **Async/Await**: Full async stack for optimal concurrency
4. **Error Handling**: Individual transaction errors don't fail the entire batch
5. **Timeout Protection**: 3-second timeout prevents hanging requests
6. **Low Temperature**: 0.1 temperature for consistent, deterministic outputs

---

## Performance Characteristics

- **Single Transaction**: < 3 seconds (target)
- **P95 Latency**: < 2.5 seconds (target)
- **Batch Processing**: Up to 1,000 concurrent requests
- **LLM Model**: Groq Llama 3.1 8B (sub-second inference)

---

## Error Handling

The system handles errors at multiple levels:

1. **Validation Errors**: Pydantic schema validation catches invalid input
2. **API Errors**: HTTPException with appropriate status codes
3. **Agent Errors**: Individual agent failures don't crash the workflow
4. **Timeout Errors**: `asyncio.TimeoutError` for long-running operations
5. **JSON Parsing Errors**: Graceful handling of malformed LLM responses

---

## Conclusion

Sentinel-MAS uses a multi-agent architecture with parallel execution to achieve high-speed fraud detection. The system processes transactions through three specialized agents (Identity, Behavioral, and Scoring) orchestrated by LangGraph, with all LLM inference handled by Groq's fast API. The complete trace of agent reasoning is returned for transparency and debugging.

