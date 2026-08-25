from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os
from invoice_extractor import InvoiceTableExtractor

app = FastAPI(
    title="Invoice Table Extractor API",
    description="Extract table data from invoice PDFs with GST detection",
    version="1.0.0"
)

extractor = InvoiceTableExtractor()


@app.post("/extract")
async def extract_invoice_data(file: UploadFile = File(...)):
    """
    Upload a PDF invoice and extract table data.
    
    Returns:
        JSON response containing:
        - is_gst_invoice: Boolean indicating if it's a GST invoice
        - tables: List of extracted tables with headers and rows
        - metadata: Page count, table count, row count
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files are accepted."
        )
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Extract data from PDF
            result = extractor.extract_all(tmp_path)
            
            # Add filename to result
            result["filename"] = file.filename
            
            return JSONResponse(
                status_code=200,
                content=result
            )
        
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF: {str(e)}"
        )


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Invoice Table Extractor API is running",
        "endpoints": {
            "POST /extract": "Upload a PDF invoice to extract table data"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
