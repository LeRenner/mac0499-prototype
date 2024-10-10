import flask
import logging
from flask import request, Response
import requests

def runMiddleware(torMiddlewarePort, localRequestsPort):
    app = flask.Flask(__name__)

    # Set up logging to a file for Flask
    handler = logging.FileHandler('logs/middleware.log')
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    @app.after_request
    def add_custom_header(response):
        # Add a custom header
        response.headers['Tor-Middleware-Header'] = 'True'
        return response

    @app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
    @app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
    def proxy(path):
        # Forward the request to the local server
        url = f'http://localhost:{localRequestsPort}/{path}'

        forwardHeaders = {key: value for key, value in request.headers if key != 'Host'}
        forwardHeaders['Tor-Middleware-Header'] = 'True'

        print(f"Proxying request to {url} with headers: {forwardHeaders}")
        
        # Forward the request with filtered headers
        response = requests.request(
            method=request.method,
            url=url,
            headers=forwardHeaders,
            data=request.get_data(),
            allow_redirects=False
        )

        # Create a response object to return to the client
        proxy_response = Response(
            response.content,
            response.status_code,
            response.headers.items()
        )
        return proxy_response

    app.run(host="localhost", port=torMiddlewarePort)


