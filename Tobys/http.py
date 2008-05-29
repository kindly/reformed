
def render(start_response, body):
    start_response("200 OK", [('Content-Type', 'text/html')])
    return [body]

