import logging
from typing import Dict

from fastapi import UploadFile

logger = logging.getLogger(__name__)

_SIGNATURES: Dict = {
    'jpg': ['FF D8 FF DB'],
    'jpeg': ['FF D8 FF E0', 'FF D8 FF E1'],
    'png': ['89 50 4E 47 0D 0A 1A 0A']
}


async def is_valid_image_signature(file: UploadFile) -> bool:
    if not file.content_type:
        logger.error("File %s has no content type", file.filename)
        return False
    file_type, extension = file.content_type.split('/')
    if file_type != 'image':
        logger.error("File has invalid type %s", file_type)
        return False
    is_valid: bool = False
    data = await file.read(32)
    logger.info("Validation file with extension = %s", extension)
    hex_data: str = ' '.join(['{:02X}'.format(byte) for byte in data])
    for signature in _SIGNATURES.get(extension, []):
        if signature in hex_data:
            is_valid = True
            logger.info("File validated at signature %s", signature)
            break
    await file.seek(0)
    logger.info("Validation file signature result = %s", is_valid)
    return is_valid
