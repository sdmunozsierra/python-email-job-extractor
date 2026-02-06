"""Cert, CertBuilder, and CertFactory -- certification model."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class Cert:
    """Represents a professional certification."""

    def __init__(
        self,
        title: str = "",
        issuer: Optional[str] = None,
        completion_date: Optional[str] = None,
        expiry: Optional[str] = None,
        credential_id: Optional[str] = None,
    ) -> None:
        self.title = title
        self.issuer = issuer
        self.completion_date = completion_date
        self.expiry = expiry
        self.credential_id = credential_id

    def __repr__(self) -> str:
        return f"Cert(title={self.title!r})"

    def __str__(self) -> str:
        parts = [self.title]
        if self.issuer:
            parts.append(f"({self.issuer})")
        return " ".join(parts)


class CertBuilder:
    """Fluent builder for :class:`Cert`."""

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}

    def title(self, title: str) -> "CertBuilder":
        self._data["title"] = title
        return self

    def issuer(self, issuer: str) -> "CertBuilder":
        self._data["issuer"] = issuer
        return self

    def completion_date(self, date: str) -> "CertBuilder":
        self._data["completion_date"] = date
        return self

    def expiry(self, date: str) -> "CertBuilder":
        self._data["expiry"] = date
        return self

    def credential_id(self, cid: str) -> "CertBuilder":
        self._data["credential_id"] = cid
        return self

    def build(self) -> Cert:
        return Cert(**self._data)


class CertFactory:
    """Create :class:`Cert` instances from various data sources."""

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Cert:
        return Cert(
            title=data.get("title") or data.get("name", ""),
            issuer=data.get("issuer"),
            completion_date=data.get("completion_date") or data.get("date"),
            expiry=data.get("expiry"),
            credential_id=data.get("credential_id"),
        )

    @staticmethod
    def from_text_line(line: str) -> Cert:
        """Parse a single text line like ``AWS SAA - Amazon Web Services``."""
        if " - " in line:
            title, issuer = line.split(" - ", 1)
            return Cert(title=title.strip(), issuer=issuer.strip())
        return Cert(title=line.strip())

    @classmethod
    def from_text_file(cls, path: str) -> List[Cert]:
        """Read a flat-text certifications file (one per line)."""
        certs: List[Cert] = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    certs.append(cls.from_text_line(line))
        return certs
