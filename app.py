"""
app.py
------
Main entry point for the AI Business Assistant.

Run with:
    python app.py

This registers all blueprints, initializes the database, and adds
app-level error handlers so the app never crashes ungracefully.
"""

import os
import webbrowser
from threading import Timer

from flask import Flask, render_template

from config import Config
from database.database import init_db

from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.chatbot import chatbot_bp
from routes.business import business_bp
from routes.prediction import prediction_bp
from routes.reports import reports_bp
from routes.analyzer import analyzer_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure required folders exist
    try:
        if not os.environ.get("VERCEL"):
            os.makedirs(
                os.path.join(app.root_path, "instance"),
                exist_ok=True
            )
    except OSError:
        pass

    try:
        os.makedirs(Config.REPORTS_DIR, exist_ok=True)
    except OSError:
        pass

    # Database initialization
    init_db(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(business_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(analyzer_bp)

    # Inject global variables into templates
    @app.context_processor
    def inject_globals():
        return {"demo_mode": Config.DEMO_MODE}

    # Health / diagnostic endpoint
    @app.route("/api/health")
    def health():
        import traceback

        from database.database import db
        from database.models import (
            User,
            Conversation,
            Message,
            BusinessPlan,
            Prediction
        )

        try:
            engine_str = str(db.engine.url)
            safe_engine = engine_str

            if "@" in safe_engine:
                parts = safe_engine.split("@")
                safe_engine = f"***@{parts[1]}"

            users = User.query.all()
            user_list = []

            for u in users:
                c_count = Conversation.query.filter_by(
                    user_id=u.id
                ).count()

                p_count = Prediction.query.filter_by(
                    user_id=u.id
                ).count()

                bp_count = BusinessPlan.query.filter_by(
                    user_id=u.id
                ).count()

                user_list.append({
                    "id": u.id,
                    "email": u.email,
                    "name": u.name,
                    "conversations": c_count,
                    "predictions": p_count,
                    "plans": bp_count
                })

            conv_count = Conversation.query.count()
            msg_count = Message.query.count()
            plan_count = BusinessPlan.query.count()
            pred_count = Prediction.query.count()

            return {
                "status": "ok",
                "database_engine": safe_engine,
                "is_sqlite": "sqlite" in safe_engine,
                "users": user_list,
                "conversations": conv_count,
                "messages": msg_count,
                "plans": plan_count,
                "predictions": pred_count
            }

        except Exception as exc:
            return {
                "status": "error",
                "error": str(exc),
                "trace": traceback.format_exc()
            }, 200

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template(
            "error.html",
            code=404,
            message="Page not found."
        ), 404

    @app.errorhandler(500)
    def server_error(e):
        import traceback

        err_msg = traceback.format_exc()

        return render_template(
            "error.html",
            code=500,
            message=f"Internal Server Error: {err_msg[-400:]}"
        ), 500

    return app


# Create Flask application
app = create_app()


# Open Google Chrome automatically
def open_chrome():
    url = "http://127.0.0.1:5000"

    try:
        chrome = webbrowser.get("chrome")
        chrome.open(url)
    except webbrowser.Error:
        # Fallback: Open using the default browser
        webbrowser.open(url)


if __name__ == "__main__":

    print("=" * 60)
    print(" AI-Powered Business Entrepreneur Assistant")
    print(
        f" Demo Mode: "
        f"{'ON (no live LLM API key configured)' if Config.DEMO_MODE else 'OFF (live LLM enabled)'}"
    )
    print(" Running at: http://127.0.0.1:5000")
    print(" Opening Google Chrome automatically...")
    print("=" * 60)

    # Prevent Flask reloader from opening Chrome twice
    if Config.DEBUG:
        use_reloader = False
    else:
        use_reloader = False

    # Open Chrome after Flask starts
    Timer(1.5, open_chrome).start()

    # Start Flask server
    app.run(
        debug=Config.DEBUG,
        host="127.0.0.1",
        port=5000,
        threaded=True,
        use_reloader=use_reloader
    )
