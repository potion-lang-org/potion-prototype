from parser.potion_parser import (
    Assignment,
    BinaryOp,
    ErlangImportStatement,
    ExternalModuleCall,
    FunctionCall,
    FunctionParam,
    Identifier,
    ImportStatement,
    IfBlock,
    LiteralBool,
    LiteralInt,
    ListLiteral,
    LiteralNone,
    LiteralStr,
    MapLiteral,
    MatchExpression,
    MemberAccess,
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


class TypedValue:
    def __init__(self, type_name):
        self.type_name = type_name


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
    RECEIVE_EXTRA_FIELDS = ["reply_to"]

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
        self.external_functions = {}
        self.imported_erlang_modules = set()

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
        if isinstance(value, TypedValue):
            return value.type_name
        return REVERSE_TYPE_MAP.get(type(value), "unknown")

    def placeholder_value_for_type(self, type_name):
        if type_name == "int":
            return 0
        if type_name == "str":
            return ""
        if type_name == "bool":
            return False
        if type_name == "none":
            return None
        if type_name == "pid":
            return PidValue()
        if type_name == "dynamic":
            return UNKNOWN
        return TypedValue(type_name)

    def param_names(self, params):
        return [param.name for param in params]

    def validate_function_param_annotations(self, params):
        for param in params:
            if not param.type_annotation:
                continue
            if param.type_annotation not in TYPE_MAP:
                raise Exception(
                    f"Tipo desconhecido em parâmetro '{param.name}': {param.type_annotation}"
                )

    def bind_function_params(self, params, arg_values=None):
        for idx, param in enumerate(params):
            emitted_name = self.emit_local_name(param.name)
            if arg_values is not None:
                value = arg_values[idx]
            elif param.type_annotation:
                value = self.placeholder_value_for_type(param.type_annotation)
            else:
                value = UNKNOWN

            if param.type_annotation:
                self.type_env[emitted_name] = param.type_annotation
            elif value is not UNKNOWN:
                inferred = self.infer_type(value)
                if inferred != "unknown":
                    self.type_env[emitted_name] = inferred

            self.variables[emitted_name] = value

    def validate_function_call_args(self, func_name, params, args):
        if len(args) != len(params):
            raise Exception(
                f"Função '{func_name}' espera {len(params)} argumento(s), recebeu {len(args)}."
            )

        for param, arg_value in zip(params, args):
            if not param.type_annotation or arg_value is UNKNOWN:
                continue
            actual_type = self.infer_type(arg_value)
            if actual_type == "unknown":
                continue
            if actual_type != param.type_annotation:
                raise Exception(
                    f"Erro de tipo em chamada de função '{func_name}': parâmetro '{param.name}' "
                    f"espera {param.type_annotation}, mas recebeu {actual_type}"
                )

    def register_erlang_import(self, module_name):
        self.imported_erlang_modules.add(module_name)

    def validate_erlang_module_imported(self, module_name):
        if module_name not in self.imported_erlang_modules:
            raise Exception(f"Módulo Erlang '{module_name}' não foi importado.")

    def receive_binding_placeholder(self, index):
        if index > 0 and self.RECEIVE_EXTRA_FIELDS[index - 1] == "reply_to":
            return PidValue()
        return UNKNOWN

    def validate_receive_block(self, node: ReceiveBlock):
        for clause in node.clauses:
            self.validate_receive_clause(clause)

    def validate_receive_clause(self, clause):
        if clause.is_any:
            if clause.bindings:
                raise Exception("Cláusula 'on any' não pode declarar bindings.")
            if clause.guard is not None:
                raise Exception("Cláusula 'on any' não pode ter guard.")
        else:
            if clause.tag is None:
                raise Exception("Cláusula de receive sem tag.")
            if len(clause.bindings[1:]) > len(self.RECEIVE_EXTRA_FIELDS):
                raise Exception(
                    f"receive on '{clause.tag}' suporta no máximo "
                    f"{1 + len(self.RECEIVE_EXTRA_FIELDS)} binding(s) nesta etapa."
                )

        prev_inside = self.inside_function
        prev_locals = self.local_vars.copy()
        prev_variables = self.variables.copy()
        prev_type_env = self.type_env.copy()

        try:
            self.inside_function = True
            self.local_vars = prev_locals | set(clause.bindings)
            self.variables = prev_variables.copy()
            self.type_env = prev_type_env.copy()

            for index, binding in enumerate(clause.bindings):
                self.variables[self.emit_local_name(binding)] = self.receive_binding_placeholder(index)

            if clause.guard is not None:
                guard_value = self.evaluate_expression(clause.guard)
                if guard_value is not UNKNOWN and not isinstance(guard_value, bool):
                    raise Exception("Guard de receive deve resultar em bool.")

            self.evaluate_block(clause.body)
        finally:
            self.inside_function = prev_inside
            self.local_vars = prev_locals
            self.variables = prev_variables
            self.type_env = prev_type_env

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
        if isinstance(node, MemberAccess):
            target = self.evaluate_expression(node.target)
            if target is UNKNOWN or isinstance(target, DynamicValue):
                return UNKNOWN
            if isinstance(target, dict):
                return target.get(node.field, UNKNOWN)
            return UNKNOWN
        if isinstance(node, ExternalModuleCall):
            self.validate_erlang_module_imported(node.module_name)
            for arg in node.args:
                self.evaluate_expression(arg)
            return DynamicValue()
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
                external = self.external_functions.get((func_name, len(args)))
                if external is None:
                    raise Exception(f"Função '{func_name}' não definida.")
                params = external["params"]
                self.validate_function_param_annotations(params)
                self.validate_function_call_args(func_name, params, args)
                return UNKNOWN

            func_def = self.functions[func_name]
            params = func_def["params"]
            body = func_def["body"]
            self.validate_function_param_annotations(params)
            self.validate_function_call_args(func_name, params, args)

            old_variables = self.variables.copy()
            old_type_env = self.type_env.copy()
            self.variables = {}
            self.type_env = {}
            self.bind_function_params(params, args)

            result = self.evaluate_block(body)
            self.variables = old_variables
            self.type_env = old_type_env
            return result

        if isinstance(node, ReceiveBlock):
            self.validate_receive_block(node)
            return DynamicValue()
        if isinstance(node, ListLiteral):
            for element in node.elements:
                self.evaluate_expression(element)
            return DynamicValue()
        if isinstance(node, (SendExpression, MatchExpression, MapLiteral)):
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
        if isinstance(stmt, ErlangImportStatement):
            self.register_erlang_import(stmt.module_name)
            return DynamicValue()
        if isinstance(stmt, IfBlock):
            condition = self.evaluate_expression(stmt.condition)
            branch = stmt.if_body if condition else (stmt.else_body or [])
            return self.evaluate_block(branch)
        if isinstance(stmt, PrintCall):
            self.evaluate_expression(stmt.value)
            return DynamicValue()
        if isinstance(stmt, (SendExpression, ReceiveBlock, MatchExpression, SpawnExpression, MapLiteral, ListLiteral, ExternalModuleCall)):
            return self.evaluate_expression(stmt)
        if isinstance(stmt, ImportStatement):
            return DynamicValue()
        if isinstance(stmt, (FunctionCall, BinaryOp, Identifier, MemberAccess)):
            return self.evaluate_expression(stmt)
        return DynamicValue()

    def current_type_for(self, name):
        current_name = self.emit_name(name)
        return self.type_env.get(current_name)

    def is_int_value(self, value):
        return type(value) is int
