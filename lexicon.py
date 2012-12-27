def time():
    a = set(['this', 'on', 'last', 'next'])
    b = set(['tuesday', 'thursday', 'friday', 'wednesday', 'monday','saturday','sunday','week','month','year','decade'])
    c = set([])
    for i in a:
        for j in b:
            str = i + " " + j
            c.add(str)
    return c
