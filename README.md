# Sentinel-MAS: Multi-Agent Fraud Detection System

A high-speed, multi-agent system designed to identify fraudulent transactions within the Amazon Fraud Dataset Benchmark (FDB) using parallel reasoning.

## Features

- **Parallel Agent Architecture**: Identity and Behavioral agents run simultaneously for optimal performance
- **Sub-second Inference**: Powered by Groq's Llama 3.1 8B model
- **Batch Processing**: Support for up to 1,000 concurrent requests
- **Transparency**: Chain of Thought reasoning for every decision
- **Performance**: P95 latency < 2.5 seconds

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your GROQ_API_KEY
   ```

3. **Run FastAPI Backend**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Run Streamlit Frontend**
   ```bash
   streamlit run app.py
   ```

## Architecture

The system uses LangGraph to orchestrate three agents:
- **IdentityAgent**: Analyzes IP and Device risk
- **BehavioralAgent**: Analyzes transaction frequency and amount deviations
- **ScoringAgent**: Aggregates results and produces final fraud score

## API Endpoints

- `POST /analyze-single`: Analyze a single transaction with full reasoning trace
- `POST /analyze-batch`: Process multiple transactions concurrently

## Performance Targets

- Single transaction: < 3 seconds
- P95 latency: < 2.5 seconds
- Batch processing: 1,000 concurrent requests

