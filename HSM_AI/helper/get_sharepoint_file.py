import requests
import base64
import logging

logger = logging.getLogger(__name__)


def get_sharepoint_file(access_token: str, site_id: str, item_id: str) -> str:
    """
    Downloads a file from SharePoint via Microsoft Graph and returns (base64_content, file_name).

    Returns:
        (file_content_base64: str, file_name: str)
    Raises:
        Exception if download fails.
    """
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

        # Step 1: Get file metadata
        metadata_url = (
            f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/items/{item_id}"
        )
        metadata_response = requests.get(metadata_url, headers=headers)

        if metadata_response.status_code != 200:
            logger.error(f"Metadata fetch failed: {metadata_response.text}")
            raise Exception("Failed to fetch file metadata from Microsoft Graph.")

        metadata = metadata_response.json()
        file_name = metadata.get("name", "unknown_file")

        if "folder" in metadata:
            raise Exception("The selected item is a folder, not a file.")

        # Step 2: Download file content
        download_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/items/{item_id}/content"
        file_response = requests.get(download_url, headers=headers)

        if file_response.status_code != 200:
            logger.error(f"File download failed: {file_response.text}")
            raise Exception("Failed to download file from Microsoft Graph.")

        file_bytes = file_response.content
        file_content_base64 = base64.b64encode(file_bytes).decode("utf-8")

        return file_content_base64

    except Exception as e:
        logger.error(f"SharePoint file download error: {str(e)}")
        raise Exception(f"Error downloading SharePoint file: {str(e)}")
