import whoosh
from whoosh.fields import *
from whoosh.analysis import StemmingAnalyzer
from dateutil.parser import parse


index_type_lookup = dict(
    value = ID,
    text = TEXT,
    keyword = KEYWORD,
    number = NUMERIC,
    datetime = DATETIME,
    boolean = BOOLEAN,
)


def make_schema(application):
    database = application.database
    schema_kw = dict(core_id = ID(stored = True, unique = True,
                                   field_boost = 10.0))

    for index_id, (table, search_action) in database.search_actions.iteritems():
        field_type = index_type_lookup[search_action.index_type]
        field_kw = {}
        if search_action.stem:
            field_kw["analyzer"] = StemmingAnalyzer()
        if search_action.weight:
            field_kw["field_boost"] = search_action.weight

        field = field_type(**field_kw)
        schema_kw[str(index_id)] = field

    return Schema(**schema_kw)


def index_database(application):

    database = application.database
    session = database.Session()
    index = application.text_index

    writer = index.writer()

    now = datetime.datetime.now()

    search_pending = database.get_class("search_pending")
    search_info = database.get_class("search_info")

    all_ids = session.query(search_pending._core_id).filter(search_pending.created_date < now).distinct().subquery()

    search_info = session.query(search_info._core_id, search_info.value, search_info.field)\
            .join((all_ids, all_ids.c._core_id == search_info._core_id))\
            .order_by(search_info._core_id).all()

    if not search_info:
        return

    current_core = search_info[0][0]
    current_kw = dict(core_id = unicode(current_core))

    lookup = database.search_actions

    for core_id, value, field in search_info:
        field_type = lookup[field][1].index_type
        if field_type == 'datetime':
            if value:
                value = parse(value)
        if field_type in ('text', 'keyword'):
            old_value = current_kw.get(str(field))
            if old_value:
                value = value + " " + old_value
        if value:
            current_kw[str(field)] = value

        if current_core <> core_id:
            if current_kw:
                writer.update_document(**current_kw)
                current_core = core_id
                current_kw = dict(core_id = unicode(current_core))
    else:
        if current_kw:
            writer.update_document(**current_kw)


    session.query(search_pending).filter(search_pending.created_date < now).delete()

    try:
        writer.commit()
    except Exception:
        session.rollback()
        writer.cancel()
        raise
    session.commit()
    session.close()

    ##searcher = index.searcher()

    ##myquery = Term("core_id", u"10")
    ##myquery = Term(str(database.search_names["id"]), u"peter")
    ##res = searcher.search(myquery)
    ##for a in res:
    ##    print a


