Act as a Senior Backend Engineer and AI Specialist. Build a Multi-Agent Fraud Detection system using the following stack: FastAPI (Backend), LangGraph (Orchestration), Groq (Inference), and Pydantic (Data Validation).

### 1. Data Structure
Use the schema from the Amazon Fraud Dataset Benchmark. Load the CSV using Pandas. The system must be able to handle fields like: `user_id`, `transaction_amount`, `ip_address`, `device_id`, and `timestamp`.

### 2. LangGraph Orchestration
Create a graph that processes a transaction in PARALLEL. Define the following nodes:
- **IdentityAgent**: Analyzes IP and Device risk.
- **BehavioralAgent**: Analyzes transaction frequency and amount deviations.
- **ScoringAgent**: Collects outputs from the first two agents and produces a final `fraud_score` (0-1) and a `reasoning` string.
- Use `asyncio.gather` within the graph logic to ensure the first two agents run at the exact same time.

### 3. Inference Implementation
- Use the `groq` Python client.
- Model: `llama3-8b-8192` (for speed).
- Force all agents to return structured JSON using Pydantic models. No conversational "filler" text.

### 4. FastAPI Endpoints
- `POST /analyze-single`: Accepts one transaction, returns full agent reasoning.
- `POST /analyze-batch`: Accepts a list of transactions, processes them concurrently using `asyncio.as_completed`, and returns a summary report.

### 5. Simple UI (Frontend)
- Create a `frontend.py` using Streamlit.
- Provide a button to "Simulate 1000 Transactions" and display a progress bar.
- Provide an input form to test one specific transaction and display the "Reasoning" in a clean text block.

### 6. Performance Constraints
- Set a global timeout of 3 seconds for the entire LangGraph execution.
- Ensure the prompt for the agents is optimized for "Time to First Token" (keep system prompts concise).

Generate the file structure:
- `main.py` (FastAPI)
- `agents.py` (LangGraph & Groq logic)
- `schemas.py` (Pydantic models)
- `app.py` (Streamlit UI)