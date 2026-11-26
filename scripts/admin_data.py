"""Read the deliberately small, editable Part A TeX data format.

This is not a TeX interpreter. It understands balanced semantic commands,
record boundaries, common text formatting and zero-argument metadata macros.
Unknown commands remain visible and make a field's character count uncertain.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(__file__).resolve().parent / 'data'
SCHEMA = json.loads((DATA / 'part-a-fields.json').read_text(encoding='utf-8'))
QUESTIONS = json.loads((DATA / 'part-a-questions.json').read_text(encoding='utf-8'))
PARTNER_NAME = re.compile(r'partner-([1-9][0-9]*)-([A-Z0-9]+(?:-[A-Z0-9]+)*)-admin-form\.tex')
UNKNOWN = {'', 'unanswered', 'unconfirmed', 'unknown', '[todo]'}


def strip_comments(text: str, positions: bool = True) -> str:
    """Ignore unescaped comments; preserve offsets for diagnostics if requested."""
    out = []
    i = 0
    while i < len(text):
        if text[i] == '\\' and i + 1 < len(text):
            out.append(text[i:i + 2])
            i += 2
        elif text[i] == '%':
            end = text.find('\n', i)
            if end < 0:
                end = len(text)
            if positions:
                out.append(' ' * (end - i))
            i = end if positions else min(end + 1, len(text))
        else:
            out.append(text[i])
            i += 1
    return ''.join(out)


def group(text: str, start: int) -> tuple[str, int]:
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text) or text[start] != '{':
        raise ValueError('expected a braced argument')
    depth, i = 1, start + 1
    while i < len(text):
        if text[i] == '\\' and i + 1 < len(text):
            i += 2
            continue
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if not depth:
                return text[start + 1:i], i + 1
        i += 1
    raise ValueError('unclosed braced argument')


def args_of(text: str, macro: str, count: int):
    """Yield balanced arguments and source offset; ignore comments/longer names."""
    clean = strip_comments(text)
    pattern = re.compile(r'\\' + re.escape(macro) + r'(?![A-Za-z@])')
    end = 0
    for match in pattern.finditer(clean):
        if match.start() < end:
            continue
        args, cursor = [], match.end()
        for _ in range(count):
            value, cursor = group(clean, cursor)
            args.append(value)
        end = cursor
        yield tuple(args), match.start()


def metadata_macros(root: Path) -> dict[str, str]:
    path = root / 'metadata.sty'
    if not path.exists():
        return {}
    text = strip_comments(path.read_text(encoding='utf-8'))
    values = {}
    pattern = re.compile(r'\\(newcommand|renewcommand|providecommand)\*?\s*')
    for match in pattern.finditer(text):
        cursor = match.end()
        if cursor < len(text) and text[cursor] == '{':
            name, cursor = group(text, cursor)
        else:
            name_match = re.match(r'\\[A-Za-z@]+', text[cursor:])
            if not name_match:
                continue
            name = name_match.group()
            cursor += len(name)
        name = name.strip().removeprefix('\\')
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        # Parameterised commands require actual TeX expansion, so leave unknown.
        if cursor < len(text) and text[cursor] == '[':
            continue
        try:
            value, _ = group(text, cursor)
        except ValueError:
            continue
        if match.group(1) != 'providecommand' or name not in values:
            values[name] = value
    return values


@dataclass
class TextValue:
    text: str
    unknown_commands: tuple[str, ...] = ()
    placeholder: bool = False

    @property
    def missing(self):
        return (self.placeholder or self.text.casefold() in UNKNOWN
                or bool(re.fullmatch(r'\[[^\[\]]*\]', self.text)))


TEXT_WRAPPERS = {'emph', 'textbf', 'textit', 'textsc', 'textrm', 'textsf',
                 'texttt', 'underline', 'mbox', 'url', 'nolinkurl', 'textnormal'}
TEXT_SYMBOLS = {'textbackslash': '\\', 'textasciitilde': '~', 'textasciicircum': '^',
                'textunderscore': '_', 'textampersand': '&', 'LaTeX': 'LaTeX',
                'TeX': 'TeX', 'ldots': '…', 'dots': '…', 'textendash': '–',
                'textemdash': '—', 'euro': '€', 'ae': 'æ', 'AE': 'Æ', 'oe': 'œ',
                'OE': 'Œ', 'ss': 'ß', 'o': 'ø', 'O': 'Ø'}
ACCENTS = {"'": '\u0301', '`': '\u0300', '^': '\u0302', '"': '\u0308',
           '~': '\u0303', '=': '\u0304', '.': '\u0307', 'c': '\u0327',
           'v': '\u030c', 'u': '\u0306', 'H': '\u030b', 'r': '\u030a'}


def text_value(raw: str, macros: dict[str, str] | None = None) -> TextValue:
    """Normalize common TeX text, keeping paragraph separators and uncertainty."""
    macros = macros or {}
    unknown = set()
    placeholder = False

    def render(source, stack=()):
        nonlocal placeholder
        source = strip_comments(source, positions=False)
        out, i = [], 0
        while i < len(source):
            char = source[i]
            if char == '{':
                body, i = group(source, i)
                out.append(render(body, stack))
            elif char == '\\':
                match = re.match(r'\\([A-Za-z@]+|.)', source[i:], re.S)
                if not match:
                    unknown.add('\\')
                    break
                name = match.group(1)
                i += len(match.group())
                command_end = i
                if name in '&%$#_{}':
                    out.append(name)
                elif name in (' ', ',', ';', ':'):
                    out.append(' ')
                elif name == '\\' or name in ('newline', 'linebreak'):
                    out.append('\ue000')  # Preserve one explicit line break.
                elif name == 'par':
                    out.append('\n\n')
                elif name in TEXT_SYMBOLS:
                    out.append(TEXT_SYMBOLS[name])
                elif name in TEXT_WRAPPERS or name == 'HEPlaceholder':
                    body, i = group(source, i)
                    if name == 'HEPlaceholder':
                        placeholder = True
                    out.append(render(body, stack))
                elif name == 'href':
                    _, i = group(source, i)
                    body, i = group(source, i)
                    out.append(render(body, stack))
                elif name in ACCENTS:
                    if i < len(source) and source[i] == '{':
                        body, i = group(source, i)
                    elif i < len(source):
                        body, i = source[i], i + 1
                    else:
                        body = ''
                    out.append(unicodedata.normalize('NFC', render(body, stack) + ACCENTS[name]))
                elif name in macros and name not in stack and len(stack) < 20:
                    out.append(render(macros[name], (*stack, name)))
                else:
                    unknown.add('\\' + name)
                    out.append('\\' + name)
                # TeX consumes spaces immediately following a control word.
                if name.isalpha() and i == command_end:
                    while i < len(source) and source[i].isspace():
                        i += 1
            elif char == '~':
                out.append(' ')
                i += 1
            else:
                if char in '$':
                    unknown.add('math mode')
                out.append(char)
                i += 1
        return ''.join(out)

    rendered = render(raw).strip()
    rendered = rendered.replace('---', '—').replace('--', '–')
    rendered = rendered.replace('``', '“').replace("''", '”')
    paragraphs = re.split(r'\n[ \t]*\n+', rendered)
    text = '\n\n'.join(re.sub(r'\s+', ' ', p).strip() for p in paragraphs).strip()
    text = text.replace('\ue000', '\n')
    return TextValue(text, tuple(sorted(unknown)), placeholder)


@dataclass
class Field:
    key: str
    raw: str
    file: Path
    line: int
    record: tuple[str, ...]
    value: TextValue


@dataclass
class Record:
    kind: str
    path: tuple[str, ...]
    file: Path
    line: int
    fields: list[Field] = field(default_factory=list)


@dataclass
class Source:
    path: Path
    fields: list[Field] = field(default_factory=list)
    records: list[Record] = field(default_factory=list)
    questions: list[tuple[str, str, str, int]] = field(default_factory=list)
    declarations: list[tuple[str, str, int]] = field(default_factory=list)


def read_source(path: Path, macros: dict[str, str]) -> Source:
    original = path.read_text(encoding='utf-8')
    text = strip_comments(original)
    source = Source(path)
    stack, serial = [], 0
    pattern = re.compile(r'\\(AField|AQuestion|ADeclaration|begin|end)(?![A-Za-z@])')
    end = 0
    for match in pattern.finditer(text):
        if match.start() < end:
            continue
        name, cursor = match.group(1), match.end()
        count = {'AField': 2, 'AQuestion': 4, 'ADeclaration': 3}.get(name, 1)
        args = []
        try:
            for _ in range(count):
                start = cursor
                while start < len(text) and text[start].isspace():
                    start += 1
                _, cursor = group(text, cursor)
                args.append(original[start + 1:cursor - 1])
            line = text.count('\n', 0, match.start()) + 1
            if name == 'begin' and args[0] == 'ARecord':
                kind, cursor = group(text, cursor)
                serial += 1
                record = Record(kind, (*[x.path[-1] for x in stack], f'{kind}:{serial}'), path, line)
                source.records.append(record)
                stack.append(record)
            elif name == 'end' and args[0] == 'ARecord':
                if not stack:
                    raise ValueError('unmatched end of ARecord')
                stack.pop()
            elif name == 'AField':
                item = Field(args[0], args[1], path, line,
                             stack[-1].path if stack else (), text_value(args[1], macros))
                source.fields.append(item)
                if stack:
                    stack[-1].fields.append(item)
            elif name == 'AQuestion':
                source.questions.append((args[0], text_value(args[2], macros).text,
                                         text_value(args[3], macros).text, line))
            elif name == 'ADeclaration':
                source.declarations.append((args[0], text_value(args[2], macros).text, line))
            end = cursor
        except ValueError as error:
            line = text.count('\n', 0, match.start()) + 1
            raise ValueError(f'{path.name}:{line}: {error}') from error
    if stack:
        raise ValueError(f'{path.name}: unclosed ARecord{{{stack[-1].kind}}}')
    return source


def read_manifest(root: Path) -> list[Path]:
    path = root / 'part-a/partners/participants.tex'
    if not path.is_file():
        raise ValueError('part-a/partners/participants.tex is missing')
    contents = strip_comments(path.read_text(encoding='utf-8'))
    names, spans = [], []
    for (name,), start in args_of(contents, 'input', 1):
        name = name.strip()
        target = Path(name)
        if (target.parent != Path('part-a/partners') or not PARTNER_NAME.fullmatch(target.name)
                or target.is_absolute()):
            raise ValueError(f'Invalid partner manifest entry: {name}')
        names.append(root / target)
        _, end = group(contents, start + len('\\input'))
        spans.append((start, end))
    for start, end in reversed(spans):
        contents = contents[:start] + contents[end:]
    if contents.strip():
        raise ValueError('Partner manifest accepts only comments and ordinary \\input{part-a/partners/...} entries')
    if not names:
        raise ValueError('The partner manifest is empty')
    if len(names) != len(set(names)):
        raise ValueError('The partner manifest contains duplicate inputs')
    actual = set((root / 'part-a/partners').glob('partner-*.tex'))
    if set(names) != actual:
        missing = sorted(p.name for p in set(names) - actual)
        unlisted = sorted(p.name for p in actual - set(names))
        raise ValueError(f'Partner manifest mismatch: missing={missing}; unlisted={unlisted}')
    numbers = [int(PARTNER_NAME.fullmatch(p.name).group(1)) for p in names]
    if numbers != sorted(numbers) or len(numbers) != len(set(numbers)):
        raise ValueError('Partner manifest must have unique participant numbers in numeric order')
    return names


def read_project(root: Path) -> list[Source]:
    root = root.resolve()
    macros = metadata_macros(root)
    names = [root / 'part-a/part-a-consortium.tex', *sorted((root / 'part-a/ethics').glob('*.tex')),
             *read_manifest(root)]
    return [read_source(path, macros) for path in names]


def record_values(record: Record) -> dict[str, TextValue]:
    return {item.key: item.value for item in record.fields}
