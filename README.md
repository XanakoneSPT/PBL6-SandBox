# Syscall Anomaly Detection Pipeline

Hệ thống phát hiện bất thường trong chuỗi system call sử dụng mô hình LSTM.

---

## 📋 Mục lục

1. [Tổng quan](#-tổng-quan)
2. [Cài đặt](#-cài-đặt)
3. [Cấu trúc thư mục](#-cấu-trúc-thư-mục)
4. [Hướng dẫn sử dụng](#-hướng-dẫn-sử-dụng)
5. [API Reference](#-api-reference)
6. [Cấu hình](#️-cấu-hình)
8. [References](#-references)

---

## 🎯 Tổng quan

Pipeline này phân tích log strace để phát hiện hành vi bất thường của process thông qua:

1. **Tokenization**: Chuyển syscall names → syscall numbers
2. **Windowing**: Chia sequence thành sliding windows (mặc định 200 syscalls)
3. **Prediction**: Sử dụng LSTM model để tính xác suất anomaly
4. **Detection**: So sánh với threshold để quyết định

### Nguyên lý hoạt động

```
strace.log → [read, write, open] → [0, 1, 2] → Windows → LSTM → Anomaly Score
```

---

## 🚀 Cài đặt

### Requirements

```bash
pip install tensorflow numpy
```
hoặc 
``` bash
pip install -r requirements.txt
```

### Dependencies

- Python >= 3.8
- TensorFlow >= 2.10
- NumPy >= 1.21

---

## 📁 Cấu trúc thư mục

```
project/
├── model/
│   └── lstm_adfa_model.keras          # Trained model
├── lib/
│   └── linux_syscalls_x86_64_parsed.json  # Syscall mapping
├── logs/
│   ├── normal_trace.log               # Normal logs
│   └── malware_trace.log              # Anomalous logs
└── syscall_pipeline.py                # Main code
```

---

## 📖 Hướng dẫn sử dụng

### Basic Usage

```python
from syscall_pipeline import AnomalyDetector

# Khởi tạo detector
detector = AnomalyDetector(
    model_path="model/lstm_adfa_model.keras",
    syscall_map_path="lib/linux_syscalls_x86_64_parsed.json",
    threshold=0.5
)

# Phân tích log
result = detector.predict_from_log("logs/sample_trace.log")

# Kết quả
print(f"Decision: {result['final_decision']}")
print(f"Max Probability: {result['max_prob_anomaly']:.4f}")
```

### Advanced Usage

```python
# Cấu hình chi tiết
detector = AnomalyDetector(
    model_path="model/lstm_adfa_model.keras",
    syscall_map_path="lib/linux_syscalls_x86_64_parsed.json",
    window_length=200,        # Kích thước sliding window
    pad_short=True,           # Pad sequence ngắn
    threshold=0.5,            # Ngưỡng phát hiện
    unknown_token=999         # Token cho syscall không rõ
)

result = detector.predict_from_log("logs/trace.log")

# Phân tích chi tiết từng window
for window in result['per_window']:
    if window['prob_anomaly'] > 0.7:
        print(f"Window {window['window_index']}: {window['prob_anomaly']:.4f}")
```

### Batch Processing

```python
from pathlib import Path

detector = AnomalyDetector()
log_dir = Path("logs/")

for log_file in log_dir.glob("*.log"):
    try:
        result = detector.predict_from_log(str(log_file))
        print(f"{log_file.name}: {result['final_decision']}")
    except Exception as e:
        print(f"Error processing {log_file.name}: {e}")
```

---

## 🔧 API Reference

### Class: `AnomalyDetector`

#### Constructor

```python
AnomalyDetector(
    model_path: str = "model/lstm_adfa_model.keras",
    syscall_map_path: str = "lib/linux_syscalls_x86_64_parsed.json",
    window_length: int = 200,
    pad_short: bool = True,
    threshold: float = 0.5,
    unknown_token: Optional[int] = None
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_path` | str | "model/lstm_adfa_model.keras" | Đường dẫn model Keras |
| `syscall_map_path` | str | "lib/linux_syscalls_x86_64_parsed.json" | Đường dẫn syscall mapping |
| `window_length` | int | 200 | Kích thước sliding window |
| `pad_short` | bool | True | Pad sequence ngắn hơn window_length |
| `threshold` | float | 0.5 | Ngưỡng xác suất để phân loại anomaly |
| `unknown_token` | int/None | None | Token cho syscall không có trong map |

#### Methods

##### `predict_from_log(log_path: str) -> dict`

Phân tích file log và trả về kết quả phát hiện anomaly.

**Returns:**

```python
{
    "syscall_seq": [0, 1, 2, ...],           # Sequence đã tokenize
    "num_windows": 150,                       # Số windows phân tích
    "per_window": [                           # Chi tiết từng window
        {"window_index": 0, "prob_anomaly": 0.23},
        {"window_index": 1, "prob_anomaly": 0.87},
        ...
    ],
    "max_prob_anomaly": 0.87,                 # Xác suất cao nhất
    "mean_prob_anomaly": 0.45,                # Xác suất trung bình
    "final_decision": "anomalous",            # "anomalous" hoặc "normal"
    "threshold": 0.5                          # Ngưỡng sử dụng
}
```

##### `tokenize_log(log_path: str) -> List[int]`

Chuyển strace log thành sequence số.

**Returns:** `[0, 1, 2, 5, 1, ...]`

---

## ⚙️ Cấu hình

### Threshold Tuning

Điều chỉnh `threshold` để cân bằng giữa false positive và false negative:

```python
# Nghiêm ngặt hơn (ít false positive, nhiều false negative)
detector = AnomalyDetector(threshold=0.7)

# Nhạy cảm hơn (nhiều false positive, ít false negative)
detector = AnomalyDetector(threshold=0.5)
```

### Window Length

```python
# Sequence ngắn (real-time detection)
detector = AnomalyDetector(window_length=100)

# Sequence dài (phân tích sâu hơn)
detector = AnomalyDetector(window_length=300)
```

### Unknown Syscalls

```python
# Bỏ qua syscalls không rõ
detector = AnomalyDetector(unknown_token=None)

# Map syscalls không rõ thành token 999
detector = AnomalyDetector(unknown_token=999)
```

## 🔗 References

- [ADFA-LD Dataset](https://www.unsw.adfa.edu.au/australian-centre-for-cyber-security/cybersecurity/ADFA-IDS-Datasets/)
- [Strace Documentation](https://man7.org/linux/man-pages/man1/strace.1.html)
- [Linux System Calls](https://man7.org/linux/man-pages/man2/syscalls.2.html)

---

**Version:** 1.0.0  
**Last Updated:** November 2025