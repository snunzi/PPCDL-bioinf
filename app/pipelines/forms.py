from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, BooleanField, StringField, MultipleFileField, RadioField
from wtforms.validators import ValidationError, DataRequired, Length, Optional, Regexp
from flask_wtf.file import FileField, FileRequired
from app.models import User, Sample, Run
from werkzeug.utils import secure_filename

class VirusConfigForm(FlaskForm):
    library_choices = [('total','RiboZero RNA'),('small','Small RNA')]
    library_type = SelectField('Library Type', choices=library_choices, validators=[DataRequired()])
    blastx_run = RadioField('Perform blastx on Contigs?', choices=[('blastx','Yes'),('dont','No')])
    reads_out = RadioField('Output viral read fasta?', choices=[('output','Yes'),('dont','No')])
    submit = SubmitField(('Run'))

class IllMetaConfigForm(FlaskForm):
    db_choices = [('gyrB', 'gyrB')]
    DATABASE = SelectField('Choose reference database', choices=db_choices)
    submit = SubmitField(('Run'))

class MinMetaConfigForm(FlaskForm):
    barcode1 = TextAreaField(('Barcode1'), default='sample1')
    barcode2 = TextAreaField(('Barcode2'), default='sample2')
    barcode3 = TextAreaField(('Barcode3'), default='sample3')
    barcode4 = TextAreaField(('Barcode4'), default='sample4')
    barcode5 = TextAreaField(('Barcode5'), default='sample5')
    barcode6 = TextAreaField(('Barcode6'), default='sample6')
    barcode7 = TextAreaField(('Barcode7'), default='sample7')
    barcode8 = TextAreaField(('Barcode8'), default='sample8')
    barcode9 = TextAreaField(('Barcode9'), default='sample9')
    barcode10 = TextAreaField(('Barcode10'), default='sample10')
    barcode11 = TextAreaField(('Barcode11'), default='sample11')
    barcode12 = TextAreaField(('Barcode12'), default='sample12')
    submit = SubmitField(('Run'))
