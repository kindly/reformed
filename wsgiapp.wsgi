import sys
import os
import beaker.middleware

sys.stdout = sys.stderr
this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(this_dir)

from reformed.reformed import reformed 
reformed.scheduler_thread.start()
import web

app = web.WebApplication()
application = beaker.middleware.SessionMiddleware(app, {"session.type": "memory",
                                                        "session.auto": True})

