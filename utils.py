"""Utility functions for dataset loading and transaction handling."""
import os
import pandas as pd
import httpx
from pathlib import Path
from typing import Optional, Dict, Any
from schemas import Transaction
import config


def load_amazon_fdb(dataset_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load Amazon Fraud Dataset Benchmark.
    Tries local path first, downloads if missing.
    
    Args:
        dataset_path: Optional custom path to dataset
        
    Returns:
        DataFrame containing the dataset
    """
    path = dataset_path or config.DATASET_PATH
    
    # Try to load from local path
    if os.path.exists(path):
        print(f"Loading dataset from local path: {path}")
        return pd.read_csv(path)
    
    # Create data directory if it doesn't exist
    data_dir = Path(path).parent
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Download if not found locally
    print(f"Dataset not found locally. Downloading from {config.DATASET_URL}")
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(config.DATASET_URL)
            response.raise_for_status()
            
            # Save to local path
            with open(path, 'wb') as f:
                f.write(response.content)
            
            print(f"Dataset downloaded and saved to {path}")
            return pd.read_csv(path)
    except Exception as e:
        raise FileNotFoundError(
            f"Could not load dataset from {path} or download from {config.DATASET_URL}. "
            f"Error: {str(e)}"
        )


def sample_transaction(df: pd.DataFrame, random_state: Optional[int] = None) -> Dict[str, Any]:
    """
    Sample a random transaction from the dataset.
    
    Args:
        df: DataFrame containing transactions
        random_state: Optional random seed for reproducibility
        
    Returns:
        Dictionary representing a transaction
    """
    if df.empty:
        raise ValueError("Dataset is empty")
    
    sample = df.sample(n=1, random_state=random_state).iloc[0]
    
    # Convert to dictionary and handle missing fields
    transaction_dict = {
        "user_id": str(sample.get("user_id", "unknown")),
        "transaction_amount": float(sample.get("transaction_amount", 0.0)),
        "ip_address": str(sample.get("ip_address", "0.0.0.0")),
        "device_id": str(sample.get("device_id", "unknown")),
        "timestamp": str(sample.get("timestamp", "")),
    }
    
    # Add optional fields if they exist
    optional_fields = ["payment_method", "billing_address", "shipping_address", "product_category"]
    for field in optional_fields:
        if field in sample and pd.notna(sample[field]):
            transaction_dict[field] = str(sample[field])
    
    return transaction_dict


def validate_transaction(data: Dict[str, Any]) -> Transaction:
    """
    Validate and create a Transaction object from dictionary.
    
    Args:
        data: Dictionary containing transaction data
        
    Returns:
        Validated Transaction object
        
    Raises:
        ValidationError: If transaction data is invalid
    """
    return Transaction(**data)


def prepare_transaction_for_analysis(transaction: Transaction) -> Dict[str, Any]:
    """
    Prepare transaction data for agent analysis.
    
    Args:
        transaction: Transaction object
        
    Returns:
        Dictionary formatted for agent prompts
    """
    return {
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

