from flask import Blueprint

bp = Blueprint('pipelines', __name__)

from app.pipelines import routes
