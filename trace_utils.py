"""Utility functions for viewing and logging agent traces."""
import json
import sys
from typing import Dict, Any, Optional
from datetime import datetime
from schemas import AgentTrace, IdentityAgentOutput, BehavioralAgentOutput, ScoringAgentOutput


def print_trace(trace: AgentTrace, transaction_id: Optional[str] = None, detailed: bool = True):
    """
    Pretty print an agent trace to console.
    
    Args:
        trace: AgentTrace object to display
        transaction_id: Optional transaction ID to include in header
        detailed: If True, show detailed reasoning; if False, show only scores
    """
    print("\n" + "=" * 80)
    if transaction_id:
        print(f"AGENT TRACE - Transaction: {transaction_id}")
    else:
        print("AGENT TRACE")
    print("=" * 80)
    
    # Identity Agent
    print("\n[1] IDENTITY AGENT")
    print("-" * 80)
    identity = trace.identity_agent
    print(f"  IP Risk Score:        {identity.ip_risk_score:.3f}")
    print(f"  Device Risk Score:    {identity.device_risk_score:.3f}")
    if detailed:
        print(f"  Reasoning:")
        for line in identity.reasoning.split('\n'):
            print(f"    {line}")
    
    # Behavioral Agent
    print("\n[2] BEHAVIORAL AGENT")
    print("-" * 80)
    behavioral = trace.behavioral_agent
    print(f"  Frequency Anomaly Score:  {behavioral.frequency_anomaly_score:.3f}")
    print(f"  Amount Deviation Score:   {behavioral.amount_deviation_score:.3f}")
    if detailed:
        print(f"  Reasoning:")
        for line in behavioral.reasoning.split('\n'):
            print(f"    {line}")
    
    # Scoring Agent
    print("\n[3] SCORING AGENT (FINAL)")
    print("-" * 80)
    scoring = trace.scoring_agent
    decision_icon = "❌ DENY" if scoring.decision == "deny" else "✅ APPROVE"
    print(f"  Fraud Score:          {scoring.fraud_score:.3f}")
    print(f"  Decision:             {decision_icon}")
    if detailed:
        print(f"  Reasoning:")
        for line in scoring.reasoning.split('\n'):
            print(f"    {line}")
    
    print("\n" + "=" * 80 + "\n")


def trace_to_dict(trace: AgentTrace) -> Dict[str, Any]:
    """
    Convert AgentTrace to dictionary for JSON serialization.
    
    Args:
        trace: AgentTrace object
        
    Returns:
        Dictionary representation of the trace
    """
    return {
        "identity_agent": {
            "ip_risk_score": trace.identity_agent.ip_risk_score,
            "device_risk_score": trace.identity_agent.device_risk_score,
            "reasoning": trace.identity_agent.reasoning
        },
        "behavioral_agent": {
            "frequency_anomaly_score": trace.behavioral_agent.frequency_anomaly_score,
            "amount_deviation_score": trace.behavioral_agent.amount_deviation_score,
            "reasoning": trace.behavioral_agent.reasoning
        },
        "scoring_agent": {
            "fraud_score": trace.scoring_agent.fraud_score,
            "decision": trace.scoring_agent.decision,
            "reasoning": trace.scoring_agent.reasoning
        }
    }


def save_trace_to_file(trace: AgentTrace, filepath: str, transaction_id: Optional[str] = None):
    """
    Save trace to JSON file.
    
    Args:
        trace: AgentTrace object to save
        filepath: Path to output file
        transaction_id: Optional transaction ID to include in metadata
    """
    data = {
        "timestamp": datetime.utcnow().isoformat(),
        "transaction_id": transaction_id,
        "trace": trace_to_dict(trace)
    }
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Trace saved to: {filepath}")


def log_trace(trace: AgentTrace, transaction_id: Optional[str] = None, 
              log_file: Optional[str] = None, console: bool = True):
    """
    Log trace to console and/or file.
    
    Args:
        trace: AgentTrace object to log
        transaction_id: Optional transaction ID
        log_file: Optional path to log file (appends if exists)
        console: If True, print to console
    """
    if console:
        print_trace(trace, transaction_id)
    
    if log_file:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "transaction_id": transaction_id,
            "trace": trace_to_dict(trace)
        }
        
        # Append to log file
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        print(f"Trace logged to: {log_file}")


