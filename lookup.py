import reformed.reformed as r


def table_lookup(q, limit, request, http_session):

    out = ''
    table = request[0]
    field = request[1]

    print 't:%s, f:%s' % (table, field)

    session = r.reformed.Session()
    obj = r.reformed.get_class(table)
    search_field = getattr(obj, field)
    filter = search_field.like(unicode(q + '%'))

    data = session.query(search_field).filter(filter).all()[:limit]

    for item in data:
        out += getattr(item, field) + '\n'
    session.close()

    return str(out)
