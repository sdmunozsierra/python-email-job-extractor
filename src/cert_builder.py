class CertBuilder:
    def __init__(self):
        self.title = None
        self.issuer = None
        self.completion_date = None

    def with_title(self, title):
        self.title = title
        return self

    def with_issuer(self, issuer):
        self.issuer = issuer
        return self

    def with_completion_date(self, completion_date):
        self.completion_date = completion_date
        return self

    def build(self):
        return Cert(self)


class Cert:
    def __init__(self, builder):
        self.title = builder.title
        self.issuer = builder.issuer
        self.completion_date = builder.completion_date

    def __str__(self):
        return f"Title: {self.title}\nIssuer: {self.issuer}\nCompletion Date: {self.completion_date}"

    def __repr__(self):
        return self.title, self.issuer, self.completion_date

class CertFactory:
    @staticmethod
    def from_file(file_path):
        cert_list = []
        with open(file_path) as f:
            lines = f.readlines()
            i = 0
            while i < len(lines)-2:
                title = lines[i].strip()
                issuer = lines[i + 1].strip()
                completion_date = lines[i + 2].strip()
                cert = CertBuilder().with_title(title).with_issuer(issuer).with_completion_date(completion_date).build()
                cert_list.append(cert)
                i += 3
        return cert_list
