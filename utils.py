"""Utility functions for dataset loading and transaction handling."""
import os
import pandas as pd
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from schemas import Transaction
import config


def load_ieee_fraud_detection(
    transaction_path: Optional[str] = None,
    identity_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Load IEEE Fraud Detection dataset by merging transaction and identity files.
    
    Args:
        transaction_path: Path to train_transaction.csv (supports @data/ alias)
        identity_path: Path to train_identity.csv (supports @data/ alias)
        
    Returns:
        Merged DataFrame containing transaction and identity data
    """
    # Default paths using @data/ alias
    default_transaction = "@data/ieee-fraud-detection/train_transaction.csv"
    default_identity = "@data/ieee-fraud-detection/train_identity.csv"
    
    trans_path = config.resolve_data_path(transaction_path or default_transaction)
    ident_path = config.resolve_data_path(identity_path or default_identity)
    
    if not os.path.exists(trans_path):
        raise FileNotFoundError(f"Transaction file not found: {trans_path}")
    
    print(f"Loading IEEE transaction data from: {trans_path}")
    df_trans = pd.read_csv(trans_path)
    
    if os.path.exists(ident_path):
        print(f"Loading IEEE identity data from: {ident_path}")
        df_identity = pd.read_csv(ident_path)
        # Merge on TransactionID (left join to keep all transactions)
        df = df_trans.merge(df_identity, on="TransactionID", how="left")
        print(f"Merged dataset: {len(df)} rows, {len(df.columns)} columns")
    else:
        print(f"Identity file not found: {ident_path}. Using transaction data only.")
        df = df_trans
    
    return df


def map_ieee_to_transaction(row: pd.Series) -> Dict[str, Any]:
    """
    Map IEEE fraud detection dataset row to Transaction schema.
    
    Args:
        row: Pandas Series representing a single transaction from IEEE dataset
        
    Returns:
        Dictionary matching Transaction schema
    """
    # Convert TransactionDT (days since epoch) to ISO timestamp
    # IEEE TransactionDT is days since 2017-12-01 00:00:00
    base_date = datetime(2017, 12, 1)
    if pd.notna(row.get("TransactionDT")):
        try:
            transaction_dt = float(row["TransactionDT"])
            # Validate that the date will be within reasonable range
            # Python datetime supports years 1-9999, so limit to reasonable range
            # Max days from 2017-12-01 to 9999-12-31 is approximately 2,914,000 days
            # But we'll be more conservative and limit to ~100 years (36,500 days)
            max_days = 36500  # ~100 years
            min_days = -365   # Allow 1 year before base date
            
            if transaction_dt > max_days or transaction_dt < min_days:
                # If out of range, use current time as fallback
                timestamp = datetime.utcnow().isoformat() + "Z"
            else:
                transaction_date = base_date + timedelta(days=int(transaction_dt))
                # Additional check: ensure the resulting date is valid
                if transaction_date.year > 9999 or transaction_date.year < 1:
                    timestamp = datetime.utcnow().isoformat() + "Z"
                else:
                    timestamp = transaction_date.isoformat() + "Z"
        except (ValueError, OverflowError, OSError) as e:
            # Handle any date conversion errors (including out of range)
            timestamp = datetime.utcnow().isoformat() + "Z"
    else:
        timestamp = datetime.utcnow().isoformat() + "Z"
    
    # Map fields - IEEE dataset doesn't have IP addresses, so derive from addr1/addr2
    addr1 = row.get("addr1")
    addr2 = row.get("addr2")
    if pd.notna(addr1):
        # Derive IP-like address from addr1/addr2 for compatibility
        ip_octet3 = int(float(addr1)) % 256 if pd.notna(addr1) else 0
        ip_octet4 = int(float(addr2)) % 256 if pd.notna(addr2) else 0
        ip_address = f"192.168.{ip_octet3}.{ip_octet4}"
    else:
        ip_address = "0.0.0.0"
    
    # Device ID from DeviceInfo or DeviceType (from identity table)
    device_id = "unknown"
    if pd.notna(row.get("DeviceInfo")):
        device_id = str(row["DeviceInfo"])
    elif pd.notna(row.get("DeviceType")):
        device_id = str(row["DeviceType"])
    
    transaction_dict = {
        "user_id": str(row.get("TransactionID", "unknown")),
        "transaction_amount": float(row.get("TransactionAmt", 0.0)),
        "ip_address": ip_address,
        "device_id": device_id,
        "timestamp": timestamp,
    }
    
    # Add optional fields
    if pd.notna(row.get("card4")):
        transaction_dict["payment_method"] = str(row["card4"])
    
    if pd.notna(addr1):
        transaction_dict["billing_address"] = f"addr_{int(float(addr1))}"
    
    if pd.notna(row.get("ProductCD")):
        transaction_dict["product_category"] = str(row["ProductCD"])
    
    return transaction_dict


def is_ieee_format(df: pd.DataFrame) -> bool:
    """
    Check if DataFrame is in IEEE fraud detection format.
    
    Args:
        df: DataFrame to check
        
    Returns:
        True if DataFrame appears to be IEEE format
    """
    ieee_indicators = ["TransactionID", "TransactionDT", "TransactionAmt", "isFraud"]
    return all(col in df.columns for col in ieee_indicators)


def sample_transaction(df: pd.DataFrame, random_state: Optional[int] = None) -> Dict[str, Any]:
    """
    Sample a random transaction from the IEEE Fraud Detection dataset.
    
    Args:
        df: DataFrame containing IEEE transactions
        random_state: Optional random seed for reproducibility
        
    Returns:
        Dictionary representing a transaction matching Transaction schema
    """
    if df.empty:
        raise ValueError("Dataset is empty")
    
    sample = df.sample(n=1, random_state=random_state).iloc[0]
    
    # Convert IEEE format to Transaction schema
    return map_ieee_to_transaction(sample)


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

