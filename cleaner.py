"""
Universal Text Cleaning Utility
===============================

This script normalizes raw text files before linguistic analysis
or language model training. It focuses on typical artifacts that
occur in OCR corpora, digitized books, technical documents and
mixed text sources.

Main features
-------------

• removes BOM and zero-width characters
• removes private-use UTF-8 artifacts
• fixes hyphenated OCR word splits
• removes page headers and numbering
• normalizes whitespace and line breaks
• optional hexadecimal dump of input files for debugging

Typical use cases
-----------------

- corpus preparation
- NLP preprocessing
- LLM dataset cleaning
- OCR post-processing

Usage
-----

Clean a file:

    python cleaner.py input.txt output.txt

Clean a file and generate a hexdump:

    python cleaner.py input.txt output.txt --hexdump
"""

import re
import argparse
from pathlib import Path


# ---------------------------------------------------------------------
# Basic preprocessing
# ---------------------------------------------------------------------

def preprocess_text(text: str) -> str:
    """
    Perform basic whitespace normalization and remove zero-width artifacts.

    Steps
    -----
    1. Temporarily protect paragraph boundaries.
    2. Remove known broken UTF-8 private-use byte patterns.
    3. Remove zero-width characters and BOM.
    4. Normalize whitespace.
    5. Restore paragraphs.

    Parameters
    ----------
    text : str
        Raw text input.

    Returns
    -------
    str
        Cleaned text.
    """

    text = re.sub(r"\n{2,}", "§PARA§", text)
    text = re.sub(r"\xef\x84[\xb0-\xbf]", "", text)
    text = re.sub(r"[\u200b\u200c\u200d\uFEFF]", "", text)

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"[ ]*\n[ ]*", "\n", text)

    text = text.replace("§PARA§", "\n\n")

    return text.strip()


# ---------------------------------------------------------------------
# Byte-level cleanup
# ---------------------------------------------------------------------

def remove_private_use_bytes(raw: bytes) -> bytes:
    """
    Remove UTF-8 sequences belonging to the private-use range EF 84 B0–BF.

    These characters sometimes appear in corrupted OCR or PDF extraction.

    Parameters
    ----------
    raw : bytes
        Raw byte stream.

    Returns
    -------
    bytes
        Cleaned byte stream.
    """

    cleaned = bytearray()
    i = 0

    while i < len(raw):
        if (
            i + 2 < len(raw)
            and raw[i] == 0xEF
            and raw[i + 1] == 0x84
            and 0xB0 <= raw[i + 2] <= 0xBF
        ):
            i += 3
            continue

        cleaned.append(raw[i])
        i += 1

    return bytes(cleaned)


# ---------------------------------------------------------------------
# OCR artifact repair
# ---------------------------------------------------------------------

def fix_inline_hyphen_splits(text: str) -> str:
    """
    Fix OCR word splits like:
    charakterisier— ten -> charakterisierten
    """

    pattern = r"([A-Za-zÄÖÜäöüß]{3,})[-–—]\s+([A-Za-zÄÖÜäöüß]{2,})"
    return re.sub(pattern, r"\1\2", text)

def fix_linebreak_hyphenation(text: str) -> str:
    """
    Fix linebreak hyphenation:
    charakterisier-
    ten -> charakterisierten
    """

    pattern = r"([A-Za-zÄÖÜäöüß]{3,})[-–—]\n\s*([A-Za-zÄÖÜäöüß]{2,})"
    return re.sub(pattern, r"\1\2", text)


def fix_split_words(text: str, valid_words: set) -> str:
    """
    Merge split word fragments if neither fragment exists in a dictionary.

    Parameters
    ----------
    text : str
        Input text.

    valid_words : set
        Dictionary of valid tokens.

    Returns
    -------
    str
        Text with merged fragments.
    """

    pattern = r"\b([A-Za-zÄÖÜäöüß]{2,})\s+([a-z]{2,})\b"

    def repl(match):
        left, right = match.group(1), match.group(2)

        if left.lower() not in valid_words and right.lower() not in valid_words:
            return left + right

        return match.group(0)

    return re.sub(pattern, repl, text)


def fix_midword_caps(text: str) -> str:
    """
    Fix mid-word capitalization artifacts from OCR.

    Example
    -------
    charakteriSiert -> charakterisiert
    """

    return re.sub(
        r"([a-zäöüß]+)([A-Z])([a-zäöüß]+)",
        lambda m: m.group(1) + m.group(2).lower() + m.group(3),
        text,
    )


def merge_lines_safely(text: str) -> str:
    lines = text.split("\n")
    merged = []

    buffer = ""

    for line in lines:

        line = line.strip()

        if not line:
            if buffer:
                merged.append(buffer.strip())
                buffer = ""
            merged.append("")
            continue

        # Titelzeilen / Header nicht mergen
        if re.match(r"^(RFC\s*\d+|Internet Standards Process|Bradner Best Current Practice)", line):
            if buffer:
                merged.append(buffer.strip())
                buffer = ""
            merged.append(line)
            continue

        # Satzende -> neuen Absatz
        if buffer.endswith((".", "!", "?")):
            merged.append(buffer.strip())
            buffer = line
        else:
            if buffer:
                buffer += " " + line
            else:
                buffer = line

    if buffer:
        merged.append(buffer.strip())

    return "\n".join(merged)

