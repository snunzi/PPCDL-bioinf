import os
from os import listdir
from os.path import exists, isfile, join
from flask import render_template, flash, redirect, url_for, request, send_from_directory, current_app, json, render_template_string
from flask_login import current_user, login_required
from app import db
from app.models import User, Sample, Run, ReadSummary, PathoscopeSummary, BlastnFull
from app.main import bp
from app.main.helper import merge_fastq
from app.main.forms import AssemblyForm, CreateRun, PipelineForm, ExploreForm
from werkzeug.utils import secure_filename
import pathlib
import fileinput
import sys
from threading import Thread
import flask_excel as excel
import pyexcel as pe
import shutil
from shutil import copyfile



@bp.route('/user/<username>/Explore', methods=['GET', 'POST'])
@login_required
def explore(username):
	form = ExploreForm()
	if form.validate_on_submit():
		if form.pipeline.data == 'virus_id':
			if form.virus_results.data == 'pathoscope':
				return redirect(url_for('main.browsevirusresults', username=current_user.username, host=form.host.data))
			elif form.virus_results.data == 'blastn':
				return redirect(url_for('main.browseblastnresults', username=current_user.username, host=form.host.data))
	return render_template("explore2.html", user=user, form=form)

@bp.route('/user/<username>/BrowseVirusResults/<host>', methods=['GET', 'POST'])
@login_required
def browsevirusresults(username, host):
	return render_template('browsevirusresults.html', host=host)

@bp.route('/user/<username>/BrowseBlastnResults/<host>', methods=['GET', 'POST'])
@login_required
def browseblastnresults(username, host):
	return render_template('browseblastnresults.html', host=host)

@bp.route('/user/<username>/virusdata/<host>')
@login_required
def virusdata(username, host):
	if host == 'all':
		query = db.session.query(Sample, PathoscopeSummary).join(Sample).filter_by()
	else:
		query = db.session.query(Sample, PathoscopeSummary).join(Sample).filter_by(host=host)
		#query = PathoscopeSummary.query.filter(PathoscopeSummary.sample.has(host=host))

	# search filter
	search = request.args.get('search[value]')
	if search:
		query = query.filter(db.or_(
			PathoscopeSummary.virus.like(f'%{search}%'),
			PathoscopeSummary.classification.like(f'%{search}%')
	))
	total_filtered = query.count()

	# sorting
	order = []
	i = 0
	while True:
		col_index = request.args.get(f'order[{i}][column]')
		if col_index is None:
			break
		col_name = request.args.get(f'columns[{col_index}][data]')
		if col_name not in ['sample_name', 'coverage']:
			col_name = 'sample_name'
		descending = request.args.get(f'order[{i}][dir]') == 'desc'
		col = getattr(PathoscopeSummary, col_name)
		if descending:
			col = col.desc()
		order.append(col)
		i += 1
	if order:
		query = query.order_by(*order)

	# pagination
	start = request.args.get('start', type=int)
	length = request.args.get('length', type=int)
	query = query.offset(start).limit(length)

	# response
	return {
		'data': [{**pathoscopesummary.to_dict(), **{"run_name":sample.run_name.to_dict()['run_id']}}  for sample, pathoscopesummary in query],
		#'data': [pathoscopesummary.to_dict() for sample, pathoscopesummary in query],
		#'rundata' : [sample.run_name.to_dict() for sample, pathoscopesummary in query],
		'recordsFiltered': total_filtered,
		'recordsTotal': PathoscopeSummary.query.count(),
		'draw': request.args.get('draw', type=int),
	}

@bp.route('/user/<username>/blastndata/<host>')
@login_required
def blastndata(username, host):
	if host == 'all':
		query = db.session.query(Sample, BlastnFull).join(Sample).filter_by()
	else:
		query = db.session.query(Sample, BlastnFull).join(Sample).filter_by(host=host)
		#query = PathoscopeSummary.query.filter(PathoscopeSummary.sample.has(host=host))

	# search filter
	search = request.args.get('search[value]')
	if search:
		query = query.filter(db.or_(
			BlastnFull.virus.like(f'%{search}%'),
			BlastnFull.classification.like(f'%{search}%')
	))
	total_filtered = query.count()

	# sorting
	order = []
	i = 0
	while True:
		col_index = request.args.get(f'order[{i}][column]')
		if col_index is None:
			break
		col_name = request.args.get(f'columns[{col_index}][data]')
		if col_name not in ['sample_name', 'run_name']:
			col_name = 'sample_name'
		descending = request.args.get(f'order[{i}][dir]') == 'desc'
		col = getattr(BlastnFull, col_name)
		if descending:
			col = col.desc()
		order.append(col)
		i += 1
	if order:
		query = query.order_by(*order)

	# pagination
	start = request.args.get('start', type=int)
	length = request.args.get('length', type=int)
	query = query.offset(start).limit(length)

	# response
	return {
		'data': [{**blastnfull.to_dict(), **{"run_name":sample.run_name.to_dict()['run_id']}}  for sample, blastnfull in query],
		#'data': [pathoscopesummary.to_dict() for sample, pathoscopesummary in query],
		#'rundata' : [sample.run_name.to_dict() for sample, pathoscopesummary in query],
		'recordsFiltered': total_filtered,
		'recordsTotal': BlastnFull.query.count(),
		'draw': request.args.get('draw', type=int),
	}
