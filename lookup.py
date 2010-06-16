from global_session import global_session


def table_lookup(q, limit, request):

    r = global_session.database
    out = ''
    table = request[0]
    field = request[1]

    print 't:%s, f:%s' % (table, field)

    session = r.Session()
    obj = r.get_class(table)
    search_field = getattr(obj, field)
    filter = search_field.like(unicode('%' + q + '%'))

    data = session.query(search_field, obj.id).filter(filter).all()[:limit]

    for item in data:
        out += "%s|%s\n" % (getattr(item, field), item.id)
    session.close()

    return str(out)
