"""Streamlit frontend for Sentinel-MAS fraud detection system."""
import streamlit as st
import pandas as pd
import httpx
import asyncio
from typing import Dict, Any
import json
from utils import load_amazon_fdb, sample_transaction
from schemas import Transaction


# Page configuration
st.set_page_config(
    page_title="Sentinel-MAS Fraud Detection",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Sentinel-MAS: Multi-Agent Fraud Detection")
st.markdown("High-speed fraud detection using parallel agent reasoning")

# API endpoint
API_URL = st.sidebar.text_input(
    "API URL",
    value="http://localhost:8000",
    help="FastAPI backend URL"
)

# Initialize session state
if "dataset" not in st.session_state:
    st.session_state.dataset = None
if "dataset_loaded" not in st.session_state:
    st.session_state.dataset_loaded = False


def check_api_health() -> bool:
    """Check if API is available."""
    try:
        response = httpx.get(f"{API_URL}/", timeout=2.0)
        return response.status_code == 200
    except:
        return False


# Mode selection
mode = st.sidebar.radio(
    "Select Mode",
    ["Single Transaction Analysis", "Batch Simulation"],
    index=0
)

# API health check
if not check_api_health():
    st.error(f"⚠️ Cannot connect to API at {API_URL}. Please ensure the FastAPI server is running.")
    st.stop()

st.success("✅ Connected to API")


if mode == "Single Transaction Analysis":
    st.header("Single Transaction Analysis")
    st.markdown("Analyze a single transaction with full agent reasoning trace")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Transaction Input")
        
        # Load dataset for random sampling
        if st.button("Load Dataset (for random sampling)"):
            try:
                with st.spinner("Loading dataset..."):
                    df = load_amazon_fdb()
                    st.session_state.dataset = df
                    st.session_state.dataset_loaded = True
                    st.success(f"Dataset loaded: {len(df)} transactions")
            except Exception as e:
                st.error(f"Failed to load dataset: {str(e)}")
        
        # Random transaction button
        if st.session_state.dataset_loaded and st.session_state.dataset is not None:
            if st.button("🎲 Get Random Transaction"):
                try:
                    random_txn = sample_transaction(st.session_state.dataset)
                    st.session_state.random_transaction = random_txn
                    st.rerun()
                except Exception as e:
                    st.error(f"Error sampling transaction: {str(e)}")
        
        # Transaction form
        with st.form("transaction_form"):
            user_id = st.text_input("User ID", value=st.session_state.get("random_transaction", {}).get("user_id", ""))
            transaction_amount = st.number_input("Transaction Amount", value=float(st.session_state.get("random_transaction", {}).get("transaction_amount", 0.0)), step=0.01)
            ip_address = st.text_input("IP Address", value=st.session_state.get("random_transaction", {}).get("ip_address", ""))
            device_id = st.text_input("Device ID", value=st.session_state.get("random_transaction", {}).get("device_id", ""))
            timestamp = st.text_input("Timestamp", value=st.session_state.get("random_transaction", {}).get("timestamp", ""))
            
            submitted = st.form_submit_button("🔍 Analyze Transaction", use_container_width=True)
            
            if submitted:
                try:
                    transaction_data = {
                        "user_id": user_id,
                        "transaction_amount": transaction_amount,
                        "ip_address": ip_address,
                        "device_id": device_id,
                        "timestamp": timestamp,
                    }
                    
                    # Validate and send to API
                    with st.spinner("Analyzing transaction..."):
                        response = httpx.post(
                            f"{API_URL}/analyze-single",
                            json=transaction_data,
                            timeout=10.0
                        )
                        response.raise_for_status()
                        result = response.json()
                    
                    st.session_state.analysis_result = result
                    st.rerun()
                    
                except httpx.HTTPStatusError as e:
                    st.error(f"API Error: {e.response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Display results
    if "analysis_result" in st.session_state:
        result = st.session_state.analysis_result
        
        with col2:
            st.subheader("Decision")
            trace = result["trace"]
            scoring = trace["scoring_agent"]
            
            fraud_score = scoring["fraud_score"]
            decision = scoring["decision"]
            
            # Display decision
            if decision == "deny":
                st.error(f"❌ DENIED (Fraud Score: {fraud_score:.2f})")
            else:
                st.success(f"✅ APPROVED (Fraud Score: {fraud_score:.2f})")
            
            st.metric("Latency", f"{result['latency_ms']:.0f} ms")
        
        # Agent trace visualization
        st.subheader("Agent Trace")
        
        tab1, tab2, tab3 = st.tabs(["Identity Agent", "Behavioral Agent", "Scoring Agent"])
        
        with tab1:
            identity = trace["identity_agent"]
            st.metric("IP Risk Score", f"{identity['ip_risk_score']:.2f}")
            st.metric("Device Risk Score", f"{identity['device_risk_score']:.2f}")
            st.markdown("**Reasoning:**")
            st.info(identity["reasoning"])
        
        with tab2:
            behavioral = trace["behavioral_agent"]
            st.metric("Frequency Anomaly Score", f"{behavioral['frequency_anomaly_score']:.2f}")
            st.metric("Amount Deviation Score", f"{behavioral['amount_deviation_score']:.2f}")
            st.markdown("**Reasoning:**")
            st.info(behavioral["reasoning"])
        
        with tab3:
            st.metric("Final Fraud Score", f"{scoring['fraud_score']:.2f}")
            st.metric("Decision", scoring["decision"].upper())
            st.markdown("**Final Reasoning:**")
            st.success(scoring["reasoning"])


else:  # Batch Simulation Mode
    st.header("Batch Simulation Mode")
    st.markdown("Process multiple transactions concurrently and view summary statistics")
    
    # Dataset upload/load
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Load Dataset")
        uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.session_state.dataset = df
                st.session_state.dataset_loaded = True
                st.success(f"Dataset loaded: {len(df)} transactions")
            except Exception as e:
                st.error(f"Error loading file: {str(e)}")
        else:
            if st.button("Load Default Dataset"):
                try:
                    with st.spinner("Loading dataset..."):
                        df = load_amazon_fdb()
                        st.session_state.dataset = df
                        st.session_state.dataset_loaded = True
                        st.success(f"Dataset loaded: {len(df)} transactions")
                except Exception as e:
                    st.error(f"Failed to load dataset: {str(e)}")
    
    with col2:
        st.subheader("Simulation Settings")
        num_transactions = st.number_input(
            "Number of Transactions",
            min_value=1,
            max_value=1000,
            value=100,
            step=10
        )
        
        simulate_button = st.button(
            "🚀 Simulate Transactions",
            use_container_width=True,
            disabled=not st.session_state.dataset_loaded
        )
    
    # Run simulation
    if simulate_button and st.session_state.dataset_loaded:
        df = st.session_state.dataset
        
        if len(df) < num_transactions:
            st.warning(f"Dataset has only {len(df)} transactions. Using all available.")
            num_transactions = len(df)
        
        # Sample transactions
        sample_df = df.sample(n=min(num_transactions, len(df)), replace=False)
        
        # Prepare transaction data
        transactions = []
        for _, row in sample_df.iterrows():
            txn = {
                "user_id": str(row.get("user_id", "unknown")),
                "transaction_amount": float(row.get("transaction_amount", 0.0)),
                "ip_address": str(row.get("ip_address", "0.0.0.0")),
                "device_id": str(row.get("device_id", "unknown")),
                "timestamp": str(row.get("timestamp", "")),
            }
            transactions.append(txn)
        
        # Process batch
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("Sending batch request to API...")
            response = httpx.post(
                f"{API_URL}/analyze-batch",
                json=transactions,
                timeout=300.0  # 5 minute timeout for large batches
            )
            response.raise_for_status()
            result = response.json()
            
            progress_bar.progress(1.0)
            status_text.text("✅ Processing complete!")
            
            st.session_state.batch_result = result
            
        except httpx.HTTPStatusError as e:
            st.error(f"API Error: {e.response.text}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # Display batch results
    if "batch_result" in st.session_state:
        result = st.session_state.batch_result
        
        st.subheader("📊 Summary Dashboard")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Processed", result["total_processed"])
        
        with col2:
            st.metric("Fraud Detected", result["fraud_detected"], delta=None)
        
        with col3:
            st.metric("Approved", result["approved"])
        
        with col4:
            st.metric("Errors", result["errors"])
        
        # Latency statistics
        st.subheader("⏱️ Performance Metrics")
        
        latency_stats = result["latency_stats"]
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Average Latency", f"{latency_stats['avg_ms']:.0f} ms")
        
        with col2:
            st.metric("P50 Latency", f"{latency_stats['p50_ms']:.0f} ms")
        
        with col3:
            p95 = latency_stats["p95_ms"]
            st.metric("P95 Latency", f"{p95:.0f} ms")
            if p95 > 2500:
                st.warning("⚠️ P95 latency exceeds 2.5s target")
            else:
                st.success("✅ P95 latency within target")
        
        # Show individual results if available
        if result.get("results") and len(result["results"]) > 0:
            st.subheader("Individual Results")
            results_df = pd.DataFrame(result["results"])
            st.dataframe(results_df, use_container_width=True)

