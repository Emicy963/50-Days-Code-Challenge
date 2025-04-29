def cont_words(word: str)->dict:
    words = dict()
    for i in word:
        count_word = 0
        if i in words.keys:
            pass
        words.keys = i
        for j in word:
            if i==j:
                count_word+=1
        words.values = count_word
        count_word = 0
    return words
