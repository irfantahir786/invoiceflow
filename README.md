# Invoice Table Extractor API

A FastAPI-based service for extracting table data from PDF invoices with GST detection capabilities.

## Features

- **Table Extraction**: Automatically detects and extracts tables from PDF invoices using `pdfplumber`
- **GST Invoice Detection**: Identifies if the document is a GST-compliant invoice by detecting:
  - GSTIN patterns (15-character alphanumeric format)
  - GST-related keywords (CGST, SGST, IGST)
- **Structured JSON Output**: Returns clean, structured data with headers and rows
- **Metadata**: Includes page count, table count, and row statistics

## Installation

```bash
pip install -r requirements.txt
```

Requirements include:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `python-multipart` - File upload support
- `pdfplumber` - PDF table extraction
- `pandas` - Data manipulation

## Quick Start

### 1. Start the Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Or run directly:

```bash
python main.py
```

### 2. Access API Documentation

Open your browser and visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. Test Endpoints

#### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{"status": "healthy"}
```

#### Upload Invoice for Extraction

```bash
curl -X POST "http://localhost:8000/extract" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_invoice.pdf"
```

Or using Python:

```python
import requests

url = "http://localhost:8000/extract"
files = {'file': ('invoice.pdf', open('invoice.pdf', 'rb'), 'application/pdf')}
response = requests.post(url, files=files)
print(response.json())
```

## API Endpoints

### `POST /extract`

Upload a PDF invoice to extract table data.

**Parameters:**
- `file` (multipart/form-data): PDF file to process

**Response Format:**

```json
{
  "is_gst_invoice": true,
  "filename": "sample_invoice.pdf",
  "tables": [
    {
      "table_index": 0,
      "page_number": 1,
      "headers": ["Item No", "Description", "Qty", "Rate", "Amount"],
      "rows": [
        {
          "Item No": "1",
          "Description": "Product A",
          "Qty": "10",
          "Rate": "100.00",
          "Amount": "1000.00"
        }
      ],
      "row_count": 5,
      "column_count": 5
    }
  ],
  "metadata": {
    "total_pages": 1,
    "total_tables": 2,
    "total_rows": 9
  }
}
```

### `GET /`

Root endpoint with API information.

### `GET /health`

Health check endpoint.

## Testing

Run the included test script to generate a sample invoice and test the API:

```bash
python test_api.py
```

This will:
1. Create a sample GST invoice PDF with tables
2. Send it to the extraction endpoint
3. Display the extracted results
4. Save the full JSON response to `extraction_result.json`

## How It Works

1. **PDF Processing**: Uses `pdfplumber` to extract tables based on visual lines and grid structures
2. **Header Detection**: Automatically identifies table headers using keyword matching
3. **Data Cleaning**: Removes empty rows/columns and normalizes whitespace
4. **GST Detection**: Scans text for GSTIN patterns and tax-related keywords
5. **JSON Serialization**: Converts extracted data to structured JSON format

## Example Output

The API successfully extracts:
- **Item Tables**: Product descriptions, quantities, rates, amounts
- **Tax Tables**: CGST, SGST, IGST breakdowns
- **Summary Tables**: Subtotals, tax totals, grand totals

## Usage as a Library

You can also use the extractor directly in your Python code:

```python
from invoice_extractor import InvoiceTableExtractor

# Create extractor instance
extractor = InvoiceTableExtractor()

# Extract data from PDF
result = extractor.extract_all("path/to/invoice.pdf")

# Check if GST invoice
print(f"Is GST Invoice: {result['is_gst_invoice']}")

# Access tables
for table in result['tables']:
    print(f"Table on page {table['page_number']}")
    print(f"Headers: {table['headers']}")
    print(f"Rows: {table['rows']}")
```

## Limitations

- Works best with text-based PDFs that have clear table structures
- Scanned/image-based PDFs may require OCR preprocessing
- Complex table layouts might need additional customization

## For Scanned PDFs

For image-based PDFs, consider adding OCR support:

```bash
pip install pytesseract pdf2image
```

Then modify the extractor to use OCR before table extraction.

## License

MIT License
