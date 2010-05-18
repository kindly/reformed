#FIXME this should be via a config file
application_dir = 'bug'

import sys
import os
import beaker.middleware

sys.stdout = sys.stderr
this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(this_dir)

import application
app = application.Application(application_dir)

import web
app = web.WebApplication(app)
application = beaker.middleware.SessionMiddleware(app, {"session.type": "memory",
                                                        "session.auto": True})

