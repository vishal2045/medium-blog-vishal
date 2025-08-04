"""
PTB-XL Data Loader for STEMI Detection
Loads and preprocesses PTB-XL dataset for ST-elevation MI classification
"""

import os
import numpy as np
import pandas as pd
import wfdb
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import tensorflow as tf
from typing import Tuple, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PTBXLLoader:
    """PTB-XL dataset loader and preprocessor"""
    
    def __init__(self, data_path: str = "ptb-xl/", sampling_rate: int = 100):
        """
        Initialize PTB-XL loader
        
        Args:
            data_path: Path to PTB-XL dataset directory
            sampling_rate: Target sampling rate (PTB-XL is already 100Hz)
        """
        self.data_path = data_path
        self.sampling_rate = sampling_rate
        self.sequence_length = 1000  # 10 seconds at 100Hz
        self.n_leads = 12
        
        # Load metadata
        self.load_metadata()
    
    def load_metadata(self):
        """Load PTB-XL metadata files"""
        try:
            # Load database metadata
            self.Y = pd.read_csv(os.path.join(self.data_path, 'ptbxl_database.csv'), index_col='ecg_id')
            
            # Load diagnostic statements
            self.scp_statements = pd.read_csv(os.path.join(self.data_path, 'scp_statements.csv'), index_col=0)
            
            logger.info(f"Loaded {len(self.Y)} ECG records")
            logger.info(f"Loaded {len(self.scp_statements)} SCP statements")
            
        except FileNotFoundError as e:
            logger.error(f"PTB-XL dataset not found at {self.data_path}")
            logger.error("Please download PTB-XL dataset from PhysioNet")
            raise e
    
    def create_stemi_labels(self) -> pd.Series:
        """
        Create STEMI vs non-MI labels based on diagnostic superclass and SCP codes
        
        Returns:
            Binary labels: 1 for STEMI, 0 for non-MI
        """
        # Parse diagnostic information
        def parse_scp_codes(scp_codes_str):
            if pd.isna(scp_codes_str):
                return {}
            return eval(scp_codes_str)
        
        # Extract SCP codes for each record
        scp_codes = self.Y['scp_codes'].apply(parse_scp_codes)
        
        # Check for ST-elevation MI (SCP code 313) and MI superclass
        labels = []
        
        for idx, row in self.Y.iterrows():
            codes = parse_scp_codes(row['scp_codes'])
            superclass = eval(row['diagnostic_superclass']) if pd.notna(row['diagnostic_superclass']) else {}
            
            # STEMI: Must have MI superclass AND SCP code 313 (ST elevation)
            has_mi = 'MI' in superclass
            has_st_elevation = 313 in codes  # ST elevation
            
            if has_mi and has_st_elevation:
                labels.append(1)  # STEMI
            elif not has_mi:
                labels.append(0)  # Non-MI (normal or other conditions)
            else:
                # Other MI types - exclude from binary classification
                labels.append(-1)  # Will be filtered out
        
        label_series = pd.Series(labels, index=self.Y.index)
        
        # Log label distribution
        logger.info(f"Label distribution:")
        logger.info(f"STEMI (1): {sum(label_series == 1)}")
        logger.info(f"Non-MI (0): {sum(label_series == 0)}")
        logger.info(f"Other MI (-1): {sum(label_series == -1)}")
        
        return label_series
    
    def load_ecg_data(self, ecg_id: int) -> np.ndarray:
        """
        Load single ECG record
        
        Args:
            ecg_id: ECG record ID
            
        Returns:
            ECG data as numpy array (sequence_length, n_leads)
        """
        # Construct file path
        folder = f"{ecg_id // 1000:02d}000"
        file_path = os.path.join(self.data_path, "records100", folder, str(ecg_id))
        
        try:
            # Load ECG record
            record = wfdb.rdsamp(file_path)
            ecg_data = record[0]  # Signal data
            
            # Ensure correct shape and length
            if ecg_data.shape[1] != self.n_leads:
                logger.warning(f"ECG {ecg_id} has {ecg_data.shape[1]} leads, expected {self.n_leads}")
                return None
            
            # Pad or truncate to sequence_length
            if len(ecg_data) < self.sequence_length:
                # Pad with zeros
                padding = self.sequence_length - len(ecg_data)
                ecg_data = np.pad(ecg_data, ((0, padding), (0, 0)), mode='constant')
            elif len(ecg_data) > self.sequence_length:
                # Truncate to first 10 seconds
                ecg_data = ecg_data[:self.sequence_length]
            
            return ecg_data.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Error loading ECG {ecg_id}: {e}")
            return None
    
    def preprocess_ecg(self, ecg_data: np.ndarray) -> np.ndarray:
        """
        Preprocess ECG data with z-score normalization per lead
        
        Args:
            ecg_data: Raw ECG data (sequence_length, n_leads)
            
        Returns:
            Preprocessed ECG data
        """
        # Z-score normalization per lead
        preprocessed = np.zeros_like(ecg_data)
        
        for lead in range(self.n_leads):
            lead_data = ecg_data[:, lead]
            mean = np.mean(lead_data)
            std = np.std(lead_data)
            
            if std > 0:
                preprocessed[:, lead] = (lead_data - mean) / std
            else:
                preprocessed[:, lead] = lead_data - mean
        
        return preprocessed
    
    def load_dataset(self, test_size: float = 0.2, val_size: float = 0.1) -> Tuple[Dict, Dict]:
        """
        Load complete dataset with train/val/test splits
        
        Args:
            test_size: Fraction for test set
            val_size: Fraction of remaining data for validation
            
        Returns:
            Tuple of (data_dict, metadata_dict)
        """
        # Create labels
        labels = self.create_stemi_labels()
        
        # Filter out other MI types (keep only STEMI vs non-MI)
        valid_indices = labels[labels != -1].index
        filtered_labels = labels[valid_indices]
        
        logger.info(f"Using {len(valid_indices)} records for binary classification")
        
        # Load ECG data
        X = []
        y = []
        valid_ids = []
        
        logger.info("Loading ECG data...")
        for ecg_id in valid_indices:
            ecg_data = self.load_ecg_data(ecg_id)
            
            if ecg_data is not None:
                # Preprocess
                ecg_preprocessed = self.preprocess_ecg(ecg_data)
                
                X.append(ecg_preprocessed)
                y.append(filtered_labels[ecg_id])
                valid_ids.append(ecg_id)
        
        X = np.array(X)
        y = np.array(y)
        
        logger.info(f"Loaded {len(X)} valid ECG records")
        logger.info(f"Data shape: {X.shape}")
        logger.info(f"Final label distribution - STEMI: {sum(y)}, Non-MI: {len(y) - sum(y)}")
        
        # Train/test split
        X_temp, X_test, y_temp, y_test, ids_temp, ids_test = train_test_split(
            X, y, valid_ids, test_size=test_size, stratify=y, random_state=42
        )
        
        # Train/val split
        X_train, X_val, y_train, y_val, ids_train, ids_val = train_test_split(
            X_temp, y_temp, ids_temp, test_size=val_size/(1-test_size), stratify=y_temp, random_state=42
        )
        
        data_dict = {
            'X_train': X_train,
            'X_val': X_val,
            'X_test': X_test,
            'y_train': y_train,
            'y_val': y_val,
            'y_test': y_test
        }
        
        metadata_dict = {
            'ids_train': ids_train,
            'ids_val': ids_val,
            'ids_test': ids_test,
            'n_samples': len(X),
            'sequence_length': self.sequence_length,
            'n_leads': self.n_leads,
            'sampling_rate': self.sampling_rate
        }
        
        return data_dict, metadata_dict

def download_ptbxl(data_path: str = "ptb-xl/"):
    """
    Helper function to download PTB-XL dataset
    Note: This requires manual download from PhysioNet
    """
    logger.info("PTB-XL dataset must be downloaded manually from PhysioNet:")
    logger.info("https://physionet.org/content/ptb-xl/1.0.3/")
    logger.info(f"Extract to: {data_path}")
    logger.info("Required files:")
    logger.info("- ptbxl_database.csv")
    logger.info("- scp_statements.csv")
    logger.info("- records100/ directory")

if __name__ == "__main__":
    # Example usage
    loader = PTBXLLoader("ptb-xl/")
    data, metadata = loader.load_dataset()
    
    print("Dataset loaded successfully!")
    print(f"Training samples: {len(data['X_train'])}")
    print(f"Validation samples: {len(data['X_val'])}")
    print(f"Test samples: {len(data['X_test'])}")