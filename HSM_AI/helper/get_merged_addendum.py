import fitz  # PyMuPDF
import base64
import requests
import base64


def replace_pages_in_pdf_from_s3(
    original_url: str,
    replacement_url: str,
    pages_to_replace: list[int],
) -> str:
    """
    Replace specific pages in the original PDF (from S3 URL) with pages from the replacement PDF (from S3 URL).
    Returns the updated PDF as a base64 string (ready for upload to S3).

    Args:
        original_url (str): S3 URL of the original PDF.
        replacement_url (str): S3 URL of the replacement PDF.
        pages_to_replace (list[int]): List of 1-based page numbers to replace.

    Returns:
        str: Base64-encoded string of the updated PDF.
    """

    # --- Step 1: Download both PDFs from S3 URLs ---
    original_bytes = requests.get(original_url).content
    replacement_bytes = requests.get(replacement_url).content

    # --- Step 2: Open with PyMuPDF ---
    original_doc = fitz.open(stream=original_bytes, filetype="pdf")
    replacement_doc = fitz.open(stream=replacement_bytes, filetype="pdf")

    # --- Step 3: Replace requested pages ---
    for page_num in pages_to_replace:
        orig_index = page_num - 1  # convert to 0-based

        if orig_index < 0 or orig_index >= len(original_doc):
            print(f"⚠️ Skipping page {page_num}: out of range in original PDF.")
            continue
        if orig_index >= len(replacement_doc):
            print(f"⚠️ Skipping page {page_num}: out of range in replacement PDF.")
            continue

        # Create a temporary single-page PDF from replacement
        temp_pdf = fitz.open()
        temp_pdf.insert_pdf(replacement_doc, from_page=orig_index, to_page=orig_index)

        # Replace in original
        original_doc.delete_page(orig_index)
        original_doc.insert_pdf(temp_pdf, from_page=0, to_page=0, start_at=orig_index)

        temp_pdf.close()

    # --- Step 4: Save updated PDF to memory ---
    updated_bytes = original_doc.write()
    original_doc.close()
    replacement_doc.close()

    # --- Step 5: Convert to base64 and return ---
    updated_base64 = base64.b64encode(updated_bytes).decode("utf-8")
    return updated_base64
