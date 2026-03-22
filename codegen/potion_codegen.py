from parser.potion_parser import *

RESERVED_WORDS = {
    "true": "true",
    "false": "false",
    "none": "undefined",
}

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
    "dynamic": DynamicValue
}

REVERSE_TYPE_MAP = {
    int: "int",
    str: "str",
    bool: "bool",
    type(None): "none",
    PidValue: "pid",
    DynamicValue: "dynamic"
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
        self.functions = {}
        self.function_arities = {}
        self.function_params = {}
        self.global_var_names = set()
        self.uses_to_string_builtin = False

    def generate(self) -> str:
        self.collect_function_names_and_globals(self.ast)

        self.lines.append(f"-module({self.module_name}).")
        exported = ", ".join(f"{name}/{self.function_arities[name]}" for name in self.function_names)
        self.lines.append(f"-export([{exported}]).\n")

        # Define variáveis globais
        for var_name, value in self.global_vars:
            self.lines.append(f"-define({var_name.upper()}, {value}).")

        self.visit(self.ast)
        if self.uses_to_string_builtin:
            self.append_to_string_builtin()
        return "\n".join(self.lines)

    def collect_function_names_and_globals(self, node):
        if hasattr(node, "statements"):
            for stmt in node.statements:
                if isinstance(stmt, FunctionDef):
                    self.function_names.append(stmt.name)
                    self.function_arities[stmt.name] = len(stmt.params)  
                    self.function_params[stmt.name] = stmt.params
                    self.functions[stmt.name] = {
                        "params": stmt.params,
                        "body": stmt.body,
                    }
                elif isinstance(stmt, (ValDeclaration, VarDeclaration)):
                    self.global_var_names.add(stmt.name)
                    value = self.visit(stmt.value)
                    self.global_vars.append((stmt.name, value))

                    self.type_checking(stmt, scope = "global")

                    var_key = self.emit_name(stmt.name)
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
            if not isinstance(stmt, (ValDeclaration, VarDeclaration)):  # Globais já tratadas
                self.visit(stmt)

    def visit_ValDeclaration(self, node):
        return self.emit_binding(node)

    def visit_VarDeclaration(self, node):
        return self.emit_binding(node)

    def emit_binding(self, node):
        if self.inside_function:
            self.local_vars.add(node.name)
        var_name = self.emit_name(node.name)
        value_code = self.visit(node.value)

        self.type_checking(node, scope="local" if self.inside_function else "global")

        return f"{var_name} = {value_code}"

    def type_checking(self, node, scope = "local"):
        var_name = self.emit_name(node.name)
        evaluated_value = self.evaluate_expression(node.value)

        # Verificação de tipo, se houver anotação
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
        elif isinstance(node, LiteralNone):
            return None
        elif isinstance(node, BinaryOp):
            left = self.evaluate_expression(node.left)
            right = self.evaluate_expression(node.right)
            if left is UNKNOWN or right is UNKNOWN:
                return self.evaluate_unknown_binary(node.op)
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
            elif node.op == ">=":
                return left >= right
            elif node.op == "<=":
                return left <= right
            else:
                raise Exception(f"Operação não suportada: {node.op}")
        elif isinstance(node, Identifier):
            var_name = self.emit_name(node.name)
            if var_name not in self.variables:
                if self.inside_function and node.name in self.local_vars:
                    return UNKNOWN
                raise Exception(f"Variável '{node.name}' não declarada.")
            return self.variables[var_name]
        elif isinstance(node, FunctionCall):
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
                raise Exception(f"Função '{func_name}' espera {len(param_names)} argumento(s), recebeu {len(args)}.")

            # Criar um novo escopo de variáveis
            old_variables = self.variables.copy()
            self.variables = {}

            for param_name, arg_value in zip(param_names, args):
                self.variables[self.emit_name(param_name)] = arg_value

            result = self.evaluate_block(body)

            # Restaurar escopo anterior
            self.variables = old_variables

            return result

        elif isinstance(node, SendExpression):
            return DynamicValue()

        elif isinstance(node, ReceiveBlock):
            return DynamicValue()

        elif isinstance(node, MatchExpression):
            return DynamicValue()

        elif isinstance(node, SpawnExpression):
            # Retorna um placeholder de PID para fins de inferência
            return PidValue()

        elif isinstance(node, MapLiteral):
            return DynamicValue()

        else:
            raise Exception(f"Não sei avaliar: {node}")


    def evaluate_block(self, body):
        result = None
        for stmt in body:
            if isinstance(stmt, ReturnStatement):
                return self.evaluate_expression(stmt.value)
            result = self.evaluate_statement(stmt)
        return result

    def evaluate_unknown_binary(self, op):
        if op in ("==", "!=", ">", "<", ">=", "<="):
            return False
        return UNKNOWN

    def evaluate_statement(self, stmt):
        if isinstance(stmt, (ValDeclaration, VarDeclaration)):
            self.type_checking(stmt)
            return self.variables[self.emit_name(stmt.name)]
        if isinstance(stmt, IfBlock):
            condition = self.evaluate_expression(stmt.condition)
            branch = stmt.if_body if condition else (stmt.else_body or [])
            return self.evaluate_block(branch)
        if isinstance(stmt, PrintCall):
            self.evaluate_expression(stmt.value)
            return DynamicValue()
        if isinstance(stmt, (SendExpression, ReceiveBlock, MatchExpression, SpawnExpression, MapLiteral)):
            return self.evaluate_expression(stmt)
        if isinstance(stmt, FunctionCall):
            return self.evaluate_expression(stmt)
        if isinstance(stmt, BinaryOp):
            return self.evaluate_expression(stmt)
        if isinstance(stmt, Identifier):
            return self.evaluate_expression(stmt)
        return DynamicValue()


    def visit_FunctionDef(self, node):
        # === ARMAZENA FUNÇÃO PARA POSSIVEIS USO POSTERIORES ===
        self.functions[node.name] = {
            "params": node.params,
            "body": node.body
        }

        self.lines.append("")

        formatted_params = [self.emit_local_name(p) for p in node.params]
        param_str = ", ".join(formatted_params)
        self.lines.append(f"{node.name}({param_str}) ->")

        # === CONTROLE DE ESCOPO LOCAL ===
        prev_inside = self.inside_function
        prev_locals = self.local_vars
        self.inside_function = True
        self.local_vars = set(node.params)

        # === GERAÇÃO DO CORPO ===
        # body_lines = []
        # for stmt in node.body:
        #     if isinstance(stmt, ValDeclaration):
        #         self.local_vars.add(self.emit_name(stmt.name))
        #     print(f"STMT: {stmt}")
        #     code = self.visit(stmt)
        #     print(f"CODE: {code}")
        #     if code:
        #         body_lines.append(code)
        # print(f"BODY_LINE: {body_lines}")
        
        if not node.body:
            self.lines.append("    ok.")
        else:
            *stmts, last = node.body
            for stmt in stmts:
                code = self.visit(stmt)
                if code:
                    self.lines.append(f"    {code},")
            
            if isinstance(last, ReturnStatement):
                ret_code = self.visit(last.value)
                self.lines.append(f"    {ret_code}.")
            else:
                last_code = self.visit(last)
                self.lines.append(f"    {last_code or 'ok'}.")

        # === RESTAURA CONTEXTO ===
        self.inside_function = prev_inside
        self.local_vars = prev_locals


    def visit_FunctionCall(self, node: FunctionCall):
        if node.name == "to_string":
            if len(node.args) != 1:
                raise Exception(f"Função '{node.name}' espera 1 argumento(s), recebeu {len(node.args)}.")
            self.uses_to_string_builtin = True
            arg_code = self.visit(node.args[0])
            return f"potion_to_string_builtin({arg_code})"

        args_code = [self.visit(arg) for arg in node.args]
        return f"{node.name}({', '.join(args_code)})"

    def visit_SendExpression(self, node: SendExpression):
        target_code = self.visit(node.target)
        message_code = self.visit(node.message)
        return f"{target_code} ! {message_code}"

    def visit_SpawnExpression(self, node: SpawnExpression):
        call_code = self.visit(node.call)
        return f"spawn(fun () -> {call_code} end)"

    def visit_MapLiteral(self, node: MapLiteral):
        if not node.entries:
            return "#{}"
        parts = []
        for key, value in node.entries:
            value_code = self.visit(value)
            key_code = self.emit_map_key(key)
            parts.append(f"{key_code} => {value_code}")
        inner = ", ".join(parts)
        return f"#{{{inner}}}"

    def visit_ReceiveBlock(self, node: ReceiveBlock):
        binding_name = self.emit_local_name(node.var_name)
        prev_inside = self.inside_function
        prev_locals = self.local_vars.copy()
        self.inside_function = True
        self.local_vars = prev_locals | {node.var_name}

        body_lines = []
        if node.body:
            *stmts, last = node.body
            for stmt in stmts:
                code = self.visit(stmt)
                if code:
                    formatted = self.format_with_indent(code, "        ")
                    body_lines.append(f"{formatted},")
            last_code = self.visit(last) or 'ok'
            formatted_last = self.format_with_indent(last_code, "        ")
            body_lines.append(formatted_last)
        else:
            body_lines.append("        ok")

        self.inside_function = prev_inside
        self.local_vars = prev_locals

        inner = "\n".join(body_lines)
        return f"receive {binding_name} ->\n{inner}\n    end"

    def visit_MatchExpression(self, node: MatchExpression):
        value_code = self.visit(node.value)
        clauses_code = []
        for idx, clause in enumerate(node.clauses):
            clause_code = self.generate_match_clause(clause)
            if idx < len(node.clauses) - 1:
                clause_code += ";"
            clauses_code.append(clause_code)

        clauses_block = "\n".join(clauses_code) if clauses_code else "    _ ->\n        ok"
        return f"case {value_code} of\n{clauses_block}\nend"

    def generate_match_clause(self, clause: MatchClause):
        pattern_code = self.emit_pattern(clause.pattern)
        prev_locals = self.local_vars.copy()
        bindings = self.collect_pattern_bindings(clause.pattern)
        self.local_vars |= bindings

        clause_lines = []
        if clause.body:
            *stmts, last = clause.body
            for stmt in stmts:
                code = self.visit(stmt)
                if code:
                    formatted = self.format_with_indent(code, "        ")
                    clause_lines.append(f"{formatted},")
            last_code = self.visit(last) or 'ok'
            formatted_last = self.format_with_indent(last_code, "        ")
            clause_lines.append(formatted_last)
        else:
            clause_lines.append("        ok")

        self.local_vars = prev_locals

        clause_body = "\n".join(clause_lines)
        return f"    {pattern_code} ->\n{clause_body}"

    def collect_pattern_bindings(self, pattern):
        bindings = set()
        if isinstance(pattern, Identifier):
            if pattern.name != "_" and pattern.name not in self.global_var_names:
                bindings.add(pattern.name)
        elif isinstance(pattern, MapLiteral):
            for _, value in pattern.entries:
                bindings |= self.collect_pattern_bindings(value)
        return bindings

    def emit_pattern(self, pattern):
        if isinstance(pattern, Identifier):
            if pattern.name == "_":
                return "_"
            if pattern.name in self.global_var_names:
                return f"?{pattern.name.upper()}"
            return self.emit_local_name(pattern.name)
        if isinstance(pattern, LiteralBool):
            return self.visit_LiteralBool(pattern)
        if isinstance(pattern, LiteralInt):
            return self.visit_LiteralInt(pattern)
        if isinstance(pattern, LiteralStr):
            return self.visit_LiteralStr(pattern)
        if isinstance(pattern, LiteralNone):
            return self.visit_LiteralNone(pattern)
        if isinstance(pattern, MapLiteral):
            return self.emit_pattern_map(pattern)
        return self.visit(pattern)

    def emit_pattern_map(self, map_node: MapLiteral):
        if not map_node.entries:
            return "#{}"
        parts = []
        for key, value in map_node.entries:
            key_code = self.emit_map_key(key)
            value_code = self.emit_pattern(value)
            parts.append(f"{key_code} := {value_code}")
        inner = ", ".join(parts)
        return f"#{{{inner}}}"

    def visit_PrintCall(self, node):
        expr = self.visit(node.value)
        return f'io:format("~p~n", [{expr}])'

    def visit_LiteralBool(self, node):
        return "true" if node.value else "false"

    def visit_LiteralInt(self, node):
        return str(node.value)
    
    def visit_LiteralStr(self, node):
        return f'"{node.value}"'

    def visit_LiteralNone(self, node):
        return "undefined"

    def visit_Identifier(self, node):
        if node.name in RESERVED_WORDS:
            return RESERVED_WORDS[node.name]
        return self.emit_name(node.name)

    def visit_BinaryOp(self, node):
        if node.op == "+" and (self.is_string_expression(node.left) or self.is_string_expression(node.right)):
            left = self.visit(node.left)
            right = self.visit(node.right)
            return f"({left} ++ {right})"

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

    def emit_local_name(self, name):
        return name.capitalize()

    def emit_name(self, name):
        if self.inside_function:
            if name in self.local_vars:
                return self.emit_local_name(name)
            if name in self.global_var_names:
                return f"?{name.upper()}"
            return self.emit_local_name(name)

        if name in self.global_var_names:
            return f"?{name.upper()}"

        return self.emit_local_name(name)

    def format_with_indent(self, code, indent="    "):
        if not code:
            return indent.rstrip()
        return indent + code.replace("\n", f"\n{indent}")

    def emit_map_key(self, key: str) -> str:
        if key and key[0].islower() and all(ch.isalnum() or ch == '_' for ch in key):
            return key
        return f"'{key}'"

    def is_string_expression(self, node):
        if isinstance(node, LiteralStr):
            return True
        if isinstance(node, FunctionCall) and node.name == "to_string":
            return True
        if isinstance(node, BinaryOp) and node.op == "+":
            return self.is_string_expression(node.left) or self.is_string_expression(node.right)
        return False

    def append_to_string_builtin(self):
        self.lines.append("")
        self.lines.append("potion_to_string_builtin(Value) when is_list(Value) ->")
        self.lines.append("    Value;")
        self.lines.append("potion_to_string_builtin(Value) when is_integer(Value) ->")
        self.lines.append("    integer_to_list(Value);")
        self.lines.append("potion_to_string_builtin(Value) when is_boolean(Value) ->")
        self.lines.append("    atom_to_list(Value);")
        self.lines.append("potion_to_string_builtin(undefined) ->")
        self.lines.append('    "undefined";')
        self.lines.append("potion_to_string_builtin(Value) when is_atom(Value) ->")
        self.lines.append("    atom_to_list(Value);")
        self.lines.append("potion_to_string_builtin(Value) when is_binary(Value) ->")
        self.lines.append("    binary_to_list(Value);")
        self.lines.append("potion_to_string_builtin(Value) ->")
        self.lines.append('    lists:flatten(io_lib:format("~p", [Value])).')
