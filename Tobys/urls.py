import selector
import form

urls = selector.Selector()
urls.add('/list/', GET=form.list)
urls.add('/view/{form_id}/{table_id}', POST=form.view, GET=form.view)
#urls.add('/blog/;create_form', POST=view.create, GET=view.list)
#urls.add('/blog/{id}/;edit_form', GET=view.member_get, POST=view.member_update)

