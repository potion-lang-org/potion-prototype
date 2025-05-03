from potion_parser import *

RESERVED_WORDS = {
    "true": "true",
    "false": "false",
    "none": "undefined",
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
        value = self.visit(node.value)
        return f"{var_name} = {value}"

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

        # restaurar contexto
        self.inside_function = prev_inside
        self.local_vars = prev_locals

        if not body_lines:
            self.lines.append("    ok.")
        else:
            # último é retorno, anteriores com vírgula
            *stmts, last = body_lines
            for s in stmts:
                self.lines.append(f"    {s},")
            self.lines.append(f"    {last}.")

    def visit_PrintCall(self, node):
        expr = self.visit(node.value)
        return f'io:format("~p~n", [{expr}])'

    def visit_LiteralBool(self, node):
        return "true" if node.value else "false"

    def visit_LiteralInt(self, node):
        return str(node.value)

    def visit_Literal(self, node):
        if isinstance(node, LiteralBool):
            return self.visit_LiteralBool(node)
        if isinstance(node, LiteralInt):
            return self.visit_LiteralInt(node)
        if isinstance(node.value, str) and node.value.startswith('"'):
            return f'"{node.value[1:-1]}"'
        return str(node.value)

    def visit_Identifier(self, node):
        if node.name in RESERVED_WORDS:
            return RESERVED_WORDS[node.name]
        if self.inside_function and node.name in self.local_vars:
            return self.format_variable(node.name)
        return f"?{node.name.upper()}"

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
        # variáveis locais capitalizadas, globais minúsculas
        return name.capitalize() if self.inside_function else name.lower()
