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


@bp.route('/')
@login_required
def index():
	return render_template('index.html')

@bp.route('/user/<username>')
@login_required
def user(username):
	user = User.query.filter_by(username=username).first_or_404()
	return render_template('user.html', samples=Sample.query.order_by(Sample.timestamp.desc()).all())


@bp.route('/user/<username>/CreateRun', methods=['GET', 'POST'])
@login_required
def run(username):
	form = CreateRun()
	if form.validate_on_submit():
		#Create run entry in db

		run = Run(run_id=form.run_id.data, share=form.share.data, run_type=form.run_type.data, seq_platform=form.platform.data, PE_SE=form.PE_SE.data, extension=form.extension.data, extension_R1_user=form.extension_R1_user.data, extension_R2_user=form.extension_R2_user.data, description=form.Description.data, author=current_user)

		db.session.add(run)
		db.session.commit()

		name_run = form.run_id.data

		return redirect(url_for('main.uploadrun', username=current_user.username, runname=name_run))
	return render_template("run.html", user=user, form=form)


@bp.route('/user/<username>/UploadRun/<runname>', methods=['GET', 'POST'])
@login_required
def uploadrun(username, runname):
	run = Run.query.filter_by(run_id=runname).first_or_404()
	if request.method == 'POST':

		path = os.path.join(current_app.config['UPLOAD_FOLDER'],run.run_id,'data')
		if not os.path.exists(path):
			os.makedirs(path)

		content = request.files['file'].read()
		filename = secure_filename(request.values['name'])

		with open(os.path.join(path,filename), 'ab+') as fp:
			fp.write(content)


		return redirect(url_for('main.browsemyruns', username=current_user.username))

	return render_template("uploadrun.html", user=user, runname=run.run_id)

@bp.route('/user/<username>/BrowseRuns', methods=['GET', 'POST'])
@login_required
def browseruns(username):
	user = User.query.filter_by(username=username).first_or_404()
	if request.method == 'POST':
		run_list = request.form.getlist('chkbox')
		run = run_list[0]
		analy_run = Run.query.filter_by(id=run).first()
		sample_ids = Sample.query.filter_by(run_id=analy_run.id).all()
		#path = os.path.join(current_app.config['UPLOAD_FOLDER'],form.run_id.data,'data')
		with open(os.path.join(current_app.config['CONFIG_FOLDER'], "samples.tsv"), 'w') as filehandle:
			filehandle.write("sample\n")
			for listitem in sample_ids:
				filehandle.write('%s\n' % listitem.sample_id)
				#print("This is the file " + listitem, file=sys.stderr)
		return redirect(url_for('main.pipeline', username=current_user.username, run=run))
	return render_template('browseruns.html')

@bp.route('/user/<username>/BrowseMyRuns', methods=['GET', 'POST'])
@login_required
def browsemyruns(username):
	user = User.query.filter_by(username=username).first_or_404()
	if request.method == 'POST':
		run_list = request.form.getlist('chkbox')
		run = run_list[0]
		analy_run = Run.query.filter_by(id=run).first()
		sample_ids = Sample.query.filter_by(run_id=analy_run.id).all()
		#path = os.path.join(current_app.config['UPLOAD_FOLDER'],form.run_id.data,'data')
		with open(os.path.join(current_app.config['CONFIG_FOLDER'], "samples.tsv"), 'w') as filehandle:
			filehandle.write("sample\n")
			for listitem in sample_ids:
				filehandle.write('%s\n' % listitem.sample_id)
				#print("This is the file " + listitem, file=sys.stderr)
		return redirect(url_for('main.pipeline', username=current_user.username, run=run))
	return render_template('browsemyruns.html')

