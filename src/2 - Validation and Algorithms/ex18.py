def validar_sudoku(grade: list) -> bool:
    def valida_grupo(grupo: list) -> bool:
        nums = [num for num in grupo if num != 0]
        return len(nums) == len(set(nums)) and all(1 <= num <= 9 for num in nums)

    for linha in grade:
        if not valida_grupo(linha):
            return False

    for col in range(9):
        coluna = [grade[linha][col] for linha in range(9)]
        if not valida_grupo(coluna):
            return False

    for i in range(0, 9, 3):
        for j in range(0, 9, 3):
            bloco = [grade[x][y] for x in range(i, i + 3) for y in range(j, j + 3)]
            if not valida_grupo(bloco):
                return False

    return True
