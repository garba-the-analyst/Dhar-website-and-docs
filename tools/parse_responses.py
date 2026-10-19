#!/usr/bin/env python3
"""
parse_responses.py: turn the emailed "Shaping Dhar" responses into one CSV.

Every response email starts with the line "SHAPING DHAR SURVEY RESPONSE" and ends
with "== END OF RESPONSE ==". In between, each answered question is written as

    [A1] Which country or region are you currently based in?
      Nigeria
    [A3] Which of the following ... (Select all that apply. ...)
      - Web development
      - Other: Embedded Linux
    [P3] How open would you be ...
      4 of 5 (1 = Not open at all, 5 = Very open)

This script finds every such block, however it reached you, and writes one CSV row
per response and one column per question code (A1, P3, D5, ...). The codes and the
wording behind them are listed in docs/CODEBOOK.md.

WHAT IT ACCEPTS (standard library only, no installs)
  - plain text files: paste or save the emails into one or many .txt files
  - .eml files (one email each) and .mbox files (a whole mailbox export,
    for example from Gmail Takeout or Thunderbird)
  - text that has been quoted in a reply or forward ("> " in front of each line)
  - several responses in one file

CSV COLUMNS
  source, response, survey_version, submitted, roles, answered, wording, pdf_copy, complete,
  then one column per question code in the order the codes first appear.
    - single choice: the option text
    - multiple choice: the options joined with " | "
    - 1-5 and 0-10 scales: the number only
    - grid: "statement: number" pairs joined with " | "
    - open text: the text (line breaks kept inside the cell)
  wording is "full" or "shortened" (long emails carry every answer with shortened
  question text, see README). pdf_copy is the file name of the PDF the respondent was told to
  attach (empty when no PDF was made), so a PDF in the mailbox can be paired with its row.
  complete is "yes" when the response ended with
  "== END OF RESPONSE ==" and "no" when the email was cut short (the first part,
  which holds the contact details and basics, is still read).

USAGE
  python3 tools/parse_responses.py responses.mbox -o responses.csv
  python3 tools/parse_responses.py mail/*.txt mail/*.eml -o responses.csv
"""
import argparse
import csv
import email
import email.policy
import mailbox
import os
import re
import sys

START = "SHAPING DHAR SURVEY RESPONSE"
END = "== END OF RESPONSE =="
QUOTE_PREFIX = re.compile(r"^(?:>\s?)+")
QUESTION = re.compile(r"^\[([A-Z]+[0-9]+[a-z]?)\]\s+(.*)$")
SCALE = re.compile(r"^\s*(\d+) of (\d+)(?: \(.*\))?$")
GRID_ROW = re.compile(r"^- (.*): (\d+) of \d+$")
GRID_KEY = re.compile(r"^\(1 = .*\)$")
FIXED_COLUMNS = ["source", "response", "survey_version", "submitted", "roles", "answered", "wording", "pdf_copy", "complete"]


def message_text(msg):
    """Plain-text body of an email.message.Message (decodes base64 / quoted-printable)."""
    body = msg.get_body(preferencelist=("plain",))
    if body is not None:
        return body.get_content()
    if not msg.is_multipart():
        return msg.get_content()
    return ""


def load_texts(path):
    """Yields (label, text) for a file: one item per email for .mbox, otherwise one for the file."""
    lower = path.lower()
    if lower.endswith(".mbox"):
        for i, msg in enumerate(mailbox.mbox(path, factory=lambda f: email.message_from_binary_file(f, policy=email.policy.default)), 1):
            yield f"{os.path.basename(path)}#{i}", message_text(msg)
    elif lower.endswith(".eml"):
        with open(path, "rb") as fh:
            msg = email.message_from_binary_file(fh, policy=email.policy.default)
        yield os.path.basename(path), message_text(msg)
    else:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            yield os.path.basename(path), fh.read()


def clean_lines(text):
    """Normalises line endings and removes reply quoting ("> ")."""
    out = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        out.append(QUOTE_PREFIX.sub("", line).rstrip("  \t") if line.lstrip().startswith(">") else line.rstrip("  \t"))
    return out


def split_blocks(lines):
    """Splits the lines into one list per response (start marker to the next start marker)."""
    starts = [i for i, line in enumerate(lines) if line.strip() == START]
    blocks = []
    for n, s in enumerate(starts):
        e = starts[n + 1] if n + 1 < len(starts) else len(lines)
        blocks.append(lines[s:e])
    return blocks


def answer_value(raw):
    """Turns the indented answer lines of one question into a single CSV value."""
    lines = [l[2:] if l.startswith("  ") else l for l in raw]
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return ""
    if len(lines) == 1:
        m = SCALE.match(lines[0])
        if m:
            return m.group(1)
    if all(l.startswith("- ") for l in lines):
        # grid rows ("- statement: 4 of 5", compact form) keep just the number
        return " | ".join(re.sub(r"^(.*): (\d+) of \d+$", r"\1: \2", l[2:]) for l in lines)
    if GRID_KEY.match(lines[0]) and all(GRID_ROW.match(l) for l in lines[1:] if l.strip()):
        pairs = []
        for l in lines[1:]:
            m = GRID_ROW.match(l)
            if m:
                pairs.append(f"{m.group(1)}: {m.group(2)}")
        return " | ".join(pairs)
    return "\n".join(lines)


def parse_block(block):
    """Returns (record dict, list of question codes in order, question text by code)."""
    rec = {"complete": "no"}
    texts = {}
    i = 1
    # header: "Key: value" lines until the first blank line
    while i < len(block) and block[i].strip():
        key, _, value = block[i].partition(":")
        key = key.strip().lower()
        value = value.strip()
        if key == "survey version":
            rec["survey_version"] = value
        elif key == "submitted":
            rec["submitted"] = value
        elif key == "roles":
            rec["roles"] = value
        elif key == "questions answered":
            rec["answered"] = value
        elif key == "question wording":
            rec["wording"] = value
        elif key == "pdf copy":
            rec["pdf_copy"] = value
        i += 1
    # body
    code = None
    raw = []

    def flush():
        if code is not None:
            rec[code] = answer_value(raw)

    for line in block[i:]:
        if line.strip() == END:
            flush(); code = None
            rec["complete"] = "yes"
            break
        m = QUESTION.match(line)
        if m:
            flush()
            code, raw = m.group(1), []
            texts[code] = m.group(2)
        elif line.startswith("== "):
            flush(); code, raw = None, []
        elif code is not None:
            raw.append(line)
    else:
        flush()
    return rec, texts


def main(argv=None):
    ap = argparse.ArgumentParser(description="Convert emailed Shaping Dhar responses into a CSV file.")
    ap.add_argument("inputs", nargs="+", help=".txt, .eml or .mbox files")
    ap.add_argument("-o", "--output", default="responses.csv", help="CSV file to write (default: responses.csv)")
    args = ap.parse_args(argv)

    rows, codes = [], []
    for path in args.inputs:
        for label, text in load_texts(path):
            for block in split_blocks(clean_lines(text)):
                rec, _texts = parse_block(block)
                rec["source"] = label
                rec["response"] = len(rows) + 1
                for c in rec:
                    if c not in FIXED_COLUMNS and c not in codes:
                        codes.append(c)
                rows.append(rec)

    with open(args.output, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIXED_COLUMNS + codes, extrasaction="ignore", restval="")
        writer.writeheader()
        writer.writerows(rows)

    incomplete = sum(1 for r in rows if r.get("complete") != "yes")
    print(f"{len(rows)} responses written to {args.output} ({len(codes)} question columns, {incomplete} cut short)", file=sys.stderr)
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
