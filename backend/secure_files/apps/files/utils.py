import hashlib

def check_file_integrity(file_data, stored_checksum):
    """
    Verifies file integrity using SHA-256
    """
    calculated_hash = hashlib.sha256(file_data).hexdigest()
    return calculated_hash == stored_checksum

def calculate_checksum(file_data):
    """
    Calculates SHA-256 checksum of file
    """
    return hashlib.sha256(file_data).hexdigest()

def get_mime_type(file_name):
    """
    Determines MIME type from file extension
    """
    import mimetypes
    mime_type, _ = mimetypes.guess_type(file_name)
    return mime_type or 'application/octet-stream'

def format_file_size(size):
    """Format file size in bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"