from anormaly_predictor import AnomalyDetector

detector = AnomalyDetector(
    model_path="model/lstm_adfa_model.keras",
    syscall_map_path="lib/linux_syscalls_x86_64_parsed.json",
    window_length=200,
    threshold=0.5
)

# result = detector.predict_from_log("logs/normal_trace.log")
result = detector.predict_from_log("logs/malware_trace.log")

print(f"Decision: {result['final_decision']}") # "Anomalous" or "Normal" => Use this to decide
print(f"Max Probability: {result['max_prob_anomaly']:.4f}")
print(f"Mean Probability: {result['mean_prob_anomaly']:.4f}")
print(f"Windows Analyzed: {result['num_windows']}")
