"""
integrations/box_client.py — Box.com data room management (STUBBED).

# TODO: WIRE REAL API — https://developer.box.com/reference/
# Box.com data room folder: https://app.box.com/folder/331277504511
"""
import uuid
from typing import Optional, List, Dict

from core.logger import get_logger

logger = get_logger(__name__)

# ─── Mock data store (in-memory for stub) ─────────────────────────────────────
_MOCK_FOLDERS: Dict[str, str] = {}  # company_name → folder_id
_MOCK_FILES: Dict[str, List[Dict]] = {}  # folder_id → list of file records


class BoxClient:
    """STUBBED Box.com client. All methods return realistic mock data."""

    def check_folder(self, company_name: str) -> Optional[str]:
        """
        Check if a Box folder exists for the given company.

        # STUB CALL: check_folder
        # TODO: WIRE REAL API — GET https://api.box.com/2.0/folders/{folder_id}/items
        Returns:
            folder_id string if exists, None otherwise.
        """
        logger.debug(f"# STUB CALL: BoxClient.check_folder(company_name={company_name!r})")
        folder_id = _MOCK_FOLDERS.get(company_name)
        if folder_id:
            logger.info(f"[Box STUB] Found existing folder for {company_name!r}: {folder_id}")
        else:
            logger.info(f"[Box STUB] No folder found for {company_name!r}")
        return folder_id

    def create_folder(self, company_name: str) -> str:
        """
        Create a new Box folder for a company deal.

        # STUB CALL: create_folder
        # TODO: WIRE REAL API — POST https://api.box.com/2.0/folders
        Returns:
            New folder_id string.
        """
        logger.debug(f"# STUB CALL: BoxClient.create_folder(company_name={company_name!r})")
        folder_id = f"box_folder_{uuid.uuid4().hex[:8]}"
        _MOCK_FOLDERS[company_name] = folder_id
        _MOCK_FILES[folder_id] = []
        logger.info(f"[Box STUB] Created folder for {company_name!r}: {folder_id}")
        return folder_id

    def upload_document(self, folder_id: str, file_path: str, subfolder: str = "Investor Materials") -> str:
        """
        Upload a document to a Box folder subfolder.

        # STUB CALL: upload_document
        # TODO: WIRE REAL API — POST https://upload.box.com/api/2.0/files/content
        Args:
            folder_id: Box folder ID.
            file_path: Local path to the file.
            subfolder: "Investor Materials" or "Data Room".
        Returns:
            file_id string.
        """
        logger.debug(
            f"# STUB CALL: BoxClient.upload_document("
            f"folder_id={folder_id!r}, file_path={file_path!r}, subfolder={subfolder!r})"
        )
        file_id = f"box_file_{uuid.uuid4().hex[:8]}"
        if folder_id not in _MOCK_FILES:
            _MOCK_FILES[folder_id] = []
        _MOCK_FILES[folder_id].append({
            "name": file_path.split("/")[-1],
            "file_id": file_id,
            "subfolder": subfolder,
            "uploaded_at": "2026-02-24T12:00:00Z",
        })
        logger.info(f"[Box STUB] Uploaded {file_path!r} to folder {folder_id} / {subfolder}: file_id={file_id}")
        return file_id

    def list_documents(self, folder_id: str) -> List[Dict]:
        """
        List all documents in a Box folder.

        # STUB CALL: list_documents
        # TODO: WIRE REAL API — GET https://api.box.com/2.0/folders/{folder_id}/items
        Returns:
            List of {name, file_id, subfolder, uploaded_at} dicts.
        """
        logger.debug(f"# STUB CALL: BoxClient.list_documents(folder_id={folder_id!r})")
        docs = _MOCK_FILES.get(folder_id, [])
        logger.info(f"[Box STUB] Listed {len(docs)} documents in folder {folder_id}")
        return docs

    def get_folder_url(self, folder_id: str) -> str:
        """Return the Box web URL for a folder."""
        return f"https://app.box.com/folder/{folder_id}"
