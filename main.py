from flask import Flask
from routes.pages import pages_bp
from routes.devices import devices_bp
from routes.actions import actions_bp
from routes.logs_routes import logs_bp
from modules import scan as s


def create_app():
    app = Flask(__name__)

    app.register_blueprint(pages_bp)
    app.register_blueprint(devices_bp)
    app.register_blueprint(actions_bp)
    app.register_blueprint(logs_bp)

    return app


app = create_app()

if __name__ == "__main__":
    s.scan_network()
    app.run(host="0.0.0.0", port=5001)