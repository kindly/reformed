import selector
import form
import http
import dataexport
import reformed
from form_cache import FormCache

# get our data up
reformed.data = reformed.Database()
reformed.data.create_tables()

form_cache = FormCache()
form_cache.reset()


urls = selector.Selector()
urls.add('/list', GET=form.list)
urls.add('/form/{form_id:digits}/{record_id:digits}[/{sub_data:custom}][;{cmd}]', POST=form.save, GET=form.save)
urls.add('/login', POST=http.check_login, GET=http.check_login)
urls.add('/reset_cache', GET=http.reset_cache)
urls.add('/logout', GET=http.clear_authentication)
urls.add('/content/{path:any}', GET=http.static)
urls.add('/export/{form}', GET=dataexport.export)  # FIXME
