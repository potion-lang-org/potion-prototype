from parser.potion_parser import (
    Assignment,
    BinaryOp,
    FunctionCall,
    Identifier,
    IfBlock,
    LiteralBool,
    LiteralInt,
    LiteralNone,
    LiteralStr,
    MapLiteral,
    MatchExpression,
    PrintCall,
    ReceiveBlock,
    ReturnStatement,
    SendExpression,
    SpawnExpression,
    ValDeclaration,
    VarDeclaration,
)


class PidValue:
    pass


class DynamicValue:
    pass


UNKNOWN = DynamicValue()


TYPE_MAP = {
    "int": int,
    "str": str,
    "bool": bool,
    "none": type(None),
    "pid": PidValue,
    "dynamic": DynamicValue,
}


REVERSE_TYPE_MAP = {
    int: "int",
    str: "str",
    bool: "bool",
    type(None): "none",
    PidValue: "pid",
    DynamicValue: "dynamic",
}


class SemanticAnalyzer:
    def __init__(self):
        self.local_vars = set()
        self.inside_function = False
        self.type_env = {}
        self.variables = {}
        self.functions = {}
        self.function_arities = {}
        self.function_params = {}
        self.global_var_names = set()
        self.mutable_vars = set()
        self.var_versions = {}

    def emit_local_name(self, name):
        return name.capitalize()

    def emit_versioned_name(self, name, version):
        return f"{self.emit_local_name(name)}_{version}"

    def emit_name(self, name):
        if self.inside_function:
            if name in self.mutable_vars:
                version = self.var_versions.get(name, 0)
                return self.emit_versioned_name(name, version)
            if name in self.local_vars:
                return self.emit_local_name(name)
            if name in self.global_var_names:
                return f"?{name.upper()}"
            return self.emit_local_name(name)

        if name in self.global_var_names:
            return f"?{name.upper()}"

        return self.emit_local_name(name)

    def type_checking(self, node, scope="local"):
        var_name = self.emit_name(node.name)
        evaluated_value = self.evaluate_expression(node.value)

        if node.type_annotation:
            expected_type = TYPE_MAP.get(node.type_annotation)
            if expected_type is None:
                raise Exception(f"Tipo desconhecido ({scope}) em '{node.name}': {node.type_annotation}")

            if evaluated_value is UNKNOWN:
                self.type_env[var_name] = node.type_annotation
                self.variables[var_name] = UNKNOWN
                return

            if not isinstance(evaluated_value, expected_type):
                actual_type = self.infer_type(evaluated_value)
                raise Exception(
                    f"Erro de tipo ({scope}) em '{node.name}': esperado {node.type_annotation}, mas recebeu {actual_type}"
                )
            self.type_env[var_name] = node.type_annotation

        else:
            inferred = self.infer_type(evaluated_value)
            if inferred == "unknown":
                raise Exception(f"Não foi possível inferir tipo ({scope}) para '{node.name}'")
            self.type_env[var_name] = inferred

        self.variables[var_name] = evaluated_value

    def infer_type(self, value):
        return REVERSE_TYPE_MAP.get(type(value), "unknown")

    def evaluate_expression(self, node):
        if isinstance(node, LiteralInt):
            return node.value
        if isinstance(node, LiteralStr):
            return node.value
        if isinstance(node, LiteralBool):
            return node.value
        if isinstance(node, LiteralNone):
            return None
        if isinstance(node, BinaryOp):
            left = self.evaluate_expression(node.left)
            right = self.evaluate_expression(node.right)
            if left is UNKNOWN or right is UNKNOWN:
                return self.evaluate_unknown_binary(node.op)
            if node.op == "+":
                if self.is_int_value(left) and self.is_int_value(right):
                    return left + right
                if isinstance(left, str) and isinstance(right, str):
                    return left + right
                raise Exception(
                    f"Erro de tipo: operador '+' recebeu tipos incompatíveis ({self.infer_type(left)} e {self.infer_type(right)}). "
                    "Use to_string(...) para concatenação textual."
                )
            if node.op == "-":
                return left - right
            if node.op == "*":
                return left * right
            if node.op == "/":
                return left / right
            if node.op == "==":
                return left == right
            if node.op == "!=":
                return left != right
            if node.op == ">":
                return left > right
            if node.op == "<":
                return left < right
            if node.op == ">=":
                return left >= right
            if node.op == "<=":
                return left <= right
            raise Exception(f"Operação não suportada: {node.op}")
        if isinstance(node, Identifier):
            var_name = self.emit_name(node.name)
            if var_name not in self.variables:
                if self.inside_function and node.name in self.local_vars:
                    return UNKNOWN
                raise Exception(f"Variável '{node.name}' não declarada.")
            return self.variables[var_name]
        if isinstance(node, FunctionCall):
            func_name = node.name
            args = [self.evaluate_expression(arg) for arg in node.args]

            if func_name == "self":
                return PidValue()
            if func_name == "to_string":
                if len(args) != 1:
                    raise Exception(f"Função '{func_name}' espera 1 argumento(s), recebeu {len(args)}.")
                value = args[0]
                if value is UNKNOWN:
                    return ""
                if value is None:
                    return "undefined"
                if isinstance(value, bool):
                    return "true" if value else "false"
                if isinstance(value, str):
                    return value
                return str(value)

            if func_name not in self.functions:
                raise Exception(f"Função '{func_name}' não definida.")

            func_def = self.functions[func_name]
            param_names = func_def["params"]
            body = func_def["body"]

            if len(args) != len(param_names):
                raise Exception(
                    f"Função '{func_name}' espera {len(param_names)} argumento(s), recebeu {len(args)}."
                )

            old_variables = self.variables.copy()
            self.variables = {}

            for param_name, arg_value in zip(param_names, args):
                self.variables[self.emit_name(param_name)] = arg_value

            result = self.evaluate_block(body)
            self.variables = old_variables
            return result

        if isinstance(node, (SendExpression, ReceiveBlock, MatchExpression, MapLiteral)):
            return DynamicValue()
        if isinstance(node, SpawnExpression):
            return PidValue()

        raise Exception(f"Não sei avaliar: {node}")

    def evaluate_block(self, body):
        result = None
        for stmt in body:
            if isinstance(stmt, ReturnStatement):
                return self.evaluate_expression(stmt.value)
            result = self.evaluate_statement(stmt)
        return result

    def evaluate_unknown_binary(self, op):
        if op == "+":
            return UNKNOWN
        if op in ("==", "!=", ">", "<", ">=", "<="):
            return False
        return UNKNOWN

    def evaluate_statement(self, stmt):
        if isinstance(stmt, (ValDeclaration, VarDeclaration)):
            self.type_checking(stmt)
            return self.variables[self.emit_name(stmt.name)]
        if isinstance(stmt, Assignment):
            return self.variables.get(self.emit_name(stmt.name), UNKNOWN)
        if isinstance(stmt, IfBlock):
            condition = self.evaluate_expression(stmt.condition)
            branch = stmt.if_body if condition else (stmt.else_body or [])
            return self.evaluate_block(branch)
        if isinstance(stmt, PrintCall):
            self.evaluate_expression(stmt.value)
            return DynamicValue()
        if isinstance(stmt, (SendExpression, ReceiveBlock, MatchExpression, SpawnExpression, MapLiteral)):
            return self.evaluate_expression(stmt)
        if isinstance(stmt, (FunctionCall, BinaryOp, Identifier)):
            return self.evaluate_expression(stmt)
        return DynamicValue()

    def current_type_for(self, name):
        current_name = self.emit_name(name)
        return self.type_env.get(current_name)

    def is_int_value(self, value):
        return type(value) is int
