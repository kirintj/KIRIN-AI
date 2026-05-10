import uuid
from pathlib import Path
from dataclasses import dataclass

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
AVATAR_DIR = STATIC_DIR / "avatars"
UPLOAD_DIR = STATIC_DIR / "uploads"

DOCUMENT_EXTENSIONS = {
    ".txt", ".md", ".py", ".js", ".ts", ".html", ".css", ".json",
    ".xml", ".yaml", ".yml", ".sh", ".sql", ".java", ".go", ".rs",
    ".c", ".cpp", ".log", ".ini", ".cfg", ".toml", ".csv",
    ".pdf", ".docx",
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}

DEFAULT_MAX_SIZE = 10 * 1024 * 1024
AVATAR_MAX_SIZE = 5 * 1024 * 1024


@dataclass
class FileParseResult:
    pages: list[str]
    filename: str
    total_pages: int


@dataclass
class ValidationError:
    code: int
    msg: str


def validate_file_extension(filename: str, allowed: set[str] | None = None) -> ValidationError | None:
    ext = Path(filename).suffix.lower()
    target = allowed or DOCUMENT_EXTENSIONS
    if ext not in target:
        return ValidationError(code=400, msg=f"不支持的文件格式: {ext}，支持: {', '.join(sorted(target))}")
    return None


def validate_file_size(size: int | None, max_size: int = DEFAULT_MAX_SIZE) -> ValidationError | None:
    if size and size > max_size:
        mb = max_size // (1024 * 1024)
        return ValidationError(code=400, msg=f"文件大小不能超过 {mb}MB")
    return None


def validate_image_type(content_type: str | None) -> ValidationError | None:
    if not content_type or not content_type.startswith("image/"):
        return ValidationError(code=400, msg="仅支持上传图片文件")
    if content_type not in IMAGE_CONTENT_TYPES:
        return ValidationError(code=400, msg="仅支持 JPG/PNG/GIF/WebP 格式")
    return None


def extract_text_from_file(filename: str, content: bytes) -> list[str]:
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        return _extract_pdf_text(content)
    if ext == ".docx":
        return _extract_docx_text(content)
    if ext in DOCUMENT_EXTENSIONS:
        try:
            return [content.decode("utf-8", errors="ignore")]
        except Exception:
            return []

    try:
        text = content.decode("utf-8", errors="ignore")
        if text.strip():
            return [text]
    except Exception:
        pass
    return []


def save_uploaded_file(content: bytes, filename: str, target_dir: Path, user_id: int) -> str:
    target_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(filename).suffix
    saved_name = f"{user_id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = target_dir / saved_name
    filepath.write_bytes(content)
    return saved_name


def _extract_pdf_text(content: bytes) -> list[str]:
    try:
        import io
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text and text.strip():
                pages.append(text.strip())
        return pages
    except Exception:
        return []


def _extract_docx_text(content: bytes) -> list[str]:
    try:
        import io
        import docx
        document = docx.Document(io.BytesIO(content))
        paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
        return ["\n".join(paragraphs)] if paragraphs else []
    except Exception:
        return []
