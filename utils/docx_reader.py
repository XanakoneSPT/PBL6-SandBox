import zipfile
import xml.etree.ElementTree as ET
import sys
import glob
import os

def read_docx(file_path):
    try:
        with zipfile.ZipFile(file_path) as z:
            xml_content = z.read('word/document.xml')
        
        tree = ET.fromstring(xml_content)
        
        # Word stores text in w:t tags. 
        # The namespace map is often needed, but we can search by tag names ignoring namespace for simplicity 
        # or use the full namespace URI. 
        # The namespace for w is usually http://schemas.openxmlformats.org/wordprocessingml/2006/main
        
        namespace = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        text_parts = []
        
        # Find all <w:t> tags
        for t in tree.iter():
            if t.tag.endswith('}t'): # primitive check for w:t namespaced tag
                if t.text:
                    text_parts.append(t.text)
                    
        full_text = '\n'.join(text_parts)
        return full_text
        
    except Exception as e:
        return f"Error reading DOCX: {str(e)}"

def main():
    # Find the docx file if not provided
    if len(sys.argv) > 1:
        docx_file = sys.argv[1]
    else:
        files = glob.glob("*.docx")
        if not files:
            print("No DOCX found.")
            return
        docx_file = files[0]
        
    print(f"Reading {docx_file}...")
    content = read_docx(docx_file)
    
    # Print a summary/sample of the content
    print("="*50)
    print("CONTENT PREVIEW (First 2000 chars):")
    print("="*50)
    print(content[:2000])
    
    # Keyword search
    keywords = ["Sandbox", "LSTM", "Yara", "Behavior", "Strace", "Malware", "Supervisor", "Monitor", "Cuckoo", "Static", "Dynamic"]
    print("\n" + "="*50)
    print("KEYWORD ANALYSIS:")
    print("="*50)
    
    lower_content = content.lower()
    for k in keywords:
        count = lower_content.count(k.lower())
        print(f"'{k}': Found {count} times")

    # Save to a temp file for the agent to read if needed
    with open("docx_content_dump.txt", "w", encoding="utf-8") as f:
        f.write(content)
        
if __name__ == "__main__":
    main()
