from dropbox import Dropbox
from dropbox.exceptions import AuthError, ApiError
import base64
import logging

logger = logging.getLogger(__name__)


def get_dbx_file(access_token: str, file_path: str) -> str:
    """
    Downloads a file from Dropbox and returns (base64_content, file_name).

    Returns:
        (file_content_base64: str, file_name: str)
    """
    try:
        dbx = Dropbox(access_token)
        metadata, response = dbx.files_download(file_path)

        file_bytes = response.content
        file_content_base64 = base64.b64encode(file_bytes).decode("utf-8")
        file_name = metadata.name

        return file_content_base64

    except AuthError as e:
        logger.error(f"Dropbox AuthError: {str(e)}")
        raise Exception("Invalid Dropbox access token.")
    except ApiError as e:
        logger.error(f"Dropbox ApiError: {str(e)}")
        raise Exception(f"Dropbox API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise Exception(f"Error downloading file: {str(e)}")
