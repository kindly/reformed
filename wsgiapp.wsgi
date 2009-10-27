import sys
import os

sys.stdout = sys.stderr
this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(this_dir)

from reformed.reformed import reformed 
reformed.scheduler_thread.start()
import web

application = web.WebApplication()

