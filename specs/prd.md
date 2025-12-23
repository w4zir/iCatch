1. Project Overview
Project Name: Sentinel-MAS (Multi-Agent Fraud Detection) Objective: A high-speed, multi-agent system designed to identify fraudulent transactions within the Amazon Fraud Dataset Benchmark (FDB) using parallel reasoning.

2. Target Goals
Latency: End-to-end processing of a single transaction in < 3 seconds.

Scale: Support batch processing of up to 1,000 simulated requests.

Transparency: Provide "Chain of Thought" reasoning for single-transaction analysis.

3. System Architecture
Orchestration Layer: LangGraph (Stateful, Parallel DAG).

Inference Layer: Groq (Llama 3.1 8B/70B) for sub-second reasoning.

API Layer: FastAPI with Asynchronous concurrency.

Frontend: Simple Streamlit based UI to select single or cocurrent requests.

4. Functional Requirements
Batch Simulation Mode:

Upload/Load Amazon FDB dataset.

Trigger 1,000 concurrent requests via asyncio.

Display a summary dashboard: Total Fraud Caught, False Positives, and Average Latency.

Single-User Inspection Mode:

Manual input or random selection of a transaction.

Visual "Trace" of the agents: Identity Agent, Behavioral Agent, and Risk Scoring Agent.

Final "Reasoning" block explaining the Approve/Deny decision.

5. Success Metrics
P95 Latency: 95% of transactions processed in < 2.5s.

Structured Output: 100% adherence to Pydantic JSON schemas to prevent parsing errors.