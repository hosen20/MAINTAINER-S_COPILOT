from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    chunk_id: str
    title: str
    content: str
    ordinal: int


class ChunkingService:
    def __init__(self, max_chars: int = 1200, overlap_chars: int = 180) -> None:
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    def chunk_text(self, *, source_id: str, title: str, text: str) -> list[TextChunk]:
        cleaned = self._clean(text)
        sections = self._split_sections(cleaned)

        chunks: list[TextChunk] = []
        current = ""

        for section in sections:
            if not section.strip():
                continue

            candidate = f"{current}\n\n{section}".strip() if current else section

            if len(candidate) <= self.max_chars:
                current = candidate
                continue

            if current:
                chunks.extend(self._split_large_block(source_id, title, current, len(chunks)))
                current = section
            else:
                chunks.extend(self._split_large_block(source_id, title, section, len(chunks)))
                current = ""

        if current.strip():
            chunks.extend(self._split_large_block(source_id, title, current, len(chunks)))

        return chunks

    def _split_large_block(
        self,
        source_id: str,
        title: str,
        block: str,
        start_ordinal: int,
    ) -> list[TextChunk]:
        if len(block) <= self.max_chars:
            ordinal = start_ordinal
            return [
                TextChunk(
                    chunk_id=f"{source_id}::chunk-{ordinal:04d}",
                    title=title,
                    content=block.strip(),
                    ordinal=ordinal,
                )
            ]

        chunks: list[TextChunk] = []
        start = 0
        ordinal = start_ordinal

        while start < len(block):
            end = min(start + self.max_chars, len(block))
            piece = block[start:end].strip()

            if piece:
                chunks.append(
                    TextChunk(
                        chunk_id=f"{source_id}::chunk-{ordinal:04d}",
                        title=title,
                        content=piece,
                        ordinal=ordinal,
                    )
                )
                ordinal += 1

            if end == len(block):
                break

            start = max(0, end - self.overlap_chars)

        return chunks

    def _split_sections(self, text: str) -> list[str]:
        markdown_sections = re.split(r"\n(?=#{1,6}\s+)", text)
        if len(markdown_sections) > 1:
            return markdown_sections

        return re.split(r"\n\s*\n", text)

    def _clean(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text.strip()