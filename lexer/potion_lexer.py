import re
from typing import List, Tuple

# --------------------
# TOKENS DEFINITIONS
# --------------------
TOKEN_SPEC = [
    ("RETURN", r"return\b"),
    ("EQ",         r"=="),
    ("NEQ",        r"!="),
    ("LTE",        r"<="),
    ("GTE",        r">="),
    ("LT",         r"<"),
    ("GT",         r">"),
    ("NUMBER",     r"\d+(\.\d+)?"),
    ("STRING",     r'\".*?\"'),
    ("BOOL",       r'\btrue\b|\bfalse\b'),
    ("VAL",        r"val\b"),
    ("VAR",        r"var\b"),
    ("FN",         r"fn\b"),
    ("SP",         r"sp\b"),
    ("SEND",       r"send\b"),
    ("RECEIVE",    r"receive\b"),
    ("MATCH",      r"match\b"),
    ("NONE",       r"none\b"),
    ("IF",         r"if\b"),
    ("ELSE",       r"else\b"),
    ("ARROW",      r"=>"),
    ("ASSIGN",     r"="),
    ("LBRACE",     r"\{"),
    ("RBRACE",     r"\}"),
    ("LPAREN",     r"\("),
    ("RPAREN",     r"\)"),
    ("COLON",      r":"),
    ("PLUS",       r"\+"),
    ("MINUS",      r"-"),
    ("STAR",       r"\*"),
    ("SLASH",      r"/"),
    ("COMMA",      r","),
    ("ID",         r"[a-zA-Z_][a-zA-Z0-9_]*"),
    ('WHITESPACE', r'\s+'),
    ("NEWLINE",    r"\n"),
    ("SKIP",       r"[ \t]+"),
    ("MISMATCH",   r"."),
    ('COMMENT', r'//[^\n]*'),
    

]

token_re = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC))

Token = Tuple[str, str]  # (type, value)

# --------------------
# LEXER IMPLEMENTATION
# --------------------
def tokenize(code: str) -> List[Token]:

    tokens = []
    for match in token_re.finditer(code):
        kind = match.lastgroup
        value = match.group()
        if kind in ('WHITESPACE', 'NEWLINE', 'COMMENT', 'SKIP'):
            continue
        elif kind == "MISMATCH":
            raise RuntimeError(f"Unexpected character: {value}")
        else:
            tokens.append((kind, value))
    return tokens
