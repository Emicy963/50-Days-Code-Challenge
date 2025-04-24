def cpf_verify(cpf: str)->bool:
    if len(cpf)!=11:
        return False
    else:
        for i in cpf:
            if i.is_integer():
                return True   
            else:
                return False
