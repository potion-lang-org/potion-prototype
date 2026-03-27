from typing import Union, Optional, List
from lexer.potion_lexer import Token, tokenize

# --------------------
# AST NODE DEFINITIONS
# --------------------
class ASTNode:
    pass

class Program(ASTNode):
    def __init__(self, statements: List[ASTNode]):
        self.statements = statements

class ValDeclaration(ASTNode):
    def __init__(self, name: str, value: ASTNode, type_annotation: Optional[str] = None):
        self.name = name
        self.value = value
        self.type_annotation = type_annotation

class VarDeclaration(ASTNode):
    def __init__(self, name: str, value: ASTNode, type_annotation: Optional[str] = None):
        self.name = name
        self.value = value
        self.type_annotation = type_annotation

class ImportStatement(ASTNode):
    def __init__(self, module_name: str):
        self.module_name = module_name

class Assignment(ASTNode):
    def __init__(self, name: str, value: ASTNode):
        self.name = name
        self.value = value

class FunctionParam(ASTNode):
    def __init__(self, name: str, type_annotation: Optional[str] = None):
        self.name = name
        self.type_annotation = type_annotation

class FunctionDef(ASTNode):
    def __init__(self, name: str, params: List[FunctionParam], body: List[ASTNode]):
        self.name = name
        self.params = params
        self.body = body

class FunctionCall(ASTNode):
    def __init__(self, name: str, args: List[ASTNode]):
        self.name = name
        self.args = args

class MapLiteral(ASTNode):
    def __init__(self, entries):
        self.entries = entries  # List of (key, value)

class SendExpression(ASTNode):
    def __init__(self, target: ASTNode, message: ASTNode):
        self.target = target
        self.message = message

class SpawnExpression(ASTNode):
    def __init__(self, call: FunctionCall):
        self.call = call

class MatchClause(ASTNode):
    def __init__(self, pattern: ASTNode, body: List[ASTNode]):
        self.pattern = pattern
        self.body = body

class MatchExpression(ASTNode):
    def __init__(self, value: ASTNode, clauses: List[MatchClause]):
        self.value = value
        self.clauses = clauses

class ReceiveClause(ASTNode):
    def __init__(
        self,
        tag: Optional[str],
        bindings: List[str],
        guard: Optional[ASTNode],
        body: List[ASTNode],
        is_any: bool = False,
    ):
        self.tag = tag
        self.bindings = bindings
        self.guard = guard
        self.body = body
        self.is_any = is_any

class ReceiveBlock(ASTNode):
    def __init__(self, clauses: List[ReceiveClause]):
        self.clauses = clauses

class PrintCall(ASTNode):
    def __init__(self, value: ASTNode):
        self.value = value

class LiteralBool(ASTNode):
    def __init__(self, value):
        self.value = value

class LiteralInt(ASTNode):
    def __init__(self, value):
        self.value = value

class LiteralStr(ASTNode):
    def __init__(self, value):
        self.value = value

class LiteralNone(ASTNode):
    pass

class Identifier(ASTNode):
    def __init__(self, name):
        self.name = name

