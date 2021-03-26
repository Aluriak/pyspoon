import uuid
import json
import random
import itertools
from PIL import Image
from flask import Flask, request, Response


def spoon_text(message:str) -> dict:
    return {"payload": {"spoon": { "id": "Say", "text": message }}}

def spoon_image(url:str, *, duration:float=5) -> dict:
    return {"payload": {"spoon": {
            "viewerId": "Image",
            "id": "DisplayImage",
            "imagePath": url,
            "duration": duration
    }}}
def spoon_wait(duration:float=5) -> dict:
    return {"payload": { "spoon": {
                "id": "Wait",
                "duration": duration,
    }}}

def make_app(app, *callbacks_list:{str: callable} or callable, route:str='/') -> Flask:
    callbacks = {}
    for cb in callbacks_list:
        if isinstance(cb, dict):
            for intent, func in cb.items():
                callbacks[intent] = func
        else:
            callbacks = cb
            break

    def make_func(callbacks):
        def respond():
            print('REQUEST:', request.json)
            intent = request.json['queryResult']['intent']['displayName']
            print('INTENT:', intent, callbacks)
            if callable(callbacks):  # call the callable, whatever the intent
                callback = callbacks
            elif intent in callbacks:  # match intent
                callback = callbacks[intent]
            else:  # not handled
                print('Unhandled intent:', intent)
                return Response(response=json.dumps({"fulfillmentMessages": []}), mimetype='application/json', status=202)
            data = callback(intent, query=request.json['queryResult'])
            if isinstance(data, (list, tuple)):
                data = list(data)
            elif isinstance(data, dict) and 'payload' in data:
                data = [data]
            else:
                raise TypeError(f"Unhandled return value of type {type(data)} for Spoon callback: {repr(data)}")
            data = {"fulfillmentMessages": data}
            print('DATA:', data)
            return Response(response=json.dumps(data), mimetype='application/json', status=202)
        respond.__name__ = 'generated_response_func__' + str(uuid.uuid4().hex)
        return respond
    # return data, 200
    return app.route(route, methods=['POST'])(make_func(callbacks))

