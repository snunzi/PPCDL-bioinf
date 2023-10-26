from flask import Blueprint

bp = Blueprint('analysisresults', __name__)

from app.analysisresults import routes
