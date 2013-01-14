def time():
    a = set(['this', 'on', 'last', 'next'])
    b = set(['tuesday', 'thursday', 'friday', 'wednesday', 'monday','saturday','sunday','week','month','year','decade'])
    c = set([])
    for i in a:
        for j in b:
            str = i + " " + j
            c.add(str)
    return c

w_ignore = "Then Of Their ot A By The More While Even After At To On She Some One Monday Tuesday Thursday Wednesday Thursday Friday Saturday Sunday As I When His Mr Mrs Ms In New It But N This Dr There That They And If He For"
