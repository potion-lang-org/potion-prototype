from lexer.potion_lexer import tokenize
from parser.potion_parser import Parser

def parse_potion_file(file_path):
    """
    Lê um arquivo .potion, faz a análise léxica e sintática, e retorna a AST.
    
    :param file_path: Caminho para o arquivo .potion
    :return: AST gerada pelo parser
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    tokens = tokenize(source_code)
    parser = Parser(tokens)
    ast = parser.parse()  # ou parser.program() dependendo do nome que você deu
    return ast
