import json
import sys
from gen_report import generate_pdf

def main():
    # Check if JSON file is provided as argument
    if len(sys.argv) < 2:
        print("Usage: python main.py <json_file> [output_pdf_name]")
        print("Example: python main.py 73.json report.pdf")
        sys.exit(1)
    
    json_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "report.pdf"
    
    # Load JSON data
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{json_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in '{json_file}'")
        sys.exit(1)
    
    # Prepare file_info (you may need to adjust this based on your needs)
    file_info = {
        'original_name': json_file.replace('.json', '')  # Use JSON filename as file name
    }
    
    # Generate PDF
    try:
        pdf_buffer = generate_pdf(file_info, data)
        
        # Save PDF to file
        with open(output_file, 'wb') as f:
            f.write(pdf_buffer.read())
        
        print(f"PDF report generated successfully: {output_file}")
    except Exception as e:
        print(f"Error generating PDF: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()