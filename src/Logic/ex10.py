def duplicate_remove(elements:list)->list:
    views_elemnts = set()
    new_list = []
    for element in elements:
        if element not in views_elemnts:
            new_list.append(element)
            views_elemnts.add(element)
    return new_list
