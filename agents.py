"""LangGraph orchestration and Groq inference for fraud detection agents."""
import asyncio
import json
import time
from typing import Dict, Any, TypedDict, Annotated
from groq import Groq
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, ValidationError
import config
from schemas import (
    Transaction,
    IdentityAgentOutput,
    BehavioralAgentOutput,
    ScoringAgentOutput,
    AgentTrace,
)


# Initialize Groq client
groq_client = Groq(api_key=config.GROQ_API_KEY)


class AgentState(TypedDict):
    """State passed through the LangGraph."""
    transaction: Transaction
    transaction_data: Dict[str, Any]
    identity_output: Annotated[IdentityAgentOutput | None, "Identity agent output"]
    behavioral_output: Annotated[BehavioralAgentOutput | None, "Behavioral agent output"]
    scoring_output: Annotated[ScoringAgentOutput | None, "Final scoring output"]
    error: Annotated[str | None, "Error message if any"]


async def call_groq_structured(
    prompt: str,
    output_schema: type[BaseModel],
    system_prompt: str = "",
) -> BaseModel:
    """
    Call Groq API with structured JSON output.
    
    Args:
        prompt: User prompt for the agent
        output_schema: Pydantic model for expected output
        system_prompt: System prompt (kept concise for speed)
        
    Returns:
        Validated Pydantic model instance
        
    Raises:
        ValueError: If response cannot be parsed or validated
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    try:
        # Get JSON schema from Pydantic model
        json_schema = output_schema.model_json_schema()
        
        # Create prompt that enforces JSON output
        json_prompt = f"""{prompt}

You must respond with ONLY valid JSON matching this schema:
{json.dumps(json_schema, indent=2)}

