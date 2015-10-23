import os
import sys
from urlparse import urlparse

import requests
from flask import (
    Flask,
    request,
)

app = Flask(__name__)

MATTERMOST_WEBHOOK_URL = None


@app.route('/', methods=['POST'])
def handler():
    nl = '\n'
    data = request.json

    url = data['url']
    project_name = data['project_name']

    # get project url
    parsed_url = urlparse(url)
    path_split = os.path.split(parsed_url.path)
    while True:
        path_split = os.path.split(path_split[0])
        if path_split[1] == 'group':
            break
    project_path = path_split[0]

    root_url = url[0:len(url) - len(parsed_url.path)]
    project_url = root_url + project_path
    text_parts = ['#### [{}]({})\n'.format(project_name, project_url)]

    text_parts.append(nl)
    text_parts.append(
        '**{}:** [{}]({})\n'
        .format(
            data['level'].upper(),
            data['culprit'],
            data['url'],
        )
    )
    text_parts.append(nl)
    try:
        exc = data['event']['sentry.interfaces.Exception']
    except KeyError:
        exc = None

    try:
        message = data['message'].split('\n')[0]
    except KeyError:
        message = None
    if message:
        text_parts.append('{}\n'.format(message.split(nl)[0]))

    if exc is not None:
        try:
            text_parts.append('\n')
            # exception type
            text_parts.append('#### {}\n'.format(exc['values'][0]['type']))
            # exception msg
            text_parts.append('`{}`'.format(exc['values'][0]['value']))
        except (KeyError, IndexError):
            pass

    requests.post(MATTERMOST_WEBHOOK_URL, json={'text': ''.join(text_parts)})
    return 'OK'


if __name__ == '__main__':
    MATTERMOST_WEBHOOK_URL = os.environ.get('MATTERMOST_WEBHOOK_URL')
    if not MATTERMOST_WEBHOOK_URL:
        print 'env variable MATTERMOST_WEBHOOK_URL not set'
        sys.exit()

    http_host = os.environ.get('HTTP_HOST', '127.0.0.1')
    http_port = os.environ.get('HTTP_PORT', 5000)
    try:
        http_port = int(http_port)
    except TypeError:
        print 'Invalid HTTP_PORT value: {}'.format(http_port)
        sys.exit()

    app.run(host=http_host, port=http_port)
