"""FastAPI application for Sentinel-MAS fraud detection system."""
import asyncio
import time
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import (
    Transaction,
    SingleAnalysisResponse,
    BatchAnalysisResponse,
    BatchAnalysisResult,
)
from agents import analyze_transaction
import config


app = FastAPI(
    title="Sentinel-MAS Fraud Detection API",
    description="Multi-Agent Fraud Detection System using LangGraph and Groq",
    version="1.0.0"
)

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "Sentinel-MAS Fraud Detection API"}


@app.post("/analyze-single", response_model=SingleAnalysisResponse)
async def analyze_single(transaction: Transaction):
    """
    Analyze a single transaction with full agent reasoning trace.
    
    Args:
        transaction: Transaction to analyze
        
    Returns:
        SingleAnalysisResponse with full trace and reasoning
    """
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


@app.post("/analyze-batch", response_model=BatchAnalysisResponse)
async def analyze_batch(transactions: List[Transaction]):
    """
    Analyze multiple transactions concurrently.
    
    Args:
        transactions: List of transactions to analyze
        
    Returns:
        BatchAnalysisResponse with summary statistics
    """
    if len(transactions) > config.MAX_CONCURRENT_REQUESTS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {config.MAX_CONCURRENT_REQUESTS} transactions allowed per batch"
        )
    
    results: List[BatchAnalysisResult] = []
    latencies: List[float] = []
    
    # Process transactions concurrently
    async def process_single(txn: Transaction, idx: int) -> BatchAnalysisResult:
        start_time = time.time()
        try:
            trace = await analyze_transaction(txn)
            latency_ms = (time.time() - start_time) * 1000
            latencies.append(latency_ms)
            
            return BatchAnalysisResult(
                transaction_id=str(idx),
                fraud_score=trace.scoring_agent.fraud_score,
                decision=trace.scoring_agent.decision,
                latency_ms=latency_ms,
                error=None
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return BatchAnalysisResult(
                transaction_id=str(idx),
                fraud_score=0.0,
                decision="error",
                latency_ms=latency_ms,
                error=str(e)
            )
    
    # Create tasks for all transactions
    tasks = [process_single(txn, idx) for idx, txn in enumerate(transactions)]
    
    # Process with asyncio.as_completed for better progress tracking
    completed_tasks = []
    for coro in asyncio.as_completed(tasks):
        result = await coro
        completed_tasks.append(result)
    
    results = completed_tasks
    
    # Calculate statistics
    total_processed = len(results)
    errors = sum(1 for r in results if r.error is not None)
    successful_results = [r for r in results if r.error is None]
    
    fraud_detected = sum(1 for r in successful_results if r.decision == "deny")
    approved = sum(1 for r in successful_results if r.decision == "approve")
    denied = fraud_detected
    
    # Calculate latency statistics
    successful_latencies = [r.latency_ms for r in successful_results]
    if successful_latencies:
        successful_latencies.sort()
        n = len(successful_latencies)
        p50 = successful_latencies[n // 2] if n > 0 else 0.0
        p95_idx = int(n * 0.95)
        p95 = successful_latencies[p95_idx] if p95_idx < n else successful_latencies[-1]
        avg_latency = sum(successful_latencies) / n
    else:
        p50 = p95 = avg_latency = 0.0
    
    latency_stats = {
        "p50_ms": p50,
        "p95_ms": p95,
        "avg_ms": avg_latency,
    }
    
    # Only include results if batch is small enough (for large batches, omit to save bandwidth)
    include_results = len(results) <= 100
    
    return BatchAnalysisResponse(
        total_processed=total_processed,
        fraud_detected=denied,
        approved=approved,
        denied=denied,
        errors=errors,
        latency_stats=latency_stats,
        results=results if include_results else []
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True
    )

