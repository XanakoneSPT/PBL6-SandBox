document.addEventListener('DOMContentLoaded', function() {
    // Tab functionality for results
    const resultTabBtns = document.querySelectorAll('.results-tabs .tab-btn');
    const resultTabPanes = document.querySelectorAll('.tab-pane');

    resultTabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.getAttribute('data-tab');
            
            // Update active tab button
            resultTabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Show corresponding tab content
            resultTabPanes.forEach(pane => {
                pane.classList.remove('active');
            });
            document.getElementById(`${tabName}-tab`).classList.add('active');
        });
    });

    // Simulate analysis progress
    function simulateAnalysis() {
        const progressBar = document.getElementById('bar');
        const progressText = document.getElementById('progress-text');
        const statusText = document.getElementById('status');
        const resultsSection = document.getElementById('results-section');
        const downloadBtn = document.getElementById('download-report');
        
        let progress = 0;
        const steps = [
            { progress: 15, message: "Extracting file metadata..." },
            { progress: 30, message: "Running signature analysis..." },
            { progress: 50, message: "Checking against threat databases..." },
            { progress: 70, message: "Performing behavioral analysis..." },
            { progress: 85, message: "Cross-referencing with security engines..." },
            { progress: 100, message: "Analysis complete!" }
        ];
        
        let currentStep = 0;
        
        const interval = setInterval(() => {
            if (currentStep < steps.length) {
                const step = steps[currentStep];
                progress = step.progress;
                
                progressBar.value = progress;
                progressText.textContent = progress + '%';
                statusText.innerHTML = `<span class="scanning-animation"></span>${step.message}`;
                
                if (progress === 100) {
                    clearInterval(interval);
                    statusText.className = 'status-indicator complete';
                    statusText.innerHTML = '<i class="fas fa-check-circle"></i>Analysis complete!';
                    
                    // Show results after a brief delay
                    setTimeout(() => {
                        resultsSection.style.display = 'block';
                        downloadBtn.style.display = 'inline-flex';
                        populateResults();
                    }, 1000);
                }
                
                currentStep++;
            } else {
                clearInterval(interval);
            }
        }, 2000); // Update every 2 seconds
    }

    // Populate sample results
    function populateResults() {
        const summaryGrid = document.getElementById('summary-grid');
        const detailsContent = document.getElementById('details-content');
        const rawOutput = document.getElementById('output');

        // Sample summary data
        summaryGrid.innerHTML = `
            <div class="summary-card">
                <h5><i class="fas fa-shield-alt"></i>Threat Level</h5>
                <p><span class="threat-level safe">Safe</span></p>
                <p>No threats detected by any security engines.</p>
            </div>
            <div class="summary-card">
                <h5><i class="fas fa-search"></i>Detection Rate</h5>
                <p><strong>0/74</strong> security engines flagged this file</p>
                <p>Scanned with 74 antivirus engines.</p>
            </div>
            <div class="summary-card">
                <h5><i class="fas fa-file-alt"></i>File Info</h5>
                <p><strong>Type:</strong> Executable</p>
                <p><strong>Size:</strong> 2.4 MB</p>
                <p><strong>MD5:</strong> d41d8cd98f00b204...</p>
            </div>
            <div class="summary-card">
                <h5><i class="fas fa-clock"></i>Analysis Time</h5>
                <p><strong>Started:</strong> ${new Date().toLocaleString()}</p>
                <p><strong>Duration:</strong> 12 seconds</p>
            </div>
        `;

        // Sample detailed analysis
        detailsContent.innerHTML = `
            <div class="detail-section">
                <h6>File Properties</h6>
                <ul class="detail-list">
                    <li><span>File name</span><strong>{{ file.original_name }}</strong></li>
                    <li><span>File size</span><strong>2.4 MB (2,457,600 bytes)</strong></li>
                    <li><span>File type</span><strong>PE32 executable</strong></li>
                    <li><span>Creation time</span><strong>${new Date().toLocaleString()}</strong></li>
                </ul>
            </div>
            <div class="detail-section">
                <h6>Hash Values</h6>
                <ul class="detail-list">
                    <li><span>MD5</span><strong>d41d8cd98f00b204e9800998ecf8427e</strong></li>
                    <li><span>SHA1</span><strong>da39a3ee5e6b4b0d3255bfef95601890afd80709</strong></li>
                    <li><span>SHA256</span><strong>e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855</strong></li>
                </ul>
            </div>
            <div class="detail-section">
                <h6>Security Analysis</h6>
                <ul class="detail-list">
                    <li><span>Malware detected</span><strong style="color: #28a745;">No</strong></li>
                    <li><span>Suspicious behavior</span><strong style="color: #28a745;">None detected</strong></li>
                    <li><span>Network connections</span><strong>0 detected</strong></li>
                    <li><span>Registry modifications</span><strong>0 detected</strong></li>
                </ul>
            </div>
        `;

        // Sample raw output
        rawOutput.textContent = `MalSanbox Analysis Report
============================

File Information:
- Name: {{ file.original_name }}
- Size: 2,457,600 bytes
- Type: PE32 executable (GUI) Intel 80386, for MS Windows
- MD5: d41d8cd98f00b204e9800998ecf8427e
- SHA1: da39a3ee5e6b4b0d3255bfef95601890afd80709
- SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855

Scan Results:
=============
Total engines: 74
Detections: 0
Clean: 74

Engine Results:
- Avast: Clean
- AVG: Clean  
- Bitdefender: Clean
- ClamAV: Clean
- ESET-NOD32: Clean
- F-Secure: Clean
- Kaspersky: Clean
- McAfee: Clean
- Microsoft: Clean
- Norton: Clean
- Sophos: Clean
- Symantec: Clean
- Trend Micro: Clean
- Windows Defender: Clean
[... and 60 more engines ...]

Analysis Complete: ${new Date().toISOString()}`;
    }

    // Download report functionality
    document.getElementById('download-report').addEventListener('click', function() {
        const fileName = '{{ file.original_name }}'.replace(/[^a-zA-Z0-9]/g, '_');
        const reportContent = document.getElementById('output').textContent;
        
        const blob = new Blob([reportContent], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `virustotal_report_${fileName}.txt`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    });

    // Start the analysis simulation
    simulateAnalysis();
});