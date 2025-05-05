def verify_password(password:str)->bool:
    has_upper = False
    has_lower = False
    has_num = False
    has_special = False

    if len(password)<8:
        return False

    for i in password:
        if i.isupper():
            has_upper=True
        elif i.islower():
            has_lower=True
        elif i.isdigit():
            has_num=True
        else:
            has_special=True

    return has_upper and has_lower and has_num and has_special
