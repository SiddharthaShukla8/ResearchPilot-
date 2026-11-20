"""PDF parser, metadata extractor, and page-aware chunker."""
import hashlib
from dataclasses import dataclass

import fitz  # PyMuPDF
import tiktoken


class PDFValidationError(Exception):
    """Raised when PDF file violates validation constraints."""


@dataclass
class ExtractedPage:
    """Page text and 1-based page number."""
    page_number: int
    text: str
    char_count: int


@dataclass
class DocumentMetadata:
    """Extracted metadata from PDF."""
    title: str | None
    authors: list[str] | None
    year: int | None
    doi: str | None
    page_count: int


@dataclass
class ChunkRecord:
    """Page-aware semantic chunk ready for indexing."""
    chunk_index: int
    page_start: int
    page_end: int
    text: str
    token_count: int
    content_hash: str


class PDFParser:
    """Validates, parses, and chunks PDF documents safely."""

    def __init__(self, max_mb: int = 25, max_pages: int = 500):
        self.max_bytes = max_mb * 1024 * 1024
        self.max_pages = max_pages
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = None

    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken or fallback whitespace estimation."""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        return max(1, len(text.split()) * 4 // 3)

    def validate_and_open(self, file_bytes: bytes) -> fitz.Document:
        """Validate size, magic bytes, encryption, and parseability."""
        if len(file_bytes) > self.max_bytes:
            raise PDFValidationError(f"File size exceeds maximum allowed limit of {self.max_bytes // (1024 * 1024)} MB")

        # PDF magic bytes check (%PDF-)
        if not file_bytes.startswith(b"%PDF-"):
            raise PDFValidationError("Invalid file signature: file is not a valid PDF document")

        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            raise PDFValidationError(f"Corrupt or unreadable PDF: {e!s}") from e

        if doc.is_encrypted:
            raise PDFValidationError("Password-protected or encrypted PDFs are not supported")

        page_count = len(doc)
        if page_count == 0:
            raise PDFValidationError("PDF document is empty (0 pages)")

        if page_count > self.max_pages:
            raise PDFValidationError(f"PDF page count ({page_count}) exceeds limit of {self.max_pages} pages")

        return doc

    def extract_metadata(self, doc: fitz.Document) -> DocumentMetadata:
        """Extract existing metadata without hallucinating missing fields."""
        meta = doc.metadata or {}
        raw_title = meta.get("title")
        raw_author = meta.get("author")
        page_count = len(doc)

        title = raw_title.strip() if raw_title and raw_title.strip() else None
        authors = None
        if raw_author and raw_author.strip():
            # Split multiple authors if separated by comma or semicolon
            authors = [a.strip() for a in raw_author.replace(";", ",").split(",") if a.strip()]

        # Best-effort year extraction from creation date (e.g., D:20230501...)
        year = None
        creation_date = meta.get("creationDate")
        if creation_date and len(creation_date) >= 6:
            candidate = creation_date[2:6]
            if candidate.isdigit() and 1900 <= int(candidate) <= 2099:
                year = int(candidate)

        return DocumentMetadata(
            title=title,
            authors=authors,
            year=year,
            doi=None,  # Only assign if verified in text/metadata
            page_count=page_count,
        )

    def extract_pages(self, doc: fitz.Document) -> list[ExtractedPage]:
        """Extract text page by page preserving 1-based page index."""
        pages: list[ExtractedPage] = []
        total_text_length = 0

        for i, page in enumerate(doc):
            text = page.get_text("text").replace("\x00", "").strip()
            total_text_length += len(text)
            pages.append(
                ExtractedPage(
                    page_number=i + 1,
                    text=text,
                    char_count=len(text),
                )
            )

        # Detect image-only or scanned PDFs with near-zero extractable text
        if total_text_length < 50 and len(doc) > 0:
            raise PDFValidationError(
                "This PDF appears to be a scanned image without an embedded text layer. "
                "Optical Character Recognition (OCR) is required for scanned documents."
            )

        return pages

    def create_chunks(
        self,
        pages: list[ExtractedPage],
        chunk_size_tokens: int = 800,
        chunk_overlap_tokens: int = 120,
    ) -> list[ChunkRecord]:
        """Create page-aware semantic chunks with bounded token lengths and overlaps."""
        chunks: list[ChunkRecord] = []
        chunk_index = 0

        current_text_parts: list[str] = []
        current_pages: set[int] = set()
        current_token_count = 0

        for page in pages:
            if not page.text:
                continue

            # Split paragraphs within page
            paragraphs = [p.strip() for p in page.text.split("\n\n") if p.strip()]
            for p in paragraphs:
                p_tokens = self.count_tokens(p)

                # If paragraph itself is excessively large, split by sentences/lines
                if p_tokens > chunk_size_tokens:
                    sub_parts = [line.strip() for line in p.split("\n") if line.strip()]
                else:
                    sub_parts = [p]

                for part in sub_parts:
                    part_tokens = self.count_tokens(part)

                    if current_token_count + part_tokens > chunk_size_tokens and current_text_parts:
                        full_chunk_text = "\n\n".join(current_text_parts)
                        chunk_hash = hashlib.sha256(full_chunk_text.encode("utf-8")).hexdigest()

                        chunks.append(
                            ChunkRecord(
                                chunk_index=chunk_index,
                                page_start=min(current_pages),
                                page_end=max(current_pages),
                                text=full_chunk_text,
                                token_count=current_token_count,
                                content_hash=chunk_hash,
                            )
                        )
                        chunk_index += 1

                        # Keep overlap from the end
                        overlap_parts: list[str] = []
                        overlap_tokens = 0
                        for prev_part in reversed(current_text_parts):
                            prev_tok = self.count_tokens(prev_part)
                            if overlap_tokens + prev_tok <= chunk_overlap_tokens:
                                overlap_parts.insert(0, prev_part)
                                overlap_tokens += prev_tok
                            else:
                                break

                        current_text_parts = overlap_parts
                        current_token_count = overlap_tokens
                        current_pages = {page.page_number}

                    current_text_parts.append(part)
                    current_pages.add(page.page_number)
                    current_token_count += part_tokens

        # Flush remaining buffer
        if current_text_parts:
            full_chunk_text = "\n\n".join(current_text_parts)
            chunk_hash = hashlib.sha256(full_chunk_text.encode("utf-8")).hexdigest()
            chunks.append(
                ChunkRecord(
                    chunk_index=chunk_index,
                    page_start=min(current_pages) if current_pages else 1,
                    page_end=max(current_pages) if current_pages else 1,
                    text=full_chunk_text,
                    token_count=current_token_count,
                    content_hash=chunk_hash,
                )
            )

        return chunks
