def cpf_verify(cpf: str) -> bool:
    if len(cpf) != 11:
        return False
    else:
        cont = 0
        for i in cpf:
            if not i.isdigit():
                continue
            else:
                cont += 1
        return True if cont == 9 else False
