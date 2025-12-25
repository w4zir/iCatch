"""Example script showing how to check agent traces."""
import asyncio
from schemas import Transaction, AgentTrace
from agents import analyze_transaction
from trace_utils import (
    print_trace,
    save_trace_to_file,
    log_trace,
    compare_traces,
    get_trace_summary,
    trace_to_dict
)


async def example_single_trace():
    """Example: Analyze a single transaction and view its trace."""
    print("=" * 80)
    print("EXAMPLE 1: Single Transaction Trace")
    print("=" * 80)
    
    # Create a sample transaction
    transaction = Transaction(
        user_id="user_123",
        transaction_amount=99.99,
        ip_address="192.168.1.1",
        device_id="device_456",
        timestamp="2024-01-15T10:30:00Z"
    )
    
    # Analyze transaction
    trace = await analyze_transaction(transaction)
    
    # Method 1: Pretty print to console
    print_trace(trace, transaction_id=transaction.user_id, detailed=True)
    
    # Method 2: Get summary (scores only)
    summary = get_trace_summary(trace)
    print("Summary (scores only):")
    print(summary)
    
    # Method 3: Save to JSON file
    save_trace_to_file(trace, "trace_example.json", transaction_id=transaction.user_id)
    
    # Method 4: Convert to dictionary
    trace_dict = trace_to_dict(trace)
    print("\nTrace as dictionary:")
    print(trace_dict)


async def example_compare_traces():
    """Example: Compare traces from two different transactions."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Compare Two Traces")
    print("=" * 80)
    
    # Transaction 1: Normal transaction
    transaction1 = Transaction(
        user_id="user_normal",
        transaction_amount=50.00,
        ip_address="192.168.1.1",
        device_id="device_known",
        timestamp="2024-01-15T10:30:00Z"
    )
    
    # Transaction 2: Suspicious transaction
    transaction2 = Transaction(
        user_id="user_suspicious",
        transaction_amount=5000.00,
        ip_address="10.0.0.1",  # Different IP
        device_id="device_unknown",
        timestamp="2024-01-15T10:30:00Z"
    )
    
    # Analyze both
    trace1 = await analyze_transaction(transaction1)
    trace2 = await analyze_transaction(transaction2)
    
    # Compare traces
    compare_traces(trace1, trace2, label1="Normal", label2="Suspicious")


async def example_log_traces():
    """Example: Log multiple traces to a file."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Log Multiple Traces")
    print("=" * 80)
    
    transactions = [
        Transaction(
            user_id=f"user_{i}",
            transaction_amount=float(10 * i),
            ip_address=f"192.168.1.{i % 255}",
            device_id=f"device_{i}",
            timestamp="2024-01-15T10:30:00Z"
        )
        for i in range(3)
    ]
    
    log_file = "traces_batch.log"
    
    for transaction in transactions:
        trace = await analyze_transaction(transaction)
        # Log to file (append mode)
        log_trace(
            trace,
            transaction_id=transaction.user_id,
            log_file=log_file,
            console=False  # Don't print to console for batch processing
        )
    
    print(f"\nLogged {len(transactions)} traces to {log_file}")


async def example_api_response_trace():
    """Example: Extract and view trace from API response."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Trace from API Response")
    print("=" * 80)
    
    import httpx
    
    # Make API call
    transaction_data = {
        "user_id": "user_api",
        "transaction_amount": 150.00,
        "ip_address": "192.168.1.100",
        "device_id": "device_api",
        "timestamp": "2024-01-15T10:30:00Z"
    }
    
    try:
        response = httpx.post(
            "http://localhost:8000/analyze-single",
            json=transaction_data,
            timeout=10.0
        )
        response.raise_for_status()
        result = response.json()
        
        # Extract trace from API response
        # The API returns a SingleAnalysisResponse which contains a trace
        trace_dict = result["trace"]
        
        # Convert dict back to AgentTrace object
        from schemas import (
            IdentityAgentOutput,
            BehavioralAgentOutput,
            ScoringAgentOutput
        )
        
        trace = AgentTrace(
            identity_agent=IdentityAgentOutput(**trace_dict["identity_agent"]),
            behavioral_agent=BehavioralAgentOutput(**trace_dict["behavioral_agent"]),
            scoring_agent=ScoringAgentOutput(**trace_dict["scoring_agent"])
        )
        
        # Now you can use trace utilities
        print_trace(trace, transaction_id=transaction_data["user_id"])
        print(f"\nLatency: {result['latency_ms']:.0f}ms")
        
    except httpx.ConnectError:
        print("⚠️  API not available. Start the FastAPI server first:")
        print("   python main.py")
    except Exception as e:
        print(f"Error: {e}")


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("AGENT TRACE CHECKING EXAMPLES")
    print("=" * 80)
    print("\nThis script demonstrates various ways to check agent traces:")
    print("1. Single trace viewing")
    print("2. Trace comparison")
    print("3. Batch trace logging")
    print("4. Trace from API response")
    print("\n" + "=" * 80 + "\n")
    
    # Run examples
    await example_single_trace()
    await example_compare_traces()
    await example_log_traces()
    await example_api_response_trace()
    
    print("\n" + "=" * 80)
    print("All examples completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

