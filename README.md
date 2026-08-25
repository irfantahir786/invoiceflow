# PDF Invoice Data Extractor

A Python tool for extracting structured data from PDF invoices, with special support for Indian GST invoices.

## Features

- **GST Invoice Detection**: Automatically detects if an invoice is a GST-compliant invoice
- **Seller Information Extraction**: 
  - Business name
  - Address
  - GSTIN (GST Identification Number)
  - PAN (Permanent Account Number)
  - Email and phone
  - State and state code
- **Buyer Information Extraction**:
  - Customer name
  - Address
  - GSTIN
  - State
- **Invoice Details**:
  - Invoice number
  - Invoice date
  - Due date
- **Line Items**:
  - Description
  - Quantity
  - Unit price
  - Amount
  - GST rate
- **Totals**:
  - Subtotal
  - Taxable value
  - CGST, SGST, IGST breakdown
  - Grand total

## Requirements

```bash
pip install pdfminer.six
```

## Usage

### Command Line

```bash
python pdf_invoice_extractor.py path/to/invoice.pdf
```

This will:
1. Extract all data from the PDF
2. Display results in the terminal
3. Save extracted data as JSON (e.g., `invoice_extracted.json`)

### As a Library

```python
from pdf_invoice_extractor import PDFInvoiceExtractor

# Create extractor instance
extractor = PDFInvoiceExtractor()

# Extract data from PDF
invoice = extractor.extract('path/to/invoice.pdf')

# Access extracted data
print(f"Is GST Invoice: {invoice.is_gst_invoice}")
print(f"Invoice Number: {invoice.invoice_number}")
print(f"Seller Name: {invoice.seller.name}")
print(f"Seller GSTIN: {invoice.seller.gstin}")
print(f"Items Count: {len(invoice.items)}")

# Convert to dictionary for JSON export
data_dict = extractor.to_dict(invoice)

# Or access raw text
print(invoice.raw_text)
```

## Output Format

The extractor returns an `InvoiceData` object with the following structure:

```python
{
    'is_gst_invoice': True/False,
    'invoice_number': 'INV-001',
    'invoice_date': '01/01/2024',
    'due_date': '15/01/2024',
    'seller': {
        'name': 'ABC Company',
        'address': '123 Street, City',
        'gstin': '27ABCDE1234F1Z5',
        'pan': 'ABCDE1234F',
        'email': 'contact@abc.com',
        'phone': '+91 9876543210',
        'state': 'Maharashtra',
        'state_code': '27'
    },
    'buyer': {
        'name': 'XYZ Corp',
        'address': '456 Road, Town',
        'gstin': '24XYZAB5678G1Z2',
        'state': 'Gujarat'
    },
    'items': [
        {
            'description': 'Product A',
            'quantity': '10',
            'unit_price': '100.00',
            'amount': '1000.00',
            'gst_rate': '18',
            'gst_amount': '180.00'
        }
    ],
    'totals': {
        'subtotal': '1000.00',
        'taxable_value': '1000.00',
        'cgst': '90.00',
        'sgst': '90.00',
        'grand_total': '1180.00'
    }
}
```

## How It Works

1. **Text Extraction**: Uses `pdfminer.six` to extract text from PDF files
2. **Pattern Matching**: Uses regular expressions to identify:
   - GSTIN format (15-character alphanumeric)
   - PAN format
   - Date formats (DD/MM/YYYY, DD Month YYYY, etc.)
   - Invoice numbers
   - Email addresses and phone numbers
3. **Section Detection**: Identifies seller, buyer, and items sections based on keywords
4. **State Code Mapping**: Converts GSTIN state codes to full state names

## Limitations

- Works best with text-based PDFs (not scanned images)
- Invoice formats vary widely; may need customization for specific layouts
- Table extraction is heuristic-based and may need adjustment for complex layouts

## For Scanned PDFs

For scanned/image-based PDFs, you'll need OCR capabilities. Consider adding:
- `pytesseract` for OCR
- `pdf2image` to convert PDF pages to images

Example enhancement:
```python
from pdf2image import convert_from_path
import pytesseract

def extract_text_with_ocr(pdf_path):
    images = convert_from_path(pdf_path)
    text = ""
    for image in images:
        text += pytesseract.image_to_string(image)
    return text
```

## License

MIT License
