import re
from typing import List, Dict, Any, Optional
import pdfplumber
import pandas as pd


class InvoiceTableExtractor:
    """Extract table data from invoice PDFs with GST detection."""
    
    def __init__(self):
        self.gst_pattern = re.compile(r'\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d{1}[Z]{1}[A-Z\d]{1}')
        self.date_patterns = [
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
            r'\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4}',
            r'[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{2,4}'
        ]
    
    def is_gst_invoice(self, text: str) -> bool:
        """Detect if the document is a GST invoice."""
        if re.search(self.gst_pattern, text):
            return True
        gst_keywords = ['cgst', 'sgst', 'igst', 'gst', 'goods and services tax']
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in gst_keywords)
    
    def extract_tables_from_page(self, page) -> List[Dict[str, Any]]:
        """Extract tables from a single PDF page."""
        tables_data = []
        
        # Try extracting tables with explicit lines
        tables = page.extract_tables()
        
        if tables:
            for idx, table in enumerate(tables):
                if table and len(table) > 0:
                    # Convert to DataFrame for easier handling
                    df = pd.DataFrame(table)
                    
                    # Clean the dataframe
                    df = df.replace('\n', ' ', regex=True)
                    df = df.replace(r'\s+', ' ', regex=True)
                    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
                    
                    # Remove completely empty rows/columns
                    df = df.dropna(how='all')
                    if not df.empty:
                        df = df.dropna(axis=1, how='all')
                    
                    # Detect headers (usually first row)
                    headers = []
                    if len(df) > 0:
                        first_row = df.iloc[0].tolist()
                        # Check if first row looks like headers
                        header_keywords = ['item', 'description', 'qty', 'quantity', 'price', 
                                         'amount', 'tax', 'gst', 'rate', 'hsn', 'sac', 'total']
                        is_header = any(
                            any(keyword in str(cell).lower() for keyword in header_keywords)
                            for cell in first_row if cell
                        )
                        
                        if is_header:
                            headers = first_row
                            data_rows = df.iloc[1:].values.tolist()
                        else:
                            headers = [f"Column_{i}" for i in range(len(df.columns))]
                            data_rows = df.values.tolist()
                    
                    # Clean headers
                    clean_headers = []
                    for h in headers:
                        if h is None:
                            clean_headers.append(f"Column_{len(clean_headers)}")
                        else:
                            clean_h = str(h).strip().replace('\n', ' ')
                            clean_headers.append(clean_h if clean_h else f"Column_{len(clean_headers)}")
                    
                    # Convert to list of dicts
                    rows = []
                    for row_data in data_rows:
                        row_dict = {}
                        for i, value in enumerate(row_data):
                            header_name = clean_headers[i] if i < len(clean_headers) else f"Column_{i}"
                            if value is not None:
                                row_dict[header_name] = str(value).strip()
                            else:
                                row_dict[header_name] = ""
                        if any(row_dict.values()):  # Only add non-empty rows
                            rows.append(row_dict)
                    
                    if rows:
                        tables_data.append({
                            "table_index": idx,
                            "headers": clean_headers,
                            "rows": rows,
                            "row_count": len(rows),
                            "column_count": len(clean_headers)
                        })
        
        return tables_data
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract all text from PDF for metadata analysis."""
        full_text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
        return full_text
    
    def extract_all(self, pdf_path: str) -> Dict[str, Any]:
        """Extract all table data and metadata from PDF."""
        result = {
            "is_gst_invoice": False,
            "tables": [],
            "metadata": {
                "total_pages": 0,
                "total_tables": 0,
                "total_rows": 0
            }
        }
        
        try:
            # Extract text for GST detection
            full_text = self.extract_text_from_pdf(pdf_path)
            result["is_gst_invoice"] = self.is_gst_invoice(full_text)
            
            # Extract tables
            all_tables = []
            total_rows = 0
            
            with pdfplumber.open(pdf_path) as pdf:
                result["metadata"]["total_pages"] = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, start=1):
                    page_tables = self.extract_tables_from_page(page)
                    
                    for table in page_tables:
                        table["page_number"] = page_num
                        all_tables.append(table)
                        total_rows += table["row_count"]
            
            result["tables"] = all_tables
            result["metadata"]["total_tables"] = len(all_tables)
            result["metadata"]["total_rows"] = total_rows
            
        except Exception as e:
            result["error"] = str(e)
        
        return result


# Example usage
if __name__ == "__main__":
    extractor = InvoiceTableExtractor()
    result = extractor.extract_all("sample_invoice.pdf")
    print(result)