# ---------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------

def clean_text_killmode(text: str) -> str:
    """
    Perform aggressive text normalization.

    This routine removes control characters, page headers,
    soft hyphens, and formatting artifacts.

    Parameters
    ----------
    text : str
        Raw text input.

    Returns
    -------
    str
        Fully normalized text.
    """

    # Normalize unusual line separators
    text = text.replace("\u2028", " ")
    text = text.replace("\u2029", " ")
    text = text.replace("\u0085", " ")
    text = text.replace("\x0b", " ")
    text = text.replace("\x0c", " ")
    text = text.replace("\r", " ")

    text = text.lstrip("\ufeff")

    # remove soft hyphen
    text = text.replace("\xad", "")

    # fix OCR hyphenation
    text = fix_linebreak_hyphenation(text)
    text = fix_inline_hyphen_splits(text)

    text = re.sub(
        r"^\s*(Bradner.*Best Current Practice.*|RFC\s*\d+.*|"
        r"Internet Standards Process.*|\[Page\s*\d+\]).*$",
        "",
        text,
        flags=re.IGNORECASE | re.MULTILINE
    )

    # ---------------------------------------------------------
    # Remove leftover PDF headers after line merging
    # ---------------------------------------------------------

    # remove patterns like "- 12 –"
    text = re.sub(
        r"[-–—]\s*\d+\s*[-–—]",
        "",
        text
    )

    # remove leftover page markers
    text = re.sub(
        r"\[\s*Seite\s*\d+\s*\]",
        "",
        text
    )

    # normalize whitespace again
    text = re.sub(r"\s{2,}", " ", text)

    # remove indentation
    text = re.sub(r"\n[ \t]+", "\n", text)

    # normalize spaces
    text = re.sub(r"[ \t]{2,}", " ", text)


    # ---------------------------------------------------------
    # Remove obvious PDF page artefacts
    # ---------------------------------------------------------

    # remove markers like "[Seite 13]"
    text = re.sub(r"\[\s*Seite\s*\d+\s*\]", "", text)

    # remove page numbers like "- 12 –" when they appear alone
    text = re.sub(r"(?m)^\s*-\s*\d+\s*[–-]\s*$", "", text)

    # remove lines that contain only a number
    text = re.sub(r"(?m)^\s*\d+\s*$", "", text)

    # 5. Collapse leftover empty lines from removed markers
    text = re.sub(r"\n{3,}", "\n\n", text)

    LIGATURES = {
        "ﬁ": "fi",
        "ﬂ": "fl",
        "ﬀ": "ff",
        "ﬃ": "ffi",
        "ﬄ": "ffl",
        "ﬅ": "ft",
        "ﬆ": "st",
    }

    for k, v in LIGATURES.items():
        text = text.replace(k, v)

    # remove chapter headers like "12 Einführung in die Systemanalyse"
    text = re.sub(
        r"(?<!\S)\d+\s+[A-ZÄÖÜ][A-Za-zÄÖÜäöüß ,.'\-]{3,}?(?=\s+[A-ZÄÖÜ][a-zäöü])",
        "",
        text
    )

    # Keep paragraphs
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n\s+", "\n", text)

    # Gutenberg formatting
    text = re.sub(r"=([^=]+)=", r"\1", text)
    text = re.sub(r"\+([^+]+)\+", r"\1", text)
    text = re.sub(r"~([^~]+)~", r"\1", text)

    text = re.sub(r"\xef\xbb\xbf", " ", text, flags=re.IGNORECASE)

    text = re.sub(
        r"\[\s*(page|seite|pg\.?)\s*\d+\s*\]",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # Remove private-use unicode range
    text = re.sub(r"[\uf130-\uf13f]", "", text)

    text = text.lstrip("\ufeff")

    # Remove control characters but keep Unicode letters
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", " ", text)

    text = merge_lines_safely(text)



    return text.strip()


# ---------------------------------------------------------------------
# Hexdump utility
# ---------------------------------------------------------------------

def write_hexdump(input_path: Path, output_path: Path):
    """
    Write a hex dump of the input file for debugging encoding issues.
    """

    with open(input_path, "rb") as f:
        data = f.read()

    with open(output_path, "w", encoding="utf-8") as out:

        for i in range(0, min(len(data), 100000), 16):

            chunk = data[i:i + 16]

            hex_bytes = " ".join(f"{b:02X}" for b in chunk)

            ascii_repr = "".join(
                chr(b) if 32 <= b < 127 else "."
                for b in chunk
            )

            out.write(f"{i:08X}  {hex_bytes:<47}  {ascii_repr}\n")


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description="Clean raw text files for corpus preparation."
    )

    parser.add_argument(
        "input",
        help="Input text file"
    )

    parser.add_argument(
        "output",
        help="Output cleaned text file"
    )

    parser.add_argument(
        "--hexdump",
        action="store_true",
        help="Generate hex dump of the input file"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        raw = f.read()

    cleaned = clean_text_killmode(raw)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(cleaned)

    print("Text cleaned:", output_path)

    if args.hexdump:

        hexfile = output_path.with_suffix(".hexdump.txt")

        write_hexdump(input_path, hexfile)

        print("Hexdump written to:", hexfile)


if __name__ == "__main__":
    main()