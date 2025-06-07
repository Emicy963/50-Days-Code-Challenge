import random


def escolher_palavra():
    palavras = [
        "python",
        "programacao",
        "computador",
        "algoritmo",
        "desenvolvimento",
        "openai",
    ]
    return random.choice(palavras)


def mostrar_palavra(palavra, letras_corretas):
    resultado = ""
    for letra in palavra:
        if letra in letras_corretas:
            resultado += letra + " "
        else:
            resultado += "_ "
    return resultado.strip()


def jogar_forca():
    palavra = escolher_palavra()
    letras_corretas = set()
    letras_erradas = set()
    tentativas_maximas = 6
    tentativas = 0

    print("Bem-vindo ao Jogo da Forca!")
    print("Adivinhe a palavra (dica: temas de tecnologia/programação)")

    while True:
        print("\n" + mostrar_palavra(palavra, letras_corretas))
        print(f"Letras erradas: {' '.join(letras_erradas)}")
        print(f"Tentativas restantes: {tentativas_maximas - tentativas}")

        if "_" not in mostrar_palavra(palavra, letras_corretas):
            print("\nParabéns! Você acertou a palavra!")
            break

        if tentativas >= tentativas_maximas:
            print(f"\nGame over! A palavra era: {palavra}")
            break

        palpite = input("Digite uma letra: ").lower()

        if len(palpite) != 1 or not palpite.isalpha():
            print("Por favor, digite apenas uma letra válida.")
            continue

        if palpite in letras_corretas or palpite in letras_erradas:
            print("Você já tentou esta letra. Tente outra.")
            continue

        if palpite in palavra:
            letras_corretas.add(palpite)
            print("Letra correta!")
        else:
            letras_erradas.add(palpite)
            tentativas += 1
            print("Letra incorreta!")


if __name__ == "__main__":
    jogar_forca()
