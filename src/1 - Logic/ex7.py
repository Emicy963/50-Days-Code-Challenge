def subsequent_increasing(sequence: list)->list:
    new_sequence = []
    for i in range(0, len(sequence)):
        if len(sequence)!=i+1:
            if sequence[i]<sequence[i+1]:
                new_sequence.append(sequence[i])
    if sequence[len(sequence)-1]<new_sequence[len(new_sequence)-1]:
        new_sequence.append(sequence[len(sequence)-1])
    return new_sequence
