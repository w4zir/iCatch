"""Quick profiling script to identify bottlenecks in batch processing."""
import asyncio
import time
import sys
from main import analyze_batch
from schemas import Transaction


async def profile_batch(num_transactions: int = 5):
    """
    Profile batch processing to identify performance bottlenecks.
    
    Args:
        num_transactions: Number of test transactions to process
    """
    # Create test transactions
    transactions = [
        Transaction(
            user_id=f"user_{i}",
            transaction_amount=100.0 + i * 10,
            ip_address=f"192.168.1.{i}",
            device_id=f"device_{i}",
            timestamp="2024-01-01T00:00:00Z"
        )
        for i in range(num_transactions)
    ]
    
    print(f"🔍 Profiling batch of {len(transactions)} transactions...")
    print("=" * 60)
    
    start = time.time()
    
    try:
        result = await analyze_batch(transactions)
        
        total_time = time.time() - start
        
        print("\n" + "=" * 60)
        print("📊 PROFILING RESULTS")
        print("=" * 60)
        print(f"Total batch time: {total_time:.2f}s")
        print(f"Average per transaction: {total_time/len(transactions):.2f}s")
        print(f"Expected (parallel, ~3s per transaction): ~3s total")
        print(f"Slowdown factor: {total_time/3:.1f}x")
        
        if result.latency_stats:
            print(f"\n📈 Latency Statistics:")
            print(f"  Average: {result.latency_stats['avg_ms']:.0f}ms")
            print(f"  P50 (median): {result.latency_stats['p50_ms']:.0f}ms")
            print(f"  P95: {result.latency_stats['p95_ms']:.0f}ms")
        
        print(f"\n✅ Successfully processed: {result.total_processed}")
        print(f"❌ Errors: {result.errors}")
        print(f"🛡️  Fraud detected: {result.fraud_detected}")
        print(f"✅ Approved: {result.approved}")
        
        # Performance analysis
        if total_time > 3.0:
            print(f"\n⚠️  PERFORMANCE WARNING:")
            print(f"   Batch took {total_time:.2f}s, expected ~3s")
            print(f"   Check console logs for [GROQ API] and [PERF] timing details")
            print(f"   Possible issues:")
            print(f"   - Groq API rate limiting (check [GROQ API] logs)")
            print(f"   - Sequential processing instead of parallel")
            print(f"   - Network latency")
        else:
            print(f"\n✅ Performance target met: {total_time:.2f}s < 3s")
            
    except Exception as e:
        total_time = time.time() - start
        print(f"\n❌ Error during profiling: {str(e)}")
        print(f"   Time elapsed: {total_time:.2f}s")
        raise


if __name__ == "__main__":
    num_txns = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    asyncio.run(profile_batch(num_txns))

