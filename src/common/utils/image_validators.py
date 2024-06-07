from typing import Dict

from fastapi import UploadFile

_SIGNATURES: Dict = {
    'jpg': ['FF D8 FF DB'],
    'jpeg': ['FF D8 FF E0', 'FF D8 FF E1'],
    'png': ['89 50 4E 47 0D 0A 1A 0A']
}


async def is_valid_image_signature(file: UploadFile) -> bool:
    if not file.content_type:
        return False
    file_type, extension = file.content_type.split('/')
    if file_type != 'image':
        return False
    is_valid: bool = False
    data = await file.read(32)
    hex_data: str = ' '.join(['{:02X}'.format(byte) for byte in data])
    for signature in _SIGNATURES.get(extension, []):
        if signature in hex_data:
            is_valid = True
            break
    await file.seek(0)
    return is_valid
