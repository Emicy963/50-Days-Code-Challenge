def gerar_senhas(caracteres: dict, comprimento: int, criterios: list) -> str:
    import random

    if not criterios:
        return "Selecione ao menos um critério."

    caracteres_possiveis = ""
    for criterio in criterios:
        caracteres_possiveis += caracteres[criterio]

    senha = [random.choice(caracteres[criterio]) for criterio in criterios]

    senha += [
        random.choice(caracteres_possiveis) for _ in range(comprimento - len(senha))
    ]

    random.shuffle(senha)

    return "".join(senha)


def salvar_senha(senhas: list, nome_do_arquivo="minhas_senhas.txt") -> None:
    with open(nome_do_arquivo, "a") as arquivo:
        for senha in senhas:
            arquivo.write(senha + "\n")
    print("Senha salva com sucesso!")
