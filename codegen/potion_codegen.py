from parser.potion_parser import *

RESERVED_WORDS = {
    "true": "true",
    "false": "false",
    "none": "undefined",
}

TYPE_MAP = {
    "int": int,
    "str": str,
    "bool": bool
}

REVERSE_TYPE_MAP = {
    int: "int",
    str: "str",
    bool: "bool"
}

class ErlangCodegen:
    def __init__(self, ast, module_name="module_name"):
        self.ast = ast
        self.lines = []
        self.module_name = module_name
        self.function_names = []
        self.global_vars = []
        self.local_vars = set()
        self.inside_function = False
        self.type_env = {}
        self.variables = {}

    def generate(self) -> str:
        self.collect_function_names_and_globals(self.ast)

        self.lines.append(f"-module({self.module_name}).")
        exported = ", ".join(f"{name}/0" for name in self.function_names)
        self.lines.append(f"-export([{exported}]).\n")

        # Define variáveis globais
        for var_name, value in self.global_vars:
            self.lines.append(f"-define({var_name.upper()}, {value}).")

        self.visit(self.ast)
        return "\n".join(self.lines)

    def collect_function_names_and_globals(self, node):
        if hasattr(node, "statements"):
            for stmt in node.statements:
                if isinstance(stmt, FunctionDef):
                    self.function_names.append(stmt.name)
                elif isinstance(stmt, ValDeclaration):
                    value = self.visit(stmt.value)
                    self.global_vars.append((stmt.name, value))

                    self.type_checking(stmt, scope = "global")

                    var_key = self.format_variable(stmt.name)
                    real_val = self.evaluate_expression(stmt.value)
                    self.variables[var_key] = real_val

    def visit(self, node):
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f"No visit_{type(node).__name__} method")

    def visit_Program(self, node):
        for stmt in node.statements:
            if not isinstance(stmt, ValDeclaration):  # Variáveis já tratadas
                self.visit(stmt)

    def visit_ValDeclaration(self, node):
        var_name = self.format_variable(node.name)
        value_code = self.visit(node.value)

        self.type_checking(node, scope = "local")

        return f"{var_name} = {value_code}"

    def type_checking(self, node, scope = "local"):
        var_name = self.format_variable(node.name)
        evaluated_value = self.evaluate_expression(node.value)

        # Verificação de tipo, se houver anotação
        if node.type_annotation:
            expected_type = TYPE_MAP.get(node.type_annotation)
            if expected_type is None:
                raise Exception(f"Tipo desconhecido ({scope}) em '{node.name}': {node.type_annotation}")

            if not isinstance(evaluated_value, expected_type):
                actual_type = self.infer_type(evaluated_value)
                raise Exception(
                    f"Erro de tipo ({scope}) em '{node.name}': esperado {node.type_annotation}, mas recebeu {actual_type}"
                )
            # Armazena o tipo no ambiente de tipos
            self.type_env[var_name] = node.type_annotation

        else:
            # Inferir tipo automaticamente
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
        elif isinstance(node, LiteralStr):
            return node.value
        elif isinstance(node, LiteralBool):
            return node.value
        elif isinstance(node, BinaryOp):
            left = self.evaluate_expression(node.left)
            right = self.evaluate_expression(node.right)
            if node.op == "+":
                return left + right
            elif node.op == "-":
                return left - right
            elif node.op == "*":
                return left * right
            elif node.op == "/":
                return left / right
            elif node.op == "==":
                return left == right
            elif node.op == "!=":
                return left != right
            elif node.op == ">":
                return left > right
            elif node.op == "<":
                return left < right
            else:
                raise Exception(f"Operação não suportada: {node.op}")
        elif isinstance(node, VariableAccess):
            var_name = self.format_variable(node.name)
            if var_name not in self.variables:
                raise Exception(f"Variável '{node.name}' não declarada.")
            return self.variables[var_name]
        elif isinstance(node, Identifier):
            var_name = self.format_variable(node.name)
            if var_name not in self.variables:
                raise Exception(f"Variável '{node.name}' não declarada.")
            return self.variables[var_name]
        else:
            raise Exception(f"Não sei avaliar: {node}")


    def visit_FunctionDef(self, node):
        self.lines.append("")
        self.lines.append(f"{node.name}() ->")

        # setup contexto
        prev_inside = self.inside_function
        prev_locals = self.local_vars
        self.inside_function = True
        self.local_vars = set()

        # gerar body
        body_lines = []
        for stmt in node.body:
            if isinstance(stmt, ValDeclaration):
                self.local_vars.add(stmt.name)
            code = self.visit(stmt)
            if code:
                body_lines.append(code)

        if not body_lines:
            self.lines.append("    ok.")
        else:
            *stmts, last = node.body
            for s in stmts:
                code = self.visit(s)
                if code:
                    self.lines.append(f"    {code},")
            
            # Se o último é ReturnStatement, pega só o valor; senão, gera normalmente
            if isinstance(last, ReturnStatement):
                ret_code = self.visit(last.value)
                self.lines.append(f"    {ret_code}.")
            else:
                last_code = self.visit(last)
                self.lines.append(f"    {last_code}.")

        # restaurar contexto só DEPOIS de tudo estar gerado
        self.inside_function = prev_inside
        self.local_vars = prev_locals


    def visit_PrintCall(self, node):
        expr = self.visit(node.value)
        return f'io:format("~p~n", [{expr}])'

    def visit_LiteralBool(self, node):
        return "true" if node.value else "false"

    def visit_LiteralInt(self, node):
        return str(node.value)
    
    def visit_LiteralStr(self, node):
        return f'"{node.value}"'

    def visit_Literal(self, node):
        if isinstance(node, LiteralBool):
            return self.visit_LiteralBool(node)
        if isinstance(node, LiteralInt):
            return self.visit_LiteralInt(node)
        if isinstance(node.value, str) and node.value.startswith('"'):
            return f'"{node.value[1:-1]}"'
        return str(node.value)

    def visit_VariableAccess(self, node):
        return self.format_variable(node.name)
    
    def visit_Identifier(self, node):
        if node.name in RESERVED_WORDS:
            return RESERVED_WORDS[node.name]
        return self.format_variable(node.name)

    def visit_BinaryOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = self.map_operator(node.op)
        return f"({left} {op} {right})"

    def visit_IfBlock(self, node):
        cond = self.visit(node.condition)
        if_body = ",\n        ".join(self.visit(s) for s in node.if_body)
        if node.else_body:
            else_body = ",\n        ".join(self.visit(s) for s in node.else_body)
            return (
                f"case {cond} of\n"
                f"    true ->\n"
                f"        {if_body};\n"
                f"    _ ->\n"
                f"        {else_body}\n"
                f"end"
            )
        return (
            f"case {cond} of\n"
            f"    true ->\n"
            f"        {if_body};\n"
            f"    _ ->\n"
            f"        ok\n"
            f"end"
        )

    def visit_ReturnStatement(self, node):
        return self.visit(node.value)

    def map_operator(self, op):
        return {
            "+": "+",
            "-": "-",
            "*": "*",
            "/": "div"
        }.get(op, op)

    def format_variable(self, name):
        if self.inside_function and name in self.local_vars:
            return name.capitalize()
        return f"?{name.upper()}"


