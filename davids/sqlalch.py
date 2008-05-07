
import widgets
import session

widgetdict ={}

allwidgets = session.session.query(session.Widgets)
for widget in allwidgets:
      widgetdict[str(widget.name)] = getattr(widgets,widget.widgetType)(str(widget.name))  




#wee = widgets.Dropdownbox3("wee")
#wee.mappem()
#poo = widgets.Dropdownbox3("poo")
#poo.mappem()