class MemberAccess(ASTNode):
    def __init__(self, target: ASTNode, field: str):
        self.target = target
        self.field = field

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

    def peek(self) -> Token:
        next_pos = self.pos + 1
        return self.tokens[next_pos] if next_pos < len(self.tokens) else ("EOF", "")

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
        elif tok[0] == "IMPORT":
            return self.import_statement()
        elif tok[0] == "FN":
            return self.function_def()
        elif tok[0] == "IF":
            return self.if_block()
        elif tok[0] == "RETURN":
            return self.return_statement()
        elif tok[0] == "ID" and self.peek()[0] == "ASSIGN":
            return self.assignment()
        elif tok[0] in ("ID", "SEND", "RECEIVE", "MATCH", "SP", "LBRACE", "LPAREN", "NUMBER", "STRING", "BOOL", "NONE"):
            return self.expression()
        else:
            self.pos += 1  # Skip unrecognized token
            return None

    def val_declaration(self) -> ValDeclaration:
        self.eat("VAL")
        name = self.eat("ID")[1]

        type_ = None
        if self.current()[0] == "COLON":
            self.eat("COLON")
            type_ = self.type_name()

        self.eat("ASSIGN")
        expr = self.expression()
        return ValDeclaration(name, expr, type_)

    def var_declaration(self) -> VarDeclaration:
        self.eat("VAR")
        name = self.eat("ID")[1]

        type_ = None
        if self.current()[0] == "COLON":
            self.eat("COLON")
            type_ = self.type_name()

        self.eat("ASSIGN")
        expr = self.expression()
        return VarDeclaration(name, expr, type_)

    def import_statement(self) -> ImportStatement:
        self.eat("IMPORT")
        module_name = self.eat("ID")[1]
        return ImportStatement(module_name)

    def function_def(self) -> FunctionDef:
        self.eat("FN")
        name = self.eat("ID")[1]
        self.eat("LPAREN")
        params = []
        if self.current()[0] != "RPAREN":
            params.append(self.function_param())
            while self.current()[0] == "COMMA":
                self.eat("COMMA")
                params.append(self.function_param())
        self.eat("RPAREN")
        self.eat("LBRACE")
        body = []
        while self.current()[0] != "RBRACE":
            stmt = self.statement()
            if stmt:
                body.append(stmt)
        self.eat("RBRACE")
        return FunctionDef(name, params, body)

    def function_param(self) -> FunctionParam:
        name = self.eat("ID")[1]
        type_ = None
        if self.current()[0] == "COLON":
            self.eat("COLON")
            type_ = self.type_name()
        return FunctionParam(name, type_)

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

    def assignment(self) -> Assignment:
        name = self.eat("ID")[1]
        self.eat("ASSIGN")
        expr = self.expression()
        return Assignment(name, expr)


    def send_expression(self) -> SendExpression:
        self.eat("SEND")
        self.eat("LPAREN")
        target = self.expression()
        self.eat("COMMA")
        message = self.expression()
        self.eat("RPAREN")
        return SendExpression(target, message)


    def spawn_expression(self) -> SpawnExpression:
        self.eat("SP")
        func_name = self.eat("ID")[1]
        self.eat("LPAREN")
        args = []
        if self.current()[0] != "RPAREN":
            args.append(self.expression())
            while self.current()[0] == "COMMA":
                self.eat("COMMA")
                args.append(self.expression())
        self.eat("RPAREN")
        return SpawnExpression(FunctionCall(func_name, args))


    def receive_block(self) -> ReceiveBlock:
        self.eat("RECEIVE")
        self.eat("LBRACE")
        clauses = []
        while self.current()[0] != "RBRACE":
            clauses.append(self.receive_clause())
        self.eat("RBRACE")
        return ReceiveBlock(clauses)

    def receive_clause(self) -> ReceiveClause:
        self.eat("ON")

        if self.current()[0] == "ANY":
            self.eat("ANY")
            self.eat("LBRACE")
            body = []
            while self.current()[0] != "RBRACE":
                stmt = self.statement()
                if stmt:
                    body.append(stmt)
            self.eat("RBRACE")
            return ReceiveClause(tag=None, bindings=[], guard=None, body=body, is_any=True)

        tag = self.eat("ID")[1]
        self.eat("LPAREN")
        bindings = []
        if self.current()[0] != "RPAREN":
            bindings.append(self.eat("ID")[1])
            while self.current()[0] == "COMMA":
                self.eat("COMMA")
                bindings.append(self.eat("ID")[1])
        self.eat("RPAREN")

        guard = None
        if self.current()[0] == "WHEN":
            self.eat("WHEN")
            guard = self.expression()

        self.eat("LBRACE")
        body = []
        while self.current()[0] != "RBRACE":
            stmt = self.statement()
            if stmt:
                body.append(stmt)
        self.eat("RBRACE")
        return ReceiveClause(tag=tag, bindings=bindings, guard=guard, body=body)


    def match_expression(self) -> MatchExpression:
        self.eat("MATCH")
        value = self.expression()
        self.eat("LBRACE")
        clauses = []
        while self.current()[0] != "RBRACE":
            pattern = self.expression()
            self.eat("ARROW")
            clause_body = []
            if self.current()[0] == "LBRACE":
                self.eat("LBRACE")
                while self.current()[0] != "RBRACE":
                    stmt = self.statement()
                    if stmt:
                        clause_body.append(stmt)
                self.eat("RBRACE")
            else:
                stmt = self.statement()
                if stmt:
                    clause_body.append(stmt)
            clauses.append(MatchClause(pattern, clause_body))
            if self.current()[0] == "COMMA":
                self.eat("COMMA")
        self.eat("RBRACE")
        return MatchExpression(value, clauses)

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
        node = self.primary()
        while self.current()[0] == "DOT":
            self.eat("DOT")
            field = self.eat("ID")[1]
            node = MemberAccess(node, field)
        return node
    
    def primary(self) -> ASTNode:
        tok_type, tok_value = self.current()

        if tok_type == "NUMBER":
            self.eat("NUMBER")
            return LiteralInt(int(tok_value))

        elif tok_type == "STRING":
            self.eat("STRING")
            return LiteralStr(tok_value.strip('"'))

        elif tok_type == "BOOL":
            self.eat("BOOL")
            return LiteralBool(tok_value == "true")
        elif tok_type == "NONE":
            self.eat("NONE")
            return LiteralNone()

        elif tok_type == "ID":
            return self.identifier_expression()
        elif tok_type == "SEND":
            return self.send_expression()
        elif tok_type == "RECEIVE":
            return self.receive_block()
        elif tok_type == "MATCH":
            return self.match_expression()
        elif tok_type == "SP":
            return self.spawn_expression()
        elif tok_type == "LBRACE":
            return self.map_literal()

        elif tok_type == "LPAREN":
            self.eat("LPAREN")
            node = self.expression()
            self.eat("RPAREN")
            return node

        else:
            raise SyntaxError(f"Unexpected token: {tok_type}")

    def identifier_expression(self) -> ASTNode:
        name = self.eat("ID")[1]
        if self.current()[0] != "LPAREN":
            return Identifier(name)

        self.eat("LPAREN")
        args = []
        if self.current()[0] != "RPAREN":
            args.append(self.expression())
            while self.current()[0] == "COMMA":
                self.eat("COMMA")
                args.append(self.expression())
        self.eat("RPAREN")

        if name == "print":
            if len(args) != 1:
                raise SyntaxError(f"print espera 1 argumento, recebeu {len(args)}")
            return PrintCall(args[0])

        return FunctionCall(name, args)

    def type_name(self) -> str:
        tok_type, tok_value = self.current()
        if tok_type in ("ID", "NONE"):
            self.pos += 1
            return tok_value
        raise SyntaxError(f"Tipo inválido: {self.current()}")

    def map_literal(self) -> MapLiteral:
        self.eat("LBRACE")
        entries = []
        if self.current()[0] == "RBRACE":
            self.eat("RBRACE")
            return MapLiteral(entries)

        while True:
            key_tok = self.current()
            if key_tok[0] != "ID":
                raise SyntaxError(f"Chave de mapa inválida: {key_tok}")
            key = self.eat("ID")[1]
            self.eat("COLON")
            value = self.expression()
            entries.append((key, value))

            if self.current()[0] == "COMMA":
                self.eat("COMMA")
            else:
                break

        self.eat("RBRACE")
        return MapLiteral(entries)
