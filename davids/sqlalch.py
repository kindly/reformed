
import widgets
import session

allwidgets = session.session.query(session.Widgets)

for widget in allwidgets:
    exec(widget.name + "=" + "widgets."+ widget.widgetType + "('" + widget.name + "')" )






#wee = widgets.Dropdownbox3("wee")
#wee.mappem()
#poo = widgets.Dropdownbox3("poo")
#poo.mappem()
