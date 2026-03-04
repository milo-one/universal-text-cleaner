# Universal Text Cleaner

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A lightweight preprocessing tool for cleaning raw text extracted from PDFs, OCR pipelines, and technical documents before linguistic analysis or language model training.

The cleaner focuses on **removing structural artifacts while preserving the actual text content**.

Typical input sources include:

- scanned books
- OCR output
- PDF text extraction
- technical specifications
- mixed corpus data

---

# Features

The cleaner performs several normalization steps commonly required for NLP pipelines.

### Unicode normalization
Removes problematic characters that often appear in digitized documents.

Examples:

- zero-width spaces
- byte order marks (BOM)
- private-use unicode artifacts

### OCR repair
Fixes common OCR word splitting issues:
charakterisier-
ten → charakterisierten


and


proto­col → protocol


### Ligature normalization

PDF ligatures are converted into standard characters:


speciﬁcation → specification


### Hyphenation repair

Line-break hyphenation is merged back into full words.

### Page artifact removal

Typical document artifacts are removed:

- page headers
- page numbers
- markers like `[Seite 13]`
- technical header blocks (RFC style)

### Whitespace normalization

- merges broken sentence lines
- removes indentation artifacts
- standardizes paragraph spacing

---

# Example

### Raw input


RFC 1234 – Example Technical Document

Internet Standards Process

Bradner Best Current Practice

The following speciﬁcation describes a proto­col used
for communication between distributed sys­tems.

Some documents contain invisible characters or corrupted bytes
that interfere with automated text processing.


### Cleaned output


The following specification describes a protocol used for communication between distributed systems.

Some documents contain invisible characters or corrupted bytes that interfere with automated text processing.


---

# Installation

No dependencies are required.

Python 3.8+ is recommended.

Clone the repository:


git clone https://github.com/milo-one/universal_cleaner.git

cd universal_cleaner


---

# Usage

Basic cleaning:


python cleaner.py input.txt output.txt


Example:


python cleaner.py examples/raw_sample.txt examples/cleaned_sample.txt


---

# Hexdump mode

For debugging encoding problems you can generate a hexadecimal dump of the input file.


python cleaner.py input.txt output.txt --hexdump


This produces an additional file:


output.hexdump.txt


The dump helps identify hidden characters such as:

- soft hyphens
- ligatures
- zero-width spaces
- corrupted byte sequences

---

# Typical Use Cases

- corpus preparation for NLP
- LLM dataset cleaning
- OCR post-processing
- preprocessing technical documentation
- removing structural noise from PDFs

---

## Repository Structure

```
universal_cleaner/
│
├── cleaner.py
├── README.md
└── examples
    ├── raw_sample.txt
    ├── raw_technical_sample.txt
    └── cleaned_sample.txt
```


---

# Design Goals

The cleaner is designed to be:

- **robust**
- **transparent**
- **dependency-free**

It focuses on fixing the most common document artifacts without introducing heavy processing pipelines.

---

# License

MIT License
