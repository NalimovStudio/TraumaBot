import logging
from pathlib import Path

from aiogram.types import FSInputFile

logger = logging.getLogger(__name__)


def get_file_by_name(filename: str):
    """
    Универсальная функция для получения любого файла из папки materials
    """
    file_path = Path(__file__).parent / filename

    if file_path.exists() and file_path.is_file():
        logger.info(f"Файл найден: {file_path}")
        return FSInputFile(str(file_path))
    else:
        logger.error(f"Файл не найден: {file_path}")
        raise FileNotFoundError(f"Файл {filename} не найден в {file_path.parent}")
