"""Basic CI checks for this static HTML/CSS site."""

from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PAGES = ("index.html", "home.html", "login.html", "perfis.html")


class LocalReferenceParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.references = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        for name in ("href", "src"):
            value = attributes.get(name, "").strip()
            if value:
                self.references.append(value)


def local_path(reference, source):
    parsed = urlsplit(reference)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    path = unquote(parsed.path)
    if path.startswith("/"):
        return ROOT / path.lstrip("/")
    return source.parent / path


def main():
    errors = []
    for relative in REQUIRED_PAGES:
        if not (ROOT / relative).is_file():
            errors.append(f"Página obrigatória ausente: {relative}")

    html_files = sorted(ROOT.rglob("*.html"))
    for html_file in html_files:
        parser = LocalReferenceParser()
        parser.feed(html_file.read_text(encoding="utf-8"))
        for reference in parser.references:
            target = local_path(reference, html_file)
            if target is not None and not target.is_file():
                errors.append(
                    f"{html_file.relative_to(ROOT)} referencia arquivo ausente: {reference}"
                )

    for css_file in sorted(ROOT.rglob("*.css")):
        content = css_file.read_text(encoding="utf-8")
        for reference in re.findall(r"url\(['\"]?(.*?)['\"]?\)", content):
            target = local_path(reference.strip(), css_file)
            if target is not None and not target.is_file():
                errors.append(
                    f"{css_file.relative_to(ROOT)} referencia arquivo ausente: {reference}"
                )

    if errors:
        print("Falha na validação do site:")
        print("\n".join(f"- {error}" for error in errors))
        return 1

    print(f"Validação concluída: {len(html_files)} páginas e referências locais verificadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
