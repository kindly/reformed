import selector
import http
import ajax

from form_cache import FormCache


form_cache = FormCache()
form_cache.reset()


urls = selector.Selector()
#urls.add('/login', POST=http.check_login, GET=http.check_login)
#urls.add('/reset_cache', GET=http.reset_cache)
#urls.add('/logout', GET=http.clear_authentication)
urls.add('/content/{path:any}', GET=http.static)
#urls.add('/export/{form}', GET=dataexport.export)  # FIXME
urls.add('/ajax', GET=ajax.process, POST=ajax.process)
