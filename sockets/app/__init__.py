#!/usr/bin/env python
# -*- coding: utf8 -*-

import os, sys, time, random
from threading import Lock

from flask import Flask
from flask import (
    render_template,
    request
)
from flask_socketio import (
    SocketIO,
    Namespace,
    emit
)


DOCKER_EVENTS = (
    'attach',
    'commit',
    'copy',
    'create',
    'destroy',
    'detach',
    'die',
    'exec_create',
    'exec_detach',
    'exec_die',
    'exec_start',
    'export',
    'health_status',
    'kill',
    'oom',
    'pause',
    'rename',
    'resize',
    'restart',
    'start',
    'stop',
    'top',
    'unpause',
    'update',
)

thread = None
thread_lock = Lock()


app = Flask(
    __name__,
    instance_relative_config=True,
)

socketio = SocketIO(app)

def create_app():
    app.config.from_mapping(
        SECRET_KEY=b'\x9e|\t\xe8V\xdb\x974{\x1aZz\xe9G\xea\x95\xd6\xfa\xcf`\x7f\\*\n',
    )
    try: os.makedirs(app.instance_path)
    except OSError as err: pass

    socketio.init_app(app)

    register_blueprints(app)
    register_endpoints(app)
    register_protocol(socketio)
    return app

def register_blueprints(app):
    pass

def register_endpoints(app):
    @app.route('/')
    def index():
        return render_template('index.html', **locals())

def register_protocol(socketio):

    def container_event_task(container_id):
        # - get container by id
        # for event in client.events(decode=True):
        #     emit('event', event, namespace='container')
        event_ptr = 0
        while True:
            event = DOCKER_EVENTS[event_ptr]
            socketio.emit(
                'state_change',
                {
                    'container_id': container_id,
                    'container_state': event,
                },
                namespace='/container'
            )
            event_ptr = (event_ptr + 1) % len(DOCKER_EVENTS)
            time.sleep(random.randint(1, 3))


    @socketio.on('connect', namespace='/container')
    def handle_connect():
        print('Client connected')
        pass

    @socketio.on('disconnect', namespace='/container')
    def handle_disconnect():
        print('Client disconnected')
        # global thread
        # with thread_lock:
        #     if thread is not None:
        #         stopped.set()

    @socketio.on('start', namespace='/container')
    def handle_start(data):
        print('start', data)

        global thread
        # since docker client is listening to all events on each container,
        # the container ID is not used 
        container_id = data['container_id']
        with thread_lock:
            if thread is None:
                thread = socketio.start_background_task(container_event_task, container_id)


if __name__ == '__main__':
    app = create_app()
    socketio.run(app, debug=True)
