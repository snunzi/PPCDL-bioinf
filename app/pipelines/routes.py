import os
from os import listdir
from os.path import exists, isfile, join
from flask import render_template, flash, redirect, url_for, request, send_from_directory, current_app, json, render_template_string
from flask_login import current_user, login_required
from app import db
from app.models import User, Sample, Run, ReadSummary, PathoscopeSummary, BlastnFull
from app.pipelines import bp
from app.pipelines.forms import VirusConfigForm, MinMetaConfigForm, IllMetaConfigForm
from werkzeug.utils import secure_filename
import pathlib
import fileinput
import sys
from threading import Thread
from app.tasks import snake_virus, snake_minmeta, snake_illmeta
import flask_excel as excel
import pyexcel as pe
import shutil
from shutil import copyfile

@bp.route('/user/<username>/VirusPipe/<run>', methods = ['GET', 'POST'])
@login_required
def viruspipe(username, run):
	form = VirusConfigForm()
	user = User.query.filter_by(username=username).first_or_404()
	if form.validate_on_submit():
		#Get the Run
		query = Run.query.filter_by(run_id=run).first()
		run_dict = query.to_dict()
		path = os.path.join(current_app.config['UPLOAD_FOLDER'],run_dict['run_id'])

		#Generate Sample file
		samples = Sample.query.filter_by(run_id=query.id).all()
		with open(os.path.join(path, "samples.tsv"), 'w') as sample_file:
			print("sample\thost", file=sample_file)
			for sample in samples:
				sample_dict = sample.to_dict()
				print(sample_dict['sample_id'] + "\t" + sample_dict['host'], file=sample_file)

		#Generate config file
		config_dict = request.form.to_dict()
		config_dict.update(run_dict)
		config_dict["user_email"] = current_user.email
		del config_dict['id']
		del config_dict['description']
		del config_dict['share']
		with open(os.path.join(path, "config.yaml"), 'w') as config_file:
			for line in fileinput.input(os.path.join(current_app.config['CONFIG_FOLDER'], "pipelines/virus/config.yaml"), inplace=False):
				line = line.rstrip()
				if not line:
					continue
				for f_key, f_value in config_dict.items():
					if f_key in line:
						line = line.replace(f_key, str(f_value))
				print(line, file = config_file)
		snakefile = os.path.join(current_app.config['PIPELINE_FOLDER'], "virus/Snakefile")
		thread = Thread(target=snake_virus, args=(snakefile,path,run))
		thread.start()
		flash('Your analysis is running!')
		return redirect(url_for('main.index', username=current_user.username))
	return render_template("viruspipe.html", user=user, form=form)

@bp.route('/user/<username>/MinMetaPipe/<run>', methods = ['GET', 'POST'])
@login_required
def minmetapipe(username, run):
	form = MinMetaConfigForm()
	user = User.query.filter_by(username=username).first_or_404()
	if form.validate_on_submit():
		query = Run.query.filter_by(id=run).first()
		run_dict = query.to_dict()
		path = os.path.join(current_app.config['UPLOAD_FOLDER'],run_dict['run_id'])

		#Generate Sample file
		with open(os.path.join(path, "samples.tsv"), 'w') as sample_file:
			print("sample\tbarcode", file=sample_file)
			for fieldname, value in form.data.items():
				if fieldname.startswith('barcode'):
					print(str(value)+'\t'+str(fieldname),file=sample_file)

		#Generate config file
		user_email = current_user.email
		with open(os.path.join(current_app.config['CONFIG_FOLDER'], "pipelines/minion_metabarcode/config.yaml"), 'r') as file :
			filedata = file.read()
		# Replace the target string
		filedata = filedata.replace('user_email', user_email)
		# Write the file out again
		with open(os.path.join(path, "config.yaml"), 'w') as file:
			file.write(filedata)

		#start pipeline
		snakefile = os.path.join(current_app.config['PIPELINE_FOLDER'], "minion_metabarcode/Snakefile")
		thread = Thread(target=snake_minmeta, args=(snakefile,path,run))
		thread.start()
		flash('Your analysis is running!')

		return redirect(url_for('main.index', username=current_user.username))

	return render_template("minmetapipe.html", user=user, form=form)

@bp.route('/user/<username>/IllMetaPipe/<run>', methods = ['GET', 'POST'])
@login_required
def illmetapipe(username, run):
	form = IllMetaConfigForm()
	user = User.query.filter_by(username=username).first_or_404()
	if form.validate_on_submit():
		#Get the Run
		query = Run.query.filter_by(id=run).first()
		run_dict = query.to_dict()
		path = os.path.join(current_app.config['UPLOAD_FOLDER'],run_dict['run_id'])

		#Generate Sample file
		samples = Sample.query.filter_by(run_id=query.id).all()
		with open(os.path.join(path, "samples.tsv"), 'w') as sample_file:
			print("sample", file=sample_file)
			for sample in samples:
				sample_dict = sample.to_dict()
				print(sample_dict['sample_id'], file=sample_file)

		#Generate config file
		config_dict = request.form.to_dict()
		config_dict.update(run_dict)
		config_dict["user_email"] = current_user.email
		config_dict["RUNPATH"] = path
		del config_dict['id']
		del config_dict['description']
		del config_dict['share']
		with open(os.path.join(path, "config.yaml"), 'w') as config_file:
			for line in fileinput.input(os.path.join(current_app.config['CONFIG_FOLDER'], "pipelines/illumina_metabarcode/config.yaml"), inplace=False):
				line = line.rstrip()
				if not line:
					continue
				for f_key, f_value in config_dict.items():
					if f_key in line:
						line = line.replace(f_key, str(f_value))
				print(line, file = config_file)
		snakefile = os.path.join(current_app.config['PIPELINE_FOLDER'], "illumina_metabarcode/Snakefile")
		thread = Thread(target=snake_illmeta, args=(snakefile,path,run))
		thread.start()
		flash('Your analysis is running!')
		return redirect(url_for('main.index', username=current_user.username))
	return render_template("illmetapipe.html", user=user, form=form)
