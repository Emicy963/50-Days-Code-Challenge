def calcular_expressao(expressao):
    import re

    expressao = expressao.replace(" ", "")
    tokens = re.findall(r"(\d+|\+|\-|\*|\/|\(|\))", expressao)

    def aplicar_operacao(operadores, valores):
        op = operadores.pop()
        b = valores.pop()
        a = valores.pop()
        if op == "+":
            valores.append(a + b)
        elif op == "-":
            valores.append(a - b)
        elif op == "*":
            valores.append(a * b)
        elif op == "/":
            valores.append(a / b)

    precedencia = {"+": 1, "-": 1, "*": 2, "/": 2}
    operadores = []
    valores = []

    for token in tokens:
        if token.isdigit():
            valores.append(int(token))
        elif token == "(":
            operadores.append(token)
        elif token == ")":
            while operadores[-1] != "(":
                aplicar_operacao(operadores, valores)
            operadores.pop()
        else:
            while (
                operadores
                and operadores[-1] != "("
                and precedencia[operadores[-1]] >= precedencia[token]
            ):
                aplicar_operacao(operadores, valores)
            operadores.append(token)

    while operadores:
        aplicar_operacao(operadores, valores)

    return valores[0] if valores else 0