@bp.route('/user/<username>/rundata')
@login_required
def rundata(username):
	idquery = User.query.filter_by(username=username).first()
	query = Run.query.filter_by(user_id=idquery.id)

	# search filter
	search = request.args.get('search[value]')
	if search:
		query = query.filter(db.or_(
			Run.description.like(f'%{search}%'),
			Run.run_id.like(f'%{search}%')
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
		if col_name not in ['run_id', 'timestamp']:
			col_name = 'run_id'
		descending = request.args.get(f'order[{i}][dir]') == 'desc'
		col = getattr(Run, col_name)
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
		'data': [run.to_dict() for run in query],
		'recordsFiltered': total_filtered,
		'recordsTotal': Run.query.count(),
		'draw': request.args.get('draw', type=int),
	}

@bp.route('/user/allrundata')
@login_required
def allrundata():
	query = Run.query.filter_by(share='Yes')

	# search filter
	search = request.args.get('search[value]')
	if search:
		query = query.filter(db.or_(
			Run.description.like(f'%{search}%'),
			Run.run_id.like(f'%{search}%')
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
		if col_name not in ['run_id', 'timestamp']:
			col_name = 'run_id'
		descending = request.args.get(f'order[{i}][dir]') == 'desc'
		col = getattr(Run, col_name)
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
		'data': [run.to_dict() for run in query],
		'recordsFiltered': total_filtered,
		'recordsTotal': Run.query.count(),
		'draw': request.args.get('draw', type=int),
	}

@bp.route('/user/<username>/RunSamples/<runname>')
@login_required
def runsamples(username,runname):
	run = Run.query.filter_by(run_id=runname).first_or_404()

	if run.concat == False:
		path = os.path.join(current_app.config['UPLOAD_FOLDER'],run.run_id,'data')

		files_filenames = [f for f in listdir(path) if isfile(join(path, f))]
		files_filenames_path = [os.path.join(path, s) for s in files_filenames]

		samples = list(set([sub.replace(run.extension_R1_user, "").replace(run.extension_R2_user, "")
		for sub in files_filenames]))
		print(samples, file=sys.stderr)

		#Concatenate multilane Illumina files
		if run.extension == 'Yes':
			keysList = merge_fastq(files_filenames_path)
			setattr(run, 'extension_R1_user', '_R1_001.fastq.gz')
			setattr(run, 'extension_R2_user', '_R2_001.fastq.gz')
			db.session.commit()
			files_filenames = [f for f in listdir(path) if isfile(join(path, f))]
			samples = list(set([sub.replace('_R1_001.fastq.gz', "").replace('_R2_001.fastq.gz', "")
			for sub in files_filenames]))
			print(samples, file=sys.stderr)
			for s in samples:
				R1 = os.path.join(path, s + '_R1_001.fastq.gz')
				R2 = os.path.join(path, s + '_R2_001.fastq.gz')
				samp = Sample(sample_id=s, R1_path=R1, R2_path=R2, run_name=run, host='arabidopsis')
				db.session.add(samp)
				db.session.commit()
		else:
			for s in samples:
				R1 = os.path.join(path, s + run.extension_R1_user)
				R2 = os.path.join(path, s + run.extension_R2_user)
				samp = Sample(sample_id=s, R1_path=R1, R2_path=R2, run_name=run, host='arabidopsis')
				db.session.add(samp)
				db.session.commit()

		setattr(run, 'concat', True)
		db.session.commit()

	user = User.query.filter_by(username=username).first_or_404()
	samples = Sample.query.filter_by(run_id=run.id).all()
	return render_template('runsamples.html', user=user, runname=runname, samples=samples)

@bp.route('/user/<username>/RunFiles/<runname>')
@login_required
def runfiles(username,runname):
	run = Run.query.filter_by(run_id=runname).first_or_404()

	path = os.path.join(current_app.config['UPLOAD_FOLDER'],run.run_id,'data')

	files_filenames = [f for f in listdir(path) if isfile(join(path, f))]
	files_filenames_path = [os.path.join(path, s) for s in files_filenames]
	user = User.query.filter_by(username=username).first_or_404()

	return render_template('runfiles.html', user=user, runname=runname, samples=files_filenames)

@bp.route('/user/<username>/RunAnalysis/<runname>', methods=['GET'])
@login_required
def runanalysis(username,runname):
	run = Run.query.filter_by(run_id=runname).first_or_404()
	book = pe.get_book(file_name=run.summary_output)
	return excel.make_response(book, 'handsontable.html')
	# run = Run.query.filter_by(run_id=runname).first_or_404()
	# samples = Sample.query.filter_by(run_id=run.id).all()
	# ids = [row.id for row in samples]
	# query = ReadSummary.query.filter(ReadSummary.sample_id.in_(ids)).all()
	# column_names = ['sample_name', 'raw_reads']
	# return excel.make_response_from_query_sets(query, column_names, 'handsontable.html')

@bp.route('/user/<username>/RunAnalysisDownload/<runname>', methods=['GET'])
@login_required
def runanalysisdown(username,runname):
	run = Run.query.filter_by(run_id=runname).first_or_404()
	analysis = run.summary_output
	analysis_file = analysis.split("/")[-1]
	analysis_path =  "/".join(analysis.split("/")[:-1])
	print(analysis_path)
	return send_from_directory(analysis_path, path=analysis_file, as_attachment=True)

@bp.route('/user/<username>/RunFileDownload/<runname>/<file>', methods=['GET'])
@login_required
def filedownload(username,runname, file):

	path = os.path.join(current_app.config['UPLOAD_FOLDER'],runname,'data')

	return send_from_directory(path, path=file, as_attachment=True)

@bp.route('/user/<username>/RunQC/<runname>', methods=['GET'])
@login_required
def runqc(username,runname):
	run = Run.query.filter_by(run_id=runname).first_or_404()
	qc = run.qc_output
	text_file = open(qc, "r")
	data = text_file.read()
	text_file.close()
	return data

@bp.route('/user/<username>/RunQCDownload/<runname>', methods=['GET'])
@login_required
def runqcdown(username,runname):
	run = Run.query.filter_by(run_id=runname).first_or_404()
	qc = run.qc_output
	qc_file = qc.split("/")[-1]
	qc_path =  "/".join(qc.split("/")[:-1])
	print(qc_path)
	return send_from_directory(qc_path, path=qc_file, as_attachment=True)


@bp.route('/user/<username>/RunDelete/<runname>', methods=['GET'])
@login_required
def rundelete(username,runname):
	run = Run.query.filter_by(run_id=runname).first_or_404()
	db.session.delete(run)
	db.session.commit()
	dir_path = os.path.join(current_app.config['UPLOAD_FOLDER'],runname)
	try:
		shutil.rmtree(dir_path)
	except OSError as e:
		print("Error: %s : %s" % (dir_path, e.strerror))
	return render_template('browsemyruns.html', user=user)

@bp.route('/user/<username>/UpdateSamples', methods=['POST'])
@login_required
def updatesample(username):
		pk = request.form['pk']
		name = request.form['name']
		value = request.form['value']
		sample = db.session.query(Sample).filter_by(id=pk).first()
		if name == 'host':
			setattr(sample, 'host', value)
		elif name == 'notes':
			setattr(sample, 'notes', value)
		db.session.commit()
		return json.dumps({'status':'OK'})

@bp.route('/user/<username>/Pipeline/<run>', methods = ['GET', 'POST'])
@login_required
def pipeline(username, run):
	form = PipelineForm()
	query = Run.query.filter_by(id=run).first()
	if form.validate_on_submit():
		if form.pipeline.data == 'virus_id':
			return redirect(url_for('main.runsamples', username=current_user.username, runname=query.run_id))
		if form.pipeline.data == 'min_meta':
			return redirect(url_for('pipelines.minmetapipe', username=current_user.username, run=run))
		if form.pipeline.data == 'illumina_meta':
			return redirect(url_for('pipelines.illmetapipe', username=current_user.username, run=run))
	return render_template("pipeline.html", user=user, form=form, run=run)
