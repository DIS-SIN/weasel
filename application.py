from flask import Flask, redirect, url_for
import os
from code import weasel
def create_app():
    app = Flask(__name__)
    app.register_blueprint(weasel.bp)
    @app.route('/')
    def index():
        return redirect(url_for('weasel.render_ermine'))
    return app
app = create_app()
app.run(host = '0.0.0.0', port=5052)
