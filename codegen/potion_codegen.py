from parser.potion_parser import *
from semantic.potion_semantic import DynamicValue, PidValue, SemanticAnalyzer, UNKNOWN

RESERVED_WORDS = {
    "true": "true",
    "false": "false",
    "none": "undefined",
}

class ErlangCodegen(SemanticAnalyzer):
    def __init__(self, ast, module_name="module_name"):
        super().__init__()
        self.ast = ast
        self.lines = []
        self.module_name = module_name
        self.function_names = []
        self.global_vars = []
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
            if isinstance(node, VarDeclaration):
                self.mutable_vars.add(node.name)
                self.var_versions.setdefault(node.name, 0)
        var_name = self.emit_name(node.name)
        value_code = self.visit(node.value)

        self.type_checking(node, scope="local" if self.inside_function else "global")

        return f"{var_name} = {value_code}"

    def visit_Assignment(self, node):
        if not self.inside_function:
            raise Exception(f"Reatribuição não suportada fora de função: '{node.name}'")
        if node.name not in self.mutable_vars:
            raise Exception(f"Variável '{node.name}' não foi declarada com var.")
        if node.name in self.global_var_names:
            raise Exception(f"Reatribuição global ainda não é suportada: '{node.name}'")

        expected_type = self.current_type_for(node.name)
        evaluated_value = self.evaluate_expression(node.value)
        value_code = self.visit(node.value)
        next_version = self.var_versions.get(node.name, 0) + 1
        next_name = self.emit_versioned_name(node.name, next_version)

        if expected_type is not None:
            if evaluated_value is not UNKNOWN and self.infer_type(evaluated_value) != expected_type:
                actual_type = self.infer_type(evaluated_value)
                raise Exception(
                    f"Erro de tipo (local) em reatribuição de '{node.name}': esperado {expected_type}, mas recebeu {actual_type}"
                )
            self.type_env[next_name] = expected_type
        elif evaluated_value is not UNKNOWN:
            inferred = self.infer_type(evaluated_value)
            if inferred != "unknown":
                self.type_env[next_name] = inferred

        self.var_versions[node.name] = next_version
        self.variables[next_name] = evaluated_value

        return f"{next_name} = {value_code}"

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
        prev_mutable = self.mutable_vars.copy()
        prev_versions = self.var_versions.copy()
        self.inside_function = True
        self.local_vars = set(node.params)
        self.mutable_vars = set()
        self.var_versions = {}

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
        self.mutable_vars = prev_mutable
        self.var_versions = prev_versions


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
        merge_vars = self.collect_assigned_mutables(node.body)
        start_versions = self.var_versions.copy()
        self.inside_function = True
        self.local_vars = prev_locals | {node.var_name}
        body_code, end_versions = self.emit_branch_body(node.body, merge_vars, start_versions)

        self.inside_function = prev_inside
        self.local_vars = prev_locals
        self.var_versions = start_versions

        inner = self.format_with_indent(body_code, "        ")
        receive_code = f"receive {binding_name} ->\n{inner}\n    end"
        return self.wrap_control_flow_with_merge(receive_code, merge_vars, [end_versions])

    def visit_MatchExpression(self, node: MatchExpression):
        value_code = self.visit(node.value)
        merge_vars = self.collect_assigned_mutables(
            [clause_stmt for clause in node.clauses for clause_stmt in clause.body]
        )
        start_versions = self.var_versions.copy()
        clauses_code = []
        branch_versions = []
        for idx, clause in enumerate(node.clauses):
            clause_code, end_versions = self.generate_match_clause(clause, merge_vars, start_versions)
            if idx < len(node.clauses) - 1:
                clause_code += ";"
            clauses_code.append(clause_code)
            branch_versions.append(end_versions)

        clauses_block = "\n".join(clauses_code) if clauses_code else "    _ ->\n        ok"
        self.var_versions = start_versions
        case_code = f"case {value_code} of\n{clauses_block}\nend"
        return self.wrap_control_flow_with_merge(case_code, merge_vars, branch_versions)

    def generate_match_clause(self, clause: MatchClause, merge_vars, start_versions):
        self.var_versions = start_versions.copy()
        pattern_code = self.emit_pattern(clause.pattern)
        prev_locals = self.local_vars.copy()
        bindings = self.collect_pattern_bindings(clause.pattern)
        self.local_vars |= bindings
        clause_body, end_versions = self.emit_branch_body(clause.body, merge_vars, start_versions)

        self.local_vars = prev_locals

        formatted_body = self.format_with_indent(clause_body, "        ")
        return f"    {pattern_code} ->\n{formatted_body}", end_versions

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
        merge_vars = self.collect_assigned_mutables((node.if_body or []) + (node.else_body or []))
        start_versions = self.var_versions.copy()
        if_body, if_versions = self.emit_branch_body(node.if_body, merge_vars, start_versions)
        if node.else_body:
            else_body, else_versions = self.emit_branch_body(node.else_body, merge_vars, start_versions)
            case_code = (
                f"case {cond} of\n"
                f"    true ->\n"
                f"        {if_body};\n"
                f"    _ ->\n"
                f"        {else_body}\n"
                f"end"
            )
            self.var_versions = start_versions
            return self.wrap_control_flow_with_merge(case_code, merge_vars, [if_versions, else_versions])
        else_body, else_versions = self.emit_branch_body([], merge_vars, start_versions)
        case_code = (
            f"case {cond} of\n"
            f"    true ->\n"
            f"        {if_body};\n"
            f"    _ ->\n"
            f"        {else_body}\n"
            f"end"
        )
        self.var_versions = start_versions
        return self.wrap_control_flow_with_merge(case_code, merge_vars, [if_versions, else_versions])

    def visit_ReturnStatement(self, node):
        return self.visit(node.value)

    def map_operator(self, op):
        return {
            "+": "+",
            "-": "-",
            "*": "*",
            "/": "div"
        }.get(op, op)

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

    def collect_assigned_mutables(self, statements):
        assigned = []
        for stmt in statements or []:
            if isinstance(stmt, Assignment) and stmt.name in self.mutable_vars:
                assigned.append(stmt.name)
            elif isinstance(stmt, IfBlock):
                assigned.extend(self.collect_assigned_mutables(stmt.if_body))
                assigned.extend(self.collect_assigned_mutables(stmt.else_body or []))
            elif isinstance(stmt, MatchExpression):
                for clause in stmt.clauses:
                    assigned.extend(self.collect_assigned_mutables(clause.body))
            elif isinstance(stmt, ReceiveBlock):
                assigned.extend(self.collect_assigned_mutables(stmt.body))
        return list(dict.fromkeys(assigned))

    def emit_merge_return_expr(self, merge_vars):
        values = [self.emit_name(name) for name in merge_vars]
        if not values:
            return "ok"
        if len(values) == 1:
            return values[0]
        return "{" + ", ".join(values) + "}"

    def emit_merge_target(self, merge_vars, branch_versions):
        targets = []
        for name in merge_vars:
            next_version = self.next_merge_version(name, branch_versions)
            targets.append(self.emit_versioned_name(name, next_version))
        if len(targets) == 1:
            return targets[0]
        return "{" + ", ".join(targets) + "}"

    def wrap_control_flow_with_merge(self, code, merge_vars, branch_versions):
        if not merge_vars:
            return code

        target = self.emit_merge_target(merge_vars, branch_versions)
        for name in merge_vars:
            current_name = self.emit_name(name)
            next_version = self.next_merge_version(name, branch_versions)
            next_name = self.emit_versioned_name(name, next_version)
            self.var_versions[name] = next_version
            if current_name in self.type_env:
                self.type_env[next_name] = self.type_env[current_name]
            self.variables[next_name] = UNKNOWN
        return f"{target} = {code}"

    def emit_branch_body(self, statements, merge_vars, start_versions):
        self.var_versions = start_versions.copy()
        if not statements:
            return self.emit_merge_return_expr(merge_vars) if merge_vars else "ok", self.var_versions.copy()

        lines = []
        *stmts, last = statements
        for stmt in stmts:
            code = self.visit(stmt)
            if code:
                lines.append(code)
        last_code = self.visit(last) or "ok"
        if merge_vars:
            lines.append(last_code)
            lines.append(self.emit_merge_return_expr(merge_vars))
        else:
            lines.append(last_code)
        return ",\n        ".join(lines), self.var_versions.copy()

    def next_merge_version(self, name, branch_versions):
        max_version = self.var_versions.get(name, 0)
        for versions in branch_versions:
            max_version = max(max_version, versions.get(name, 0))
        return max_version + 1

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
