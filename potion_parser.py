# potion_parser.py

import re
from typing import List, Tuple, Union

# --------------------
# TOKENS DEFINITIONS
# --------------------
TOKEN_SPEC = [
    ("EQ",         r"=="),
    ("NEQ",        r"!="),
    ("LTE",        r"<="),
    ("GTE",        r">="),
    ("LT",         r"<"),
    ("GT",         r">"),
    ("NUMBER",     r"\d+(\.\d+)?"),
    ("STRING",     r'\".*?\"'),
    ("VAL",        r"val\b"),
    ("VAR",        r"var\b"),
    ("FN",         r"fn\b"),
    ("SEND",       r"send\b"),
    ("RECEIVE",    r"receive\b"),
    ("MATCH",      r"match\b"),
    ("NONE",       r"none\b"),
    ("IF",         r"if\b"),
    ("ELSE",       r"else\b"),
    ("ARROW",      r"=>"),
    ("ASSIGN",     r"="),
    ("ID",         r"[a-zA-Z_][a-zA-Z0-9_]*"),
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
    ("NEWLINE",    r"\n"),
    ("SKIP",       r"[ \t]+"),
    ("MISMATCH",   r"."),
    ("RETURN", r"return\b"),

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
        if kind == "NEWLINE" or kind == "SKIP":
            continue
        elif kind == "MISMATCH":
            raise RuntimeError(f"Unexpected character: {value}")
        else:
            tokens.append((kind, value))
    return tokens

# --------------------
# AST NODE DEFINITIONS
# --------------------
class ASTNode:
    pass

class Program(ASTNode):
    def __init__(self, statements: List[ASTNode]):
        self.statements = statements

class ValDeclaration(ASTNode):
    def __init__(self, name: str, value: ASTNode):
        self.name = name
        self.value = value

class VarDeclaration(ASTNode):
    def __init__(self, name: str, value: ASTNode):
        self.name = name
        self.value = value

class FunctionDef(ASTNode):
    def __init__(self, name: str, params: List[str], body: List[ASTNode]):
        self.name = name
        self.params = params
        self.body = body

class PrintCall(ASTNode):
    def __init__(self, value: ASTNode):
        self.value = value

class Literal(ASTNode):
    def __init__(self, value):
        self.value = value

class LiteralBool:
    def __init__(self, value):
        self.value = value

class LiteralInt:
    def __init__(self, value):
        self.value = value

class Identifier(ASTNode):
    def __init__(self, name):
        self.name = name

class BinaryOp(ASTNode):
    def __init__(self, left: ASTNode, op: str, right: ASTNode):
        self.left = left
        self.op = op
        self.right = right

class IfBlock(ASTNode):
    def __init__(self, condition: ASTNode, if_body: List[ASTNode], else_body: Union[List[ASTNode], None]):
        self.condition = condition
        self.if_body = if_body
        self.else_body = else_body

class ReturnStatement(ASTNode):
    def __init__(self, value: ASTNode):
        self.value = value

# --------------------
# PARSER IMPLEMENTATION
# --------------------
class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else ("EOF", "")

    def eat(self, kind: str) -> Token:
        tok = self.current()
        if tok[0] == kind:
            self.pos += 1
            return tok
        raise SyntaxError(f"Expected {kind}, got {tok}")

    def parse(self) -> Program:
        statements = []
        while self.pos < len(self.tokens):
            stmt = self.statement()
            if stmt:
                statements.append(stmt)
        return Program(statements)

    def statement(self) -> Union[ASTNode, None]:
        tok = self.current()
        if tok[0] == "VAL":
            return self.val_declaration()
        elif tok[0] == "VAR":
            return self.var_declaration()
        elif tok[0] == "FN":
            return self.function_def()
        elif tok[0] == "IF":
            return self.if_block()
        elif tok[0] == "RETURN":
            return self.return_statement()
        elif tok[0] == "ID" and tok[1] == "print":
            return self.print_call()
        else:
            self.pos += 1  # Skip unrecognized token
            return None

    def val_declaration(self) -> ValDeclaration:
        self.eat("VAL")
        name = self.eat("ID")[1]
        self.eat("ASSIGN")
        expr = self.expression()
        return ValDeclaration(name, expr)

    def var_declaration(self) -> VarDeclaration:
        self.eat("VAR")
        name = self.eat("ID")[1]
        self.eat("ASSIGN")
        expr = self.expression()
        return VarDeclaration(name, expr)

    def function_def(self) -> FunctionDef:
        self.eat("FN")
        name = self.eat("ID")[1]
        self.eat("LPAREN")
        params = []
        if self.current()[0] != "RPAREN":
            params.append(self.eat("ID")[1])
            while self.current()[0] == "COMMA":
                self.eat("COMMA")
                params.append(self.eat("ID")[1])
        self.eat("RPAREN")
        self.eat("LBRACE")
        body = []
        while self.current()[0] != "RBRACE":
            stmt = self.statement()
            if stmt:
                body.append(stmt)
        self.eat("RBRACE")
        return FunctionDef(name, params, body)

    def if_block(self) -> IfBlock:
        self.eat("IF")
        condition = self.expression()
        self.eat("LBRACE")
        if_body = []
        while self.current()[0] != "RBRACE":
            stmt = self.statement()
            if stmt:
                if_body.append(stmt)
        self.eat("RBRACE")

        else_body = None
        if self.current()[0] == "ELSE":
            self.eat("ELSE")
            self.eat("LBRACE")
            else_body = []
            while self.current()[0] != "RBRACE":
                stmt = self.statement()
                if stmt:
                    else_body.append(stmt)
            self.eat("RBRACE")

        return IfBlock(condition, if_body, else_body)
    
    def return_statement(self) -> ReturnStatement:
        self.eat("RETURN")
        expr = self.expression()
        return ReturnStatement(expr)


    def print_call(self) -> PrintCall:
        self.eat("ID")  # 'print'
        self.eat("LPAREN")
        expr = self.expression()
        self.eat("RPAREN")
        return PrintCall(expr)

    def expression(self) -> ASTNode:
        node = self.comparison()
        while self.current()[0] in ("PLUS", "MINUS"):
            op = self.eat(self.current()[0])[1]
            right = self.comparison()
            node = BinaryOp(node, op, right)
        return node
    
    def comparison(self) -> ASTNode:
        node = self.term()
        while self.current()[0] in ("EQ", "NEQ", "LT", "GT", "LTE", "GTE"):
            op = self.eat(self.current()[0])[1]
            right = self.term()
            node = BinaryOp(node, op, right)
        return node

    def term(self) -> ASTNode:
        node = self.factor()
        while self.current()[0] in ("STAR", "SLASH"):
            op = self.eat(self.current()[0])[1]
            right = self.factor()
            node = BinaryOp(node, op, right)
        return node

    def factor(self) -> ASTNode:
        tok = self.current()
        if tok[0] == "STRING":
            return Literal(self.eat("STRING")[1])
        elif tok[0] == "NUMBER":
            return LiteralInt(int(self.eat("NUMBER")[1]))  # Alterado para LiteralInt
        elif tok[0] == "ID":
            return Identifier(self.eat("ID")[1])
        elif tok[0] == "TRUE":
            self.eat("TRUE")
            return LiteralBool(True)
        elif tok[0] == "FALSE":
            self.eat("FALSE")
            return LiteralBool(False)
        elif tok[0] == "LPAREN":
            self.eat("LPAREN")
            node = self.expression()
            self.eat("RPAREN")
            return node
        else:
            raise SyntaxError(f"Unexpected token in expression: {tok}")

