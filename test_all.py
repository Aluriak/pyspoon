
import pyspoon

import color
import pipotron
from flask import Flask


if __name__ == '__main__':
    app = Flask(__name__)
    pyspoon.make_app(app, color.populate(app), pipotron.populate(app))
    app.run(debug=True, port=5000, host='127.0.0.1')
