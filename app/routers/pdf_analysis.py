from fastapi import APIRouter, HTTPException, Query
from app.utils.supabase_client import supabase

router = APIRouter()

@router.get("/pdf-analysis")
def get_pdf_analysis(filename: str = Query(..., description="Name of the PDF file")):
    """
    Retrieve PDF analysis (summary + QA) by PDF filename.
    """
    try:
        # join pdf_files and pdf_analysis by pdf_id
        # Step 1: find the PDF row
        pdf_res = supabase.table("pdf_files").select("id, filename").eq("filename", filename).execute()
        if not pdf_res.data:
            raise HTTPException(status_code=404, detail=f"No PDF found with filename {filename}")

        pdf_id = pdf_res.data[0]["id"]

        # Step 2: get analysis for this PDF
        analysis_res = supabase.table("pdf_analysis").select("*").eq("pdf_id", pdf_id).execute()
        if not analysis_res.data:
            raise HTTPException(status_code=404, detail=f"No analysis found for {filename}")

        return {
            "filename": filename,
            "pdf_id": pdf_id,
            "analysis": analysis_res.data[0]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving PDF analysis: {str(e)}")
