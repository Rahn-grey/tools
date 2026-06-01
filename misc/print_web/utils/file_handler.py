"""
File handling utilities for PyPrint.
"""
import os
from typing import Set


class FileHandler:
    """Handles file validation and type detection."""

    # Supported file extensions
    ALLOWED_EXTENSIONS: Set[str] = {
        # Documents
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'odt', 'ods', 'odp',
        # Images
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'webp',
        # Text
        'txt', 'rtf', 'csv',
        # Other
        'svg', 'eps', 'ai'
    }

    # MIME types mapping
    MIME_TYPES = {
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'tiff': 'image/tiff',
        'tif': 'image/tiff',
        'webp': 'image/webp',
        'txt': 'text/plain',
        'rtf': 'application/rtf',
        'csv': 'text/csv',
    }

    def is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed."""
        if not filename:
            return False
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        return ext in self.ALLOWED_EXTENSIONS

    def get_file_type(self, filename: str) -> str:
        """Get the file type category."""
        if not filename:
            return 'unknown'
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

        doc_types = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'odt', 'ods', 'odp', 'rtf', 'csv'}
        img_types = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'webp'}
        txt_types = {'txt'}

        if ext in doc_types:
            return 'document'
        elif ext in img_types:
            return 'image'
        elif ext in txt_types:
            return 'text'
        return 'unknown'

    def get_mime_type(self, filename: str) -> str:
        """Get MIME type for file."""
        if not filename:
            return 'application/octet-stream'
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        return self.MIME_TYPES.get(ext, 'application/octet-stream')

    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"