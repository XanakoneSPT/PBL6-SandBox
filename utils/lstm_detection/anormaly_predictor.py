#!/usr/bin/env python3
"""
Syscall Anomaly Detection Pipeline
Loads syscall mapping, tokenizes strace logs, and predicts anomalies using LSTM model.
"""

import re
import json
import numpy as np
from pathlib import Path
from tensorflow import keras
from typing import Dict, List, Optional


class AnomalyDetector:
    """Detect anomalies in system call sequences using trained LSTM model."""
    
    def __init__(
        self,
        model_path: str = "model/lstm_adfa_model.keras",
        syscall_map_path: str = "lib/linux_syscalls_x86_64_parsed.json",
        window_length: int = 200,
        pad_short: bool = True,
        threshold: float = 0.5,
        unknown_token: Optional[int] = None
    ):
        """
        Initialize anomaly detection pipeline.
        
        Args:
            model_path: Path to trained Keras model
            syscall_map_path: Path to syscall name-to-number mapping JSON
            window_length: Sliding window size for sequence analysis
            pad_short: Whether to pad sequences shorter than window_length
            threshold: Probability threshold for anomaly classification
            unknown_token: Token ID for unmapped syscalls (None to skip)
        """
        self.window_length = window_length
        self.pad_short = pad_short
        self.threshold = threshold
        self.unknown_token = unknown_token
        
        self.model = self._load_model(model_path)
        self.syscall_map = self._load_syscall_map(syscall_map_path)
    
    def _load_model(self, model_path: str) -> keras.Model:
        """Load trained Keras model."""
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        return keras.models.load_model(model_path, compile=False)
    
    def _load_syscall_map(self, json_path: str) -> Dict[str, int]:
        """
        Load syscall name-to-number mapping from JSON.
        
        Supports two formats:
        1. Dict: {"read": 0, "write": 1}
        2. List: [{"name": "read", "nr": 0}, ...]
        """
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"Syscall map not found: {json_path}")
        
        with path.open() as f:
            data = json.load(f)
        
        mapping = {}
        
        if isinstance(data, dict):
            mapping = {str(k): int(v) for k, v in data.items() if self._is_valid_int(v)}
        
        elif isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                
                nr = item.get("nr") or item.get("number") or item.get("num")
                name = item.get("name") or item.get("syscall") or item.get("call")
                
                if name and nr is not None and self._is_valid_int(nr):
                    mapping[str(name)] = int(nr)
        
        if not mapping:
            raise ValueError(f"No valid syscall mappings found in {json_path}")
        
        return mapping
    
    @staticmethod
    def _is_valid_int(value) -> bool:
        """Check if value can be converted to int."""
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def _parse_syscall_name(line: str) -> Optional[str]:
        """Extract syscall name from strace log line."""
        match = re.search(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", line)
        return match.group(1) if match else None
    
    def tokenize_log(self, log_path: str) -> List[int]:
        """
        Tokenize strace log file into syscall number sequence.
        
        Args:
            log_path: Path to strace log file
            
        Returns:
            List of syscall numbers [9, 4, 2, ...]
        """
        path = Path(log_path)
        if not path.exists():
            raise FileNotFoundError(f"Log file not found: {log_path}")
        
        seq = []
        
        with path.open(errors="replace") as f:
            for line in f:
                name = self._parse_syscall_name(line.strip())
                if not name:
                    continue
                
                nr = self.syscall_map.get(name)
                if nr is not None:
                    seq.append(nr)
                elif self.unknown_token is not None:
                    seq.append(self.unknown_token)
        
        return seq
    
    def _create_windows(self, seq: List[int]) -> np.ndarray:
        """
        Convert syscall sequence to sliding windows.
        
        Args:
            seq: Syscall number sequence
            
        Returns:
            Array of shape (num_windows, window_length)
        """
        n = len(seq)
        windows = []
        
        if n >= self.window_length:
            for i in range(n - self.window_length + 1):
                windows.append(seq[i:i + self.window_length])
        
        elif self.pad_short:
            padded = seq + [0] * (self.window_length - n)
            windows.append(padded)
        
        if not windows:
            raise ValueError(
                f"Sequence too short ({n} < {self.window_length}) and pad_short=False"
            )
        
        return np.array(windows, dtype=np.float32)
    
    def predict_from_log(self, log_path: str) -> dict:
        """
        Full pipeline: log file → anomaly detection result.
        
        Args:
            log_path: Path to strace log file
            
        Returns:
            Dictionary containing:
                - syscall_seq: Tokenized sequence
                - num_windows: Number of sliding windows analyzed
                - per_window: Per-window anomaly probabilities
                - max_prob_anomaly: Highest anomaly probability
                - mean_prob_anomaly: Average anomaly probability
                - final_decision: "anomalous" or "normal"
                - threshold: Detection threshold used
        """
        seq = self.tokenize_log(log_path)
        
        if not seq:
            raise ValueError(f"No valid syscalls found in {log_path}")
        
        windows = self._create_windows(seq)
        X = np.expand_dims(windows, axis=-1)
        
        preds = self.model.predict(X, verbose=0)
        probs = preds.reshape(-1)
        
        max_prob = float(np.max(probs))
        mean_prob = float(np.mean(probs))
        is_anomaly = max_prob > self.threshold
        
        return {
            "syscall_seq": seq,
            "num_windows": len(probs),
            "per_window": [
                {"window_index": i, "prob_anomaly": float(p)} 
                for i, p in enumerate(probs)
            ],
            "max_prob_anomaly": max_prob,
            "mean_prob_anomaly": mean_prob,
            "final_decision": "anomalous" if is_anomaly else "normal",
            "threshold": self.threshold
        }