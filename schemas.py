"""Pydantic models for transaction validation and agent outputs."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class Transaction(BaseModel):
    """Transaction input schema matching Amazon FDB format."""
    user_id: str = Field(..., description="Unique user identifier")
    transaction_amount: float = Field(..., description="Transaction amount in currency units")
    ip_address: str = Field(..., description="IP address of the transaction")
    device_id: str = Field(..., description="Device identifier")
    timestamp: str = Field(..., description="Transaction timestamp")
    
    # Additional fields that may exist in Amazon FDB
    payment_method: Optional[str] = None
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None
    product_category: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "transaction_amount": 99.99,
                "ip_address": "192.168.1.1",
                "device_id": "device_456",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class IdentityAgentOutput(BaseModel):
    """Output from Identity Agent analyzing IP and Device risk."""
    ip_risk_score: float = Field(..., ge=0.0, le=1.0, description="IP address risk score (0-1)")
    device_risk_score: float = Field(..., ge=0.0, le=1.0, description="Device risk score (0-1)")
    reasoning: str = Field(..., description="Explanation of identity risk assessment")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ip_risk_score": 0.3,
                "device_risk_score": 0.2,
                "reasoning": "IP address shows normal patterns. Device ID matches user history."
            }
        }


class BehavioralAgentOutput(BaseModel):
    """Output from Behavioral Agent analyzing transaction patterns."""
    frequency_anomaly_score: float = Field(..., ge=0.0, le=1.0, description="Transaction frequency anomaly score (0-1)")
    amount_deviation_score: float = Field(..., ge=0.0, le=1.0, description="Amount deviation from normal patterns (0-1)")
    reasoning: str = Field(..., description="Explanation of behavioral risk assessment")
    
    class Config:
        json_schema_extra = {
            "example": {
                "frequency_anomaly_score": 0.1,
                "amount_deviation_score": 0.4,
                "reasoning": "Transaction frequency is normal. Amount is slightly higher than average but within acceptable range."
            }
        }


class ScoringAgentOutput(BaseModel):
    """Final output from Scoring Agent with fraud decision."""
    fraud_score: float = Field(..., ge=0.0, le=1.0, description="Final fraud score (0-1)")
    decision: str = Field(..., pattern="^(approve|deny)$", description="Final decision: approve or deny")
    reasoning: str = Field(..., description="Comprehensive explanation of the fraud decision")
    
    class Config:
        json_schema_extra = {
            "example": {
                "fraud_score": 0.25,
                "decision": "approve",
                "reasoning": "Combined risk scores from identity and behavioral agents indicate low fraud probability. Transaction approved."
            }
        }


class AgentTrace(BaseModel):
    """Complete trace of all agent outputs for a transaction."""
    identity_agent: IdentityAgentOutput
    behavioral_agent: BehavioralAgentOutput
    scoring_agent: ScoringAgentOutput


class SingleAnalysisResponse(BaseModel):
    """Response for single transaction analysis."""
    transaction: Transaction
    trace: AgentTrace
    latency_ms: float = Field(..., description="Total processing time in milliseconds")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class BatchAnalysisResult(BaseModel):
    """Result for a single transaction in batch processing."""
    transaction_id: Optional[str] = None
    fraud_score: float
    decision: str
    latency_ms: float
    error: Optional[str] = None


class BatchAnalysisResponse(BaseModel):
    """Response for batch transaction analysis."""
    total_processed: int
    fraud_detected: int
    approved: int
    denied: int
    errors: int
    latency_stats: Dict[str, float] = Field(..., description="P50, P95, and average latency in milliseconds")
    results: List[BatchAnalysisResult] = Field(default_factory=list, description="Individual results (optional, can be empty for large batches)")