Do not include any explanatory text, markdown formatting, or code blocks. Return only the JSON object."""
        
        messages[-1]["content"] = json_prompt
        
        # Try with response_format first (if supported), fallback without it
        try:
            response = groq_client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=messages,
                temperature=0.1,  # Low temperature for consistent structured output
                response_format={"type": "json_object"},
            )
        except TypeError:
            # response_format not supported, try without it
            response = groq_client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=messages,
                temperature=0.1,
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
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {str(e)}")
    except ValidationError as e:
        raise ValueError(f"Response validation failed: {str(e)}")
    except Exception as e:
        raise ValueError(f"Groq API error: {str(e)}")


async def identity_agent_node(state: AgentState) -> AgentState:
    """Identity Agent: Analyzes IP and Device risk."""
    transaction_data = state.get("transaction_data", {})
    
    # Validate required fields
    required_fields = ["user_id", "ip_address", "device_id", "timestamp"]
    missing_fields = [field for field in required_fields if field not in transaction_data or transaction_data[field] is None]
    if missing_fields:
        return {
            **state,
            "error": f"Identity agent error: Missing required transaction data fields: {', '.join(missing_fields)}",
            "identity_output": None
        }
    
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
    
    try:
        output = await call_groq_structured(prompt, IdentityAgentOutput, system_prompt)
        return {**state, "identity_output": output}
    except Exception as e:
        return {**state, "error": f"Identity agent error: {str(e)}", "identity_output": None}


async def behavioral_agent_node(state: AgentState) -> AgentState:
    """Behavioral Agent: Analyzes transaction frequency and amount deviations."""
    transaction_data = state.get("transaction_data", {})
    
    # Validate required fields
    required_fields = ["user_id", "transaction_amount", "timestamp"]
    missing_fields = [field for field in required_fields if field not in transaction_data or transaction_data[field] is None]
    if missing_fields:
        return {
            **state,
            "error": f"Behavioral agent error: Missing required transaction data fields: {', '.join(missing_fields)}",
            "behavioral_output": None
        }
    
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
    
    try:
        output = await call_groq_structured(prompt, BehavioralAgentOutput, system_prompt)
        return {**state, "behavioral_output": output}
    except Exception as e:
        return {**state, "error": f"Behavioral agent error: {str(e)}", "behavioral_output": None}


async def parallel_agents_node(state: AgentState) -> AgentState:
    """Execute Identity and Behavioral agents in parallel."""
    identity_task = identity_agent_node(state)
    behavioral_task = behavioral_agent_node(state)
    
    identity_state, behavioral_state = await asyncio.gather(
        identity_task,
        behavioral_task,
        return_exceptions=True
    )
    
    # Handle exceptions
    if isinstance(identity_state, Exception):
        identity_state = {**state, "error": f"Identity agent exception: {str(identity_state)}", "identity_output": None}
    if isinstance(behavioral_state, Exception):
        behavioral_state = {**state, "error": f"Behavioral agent exception: {str(behavioral_state)}", "behavioral_output": None}
    
    # Merge results - always update outputs to ensure state is properly updated
    merged_state = {**state}
    # Always update outputs from agent states (even if None) to ensure proper state tracking
    merged_state["identity_output"] = identity_state.get("identity_output")
    merged_state["behavioral_output"] = behavioral_state.get("behavioral_output")
    
    # Merge errors
    errors = []
    if identity_state.get("error"):
        errors.append(identity_state["error"])
    if behavioral_state.get("error"):
        errors.append(behavioral_state["error"])
    
    if errors:
        merged_state["error"] = "; ".join(errors)
    
    return merged_state


async def scoring_agent_node(state: AgentState) -> AgentState:
    """Scoring Agent: Aggregates results and produces final fraud score."""
    identity_output = state.get("identity_output")
    behavioral_output = state.get("behavioral_output")
    error = state.get("error")
    
    if not identity_output or not behavioral_output:
        missing = []
        if not identity_output:
            missing.append("identity_output")
        if not behavioral_output:
            missing.append("behavioral_output")
        
        error_msg = f"Missing required agent outputs for scoring: {', '.join(missing)}"
        if error:
            error_msg += f". Previous errors: {error}"
        
        return {
            **state,
            "error": error_msg,
            "scoring_output": None
        }
    
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
    
    try:
        output = await call_groq_structured(prompt, ScoringAgentOutput, system_prompt)
        return {**state, "scoring_output": output}
    except Exception as e:
        return {**state, "error": f"Scoring agent error: {str(e)}", "scoring_output": None}


def create_fraud_detection_graph():
    """Create and configure the LangGraph state machine."""
    workflow = StateGraph(AgentState)
    
    # Entry: Prepare transaction data
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


async def analyze_transaction(transaction: Transaction) -> AgentTrace:
    """
    Analyze a single transaction through the fraud detection pipeline.
    
    Args:
        transaction: Transaction to analyze
        
    Returns:
        AgentTrace with all agent outputs
        
    Raises:
        ValueError: If analysis fails or times out
    """
    graph = create_fraud_detection_graph()
    
    initial_state: AgentState = {
        "transaction": transaction,
        "transaction_data": {},
        "identity_output": None,
        "behavioral_output": None,
        "scoring_output": None,
        "error": None,
    }
    
    try:
        # Execute with timeout
        final_state = await asyncio.wait_for(
            graph.ainvoke(initial_state),
            timeout=config.TIMEOUT_SECONDS
        )
        
        # Check for errors
        if final_state.get("error"):
            raise ValueError(final_state["error"])
        
        identity_output = final_state.get("identity_output")
        behavioral_output = final_state.get("behavioral_output")
        scoring_output = final_state.get("scoring_output")
        
        if not all([identity_output, behavioral_output, scoring_output]):
            raise ValueError("Incomplete agent outputs")
        
        return AgentTrace(
            identity_agent=identity_output,
            behavioral_agent=behavioral_output,
            scoring_agent=scoring_output
        )
        
    except asyncio.TimeoutError:
        raise ValueError(f"Analysis timed out after {config.TIMEOUT_SECONDS} seconds")
    except Exception as e:
        raise ValueError(f"Analysis failed: {str(e)}")

