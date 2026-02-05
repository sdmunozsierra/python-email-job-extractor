"""Certification model and builder with support for the resume JSON schema."""


class CertBuilder:
    def __init__(self):
        self.title = None
        self.issuer = None
        self.completion_date = None
        self.expiry = None
        self.credential_id = None

    def with_title(self, title):
        self.title = title
        return self

    def with_issuer(self, issuer):
        self.issuer = issuer
        return self

    def with_completion_date(self, completion_date):
        self.completion_date = completion_date
        return self

    def with_expiry(self, expiry):
        self.expiry = expiry
        return self

    def with_credential_id(self, credential_id):
        self.credential_id = credential_id
        return self

    def build(self):
        return Cert(self)


class Cert:
    """Represents a certification / credential."""

    def __init__(self, builder):
        self.title = builder.title
        self.issuer = builder.issuer
        self.completion_date = builder.completion_date
        self.expiry = builder.expiry
        self.credential_id = builder.credential_id

    def __str__(self):
        parts = [
            f"Title: {self.title}",
            f"Issuer: {self.issuer}",
            f"Completion Date: {self.completion_date}",
        ]
        if self.expiry:
            parts.append(f"Expiry: {self.expiry}")
        if self.credential_id:
            parts.append(f"Credential ID: {self.credential_id}")
        return "\n".join(parts)

    def __repr__(self):
        return (self.title, self.issuer, self.completion_date)


class CertFactory:
    @staticmethod
    def from_file(file_path):
        """Legacy method — parse certs from a flat text file."""
        cert_list = []
        with open(file_path) as f:
            lines = f.readlines()
            i = 0
            while i < len(lines) - 2:
                title = lines[i].strip()
                issuer = lines[i + 1].strip()
                completion_date = lines[i + 2].strip()
                cert = (
                    CertBuilder()
                    .with_title(title)
                    .with_issuer(issuer)
                    .with_completion_date(completion_date)
                    .build()
                )
                cert_list.append(cert)
                i += 3
        return cert_list

    @staticmethod
    def from_dict(data):
        """Create a Cert from a JSON schema dict."""
        return (
            CertBuilder()
            .with_title(data.get("name"))
            .with_issuer(data.get("issuer"))
            .with_completion_date(data.get("date"))
            .with_expiry(data.get("expiry"))
            .with_credential_id(data.get("credential_id"))
            .build()
        )
