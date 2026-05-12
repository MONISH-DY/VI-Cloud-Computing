from flask import Flask
from config import Config
from datetime import timedelta
import os
import logging

# Azure Monitor / App Insights
from opencensus.ext.azure.log_exporter import AzureLogHandler

from routes.auth import auth_bp
from routes.files import files_bp

app = Flask(__name__)

# Setup Monitoring if connection string exists
APP_INSIGHTS_KEY = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
if APP_INSIGHTS_KEY:
    logger = logging.getLogger(__name__)
    logger.addHandler(AzureLogHandler(connection_string=APP_INSIGHTS_KEY))
    logger.info("Application Insights Monitoring enabled.")

app.config.from_object(Config)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

app.permanent_session_lifetime = timedelta(days=7)


# =====================================
# REGISTER ROUTES
# =====================================
app.register_blueprint(auth_bp)
app.register_blueprint(files_bp)


# =====================================
# START APP
# =====================================
if __name__ == "__main__":
    app.run(debug=True)