def compare_traces(trace1: AgentTrace, trace2: AgentTrace, 
                   label1: str = "Trace 1", label2: str = "Trace 2"):
    """
    Compare two traces side by side.
    
    Args:
        trace1: First AgentTrace to compare
        trace2: Second AgentTrace to compare
        label1: Label for first trace
        label2: Label for second trace
    """
    print("\n" + "=" * 80)
    print("TRACE COMPARISON")
    print("=" * 80)
    
    # Identity Agent Comparison
    print(f"\n[1] IDENTITY AGENT")
    print("-" * 80)
    print(f"{'Metric':<30} {label1:<20} {label2:<20} {'Diff':<10}")
    print("-" * 80)
    ip_diff = trace1.identity_agent.ip_risk_score - trace2.identity_agent.ip_risk_score
    device_diff = trace1.identity_agent.device_risk_score - trace2.identity_agent.device_risk_score
    print(f"{'IP Risk Score':<30} {trace1.identity_agent.ip_risk_score:<20.3f} {trace2.identity_agent.ip_risk_score:<20.3f} {ip_diff:+.3f}")
    print(f"{'Device Risk Score':<30} {trace1.identity_agent.device_risk_score:<20.3f} {trace2.identity_agent.device_risk_score:<20.3f} {device_diff:+.3f}")
    
    # Behavioral Agent Comparison
    print(f"\n[2] BEHAVIORAL AGENT")
    print("-" * 80)
    print(f"{'Metric':<30} {label1:<20} {label2:<20} {'Diff':<10}")
    print("-" * 80)
    freq_diff = trace1.behavioral_agent.frequency_anomaly_score - trace2.behavioral_agent.frequency_anomaly_score
    amount_diff = trace1.behavioral_agent.amount_deviation_score - trace2.behavioral_agent.amount_deviation_score
    print(f"{'Frequency Anomaly Score':<30} {trace1.behavioral_agent.frequency_anomaly_score:<20.3f} {trace2.behavioral_agent.frequency_anomaly_score:<20.3f} {freq_diff:+.3f}")
    print(f"{'Amount Deviation Score':<30} {trace1.behavioral_agent.amount_deviation_score:<20.3f} {trace2.behavioral_agent.amount_deviation_score:<20.3f} {amount_diff:+.3f}")
    
    # Scoring Agent Comparison
    print(f"\n[3] SCORING AGENT")
    print("-" * 80)
    print(f"{'Metric':<30} {label1:<20} {label2:<20} {'Diff':<10}")
    print("-" * 80)
    fraud_diff = trace1.scoring_agent.fraud_score - trace2.scoring_agent.fraud_score
    print(f"{'Fraud Score':<30} {trace1.scoring_agent.fraud_score:<20.3f} {trace2.scoring_agent.fraud_score:<20.3f} {fraud_diff:+.3f}")
    print(f"{'Decision':<30} {trace1.scoring_agent.decision:<20} {trace2.scoring_agent.decision:<20} {'-' if trace1.scoring_agent.decision == trace2.scoring_agent.decision else 'DIFFERENT'}")
    
    print("\n" + "=" * 80 + "\n")


def get_trace_summary(trace: AgentTrace) -> Dict[str, Any]:
    """
    Get a summary of the trace (scores only, no reasoning).
    
    Args:
        trace: AgentTrace object
        
    Returns:
        Dictionary with summary scores
    """
    return {
        "identity": {
            "ip_risk_score": trace.identity_agent.ip_risk_score,
            "device_risk_score": trace.identity_agent.device_risk_score
        },
        "behavioral": {
            "frequency_anomaly_score": trace.behavioral_agent.frequency_anomaly_score,
            "amount_deviation_score": trace.behavioral_agent.amount_deviation_score
        },
        "scoring": {
            "fraud_score": trace.scoring_agent.fraud_score,
            "decision": trace.scoring_agent.decision
        }
    }

