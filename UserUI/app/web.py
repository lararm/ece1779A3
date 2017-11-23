###########################################################
# File:		web.py
# Authors:	Irfan Khan				 999207665
#		   	Larissa Ribeiro Madeira 1003209173
# Date:		October 2017
# Purpose: 	Webpage routes
###########################################################
from flask import render_template, session, request, escape, redirect, url_for,flash
from werkzeug.utils import secure_filename
from app import webapp
from app import db
from app import config
import datetime
import os
import boto3
import time
import random 
from random import randint

ALLOWED_IMAGE_EXTENSIONS = set(['image/png', 'image/jpg', 'image/jpeg', 'image/gif'])
@webapp.route('/')
def main():
	#session.clear()

	if 'username' in session:
		print ("Session user is: %s" % escape(session['username']))
		return redirect(url_for('homepage'))
	return render_template("login.html")

@webapp.route('/login', methods=['GET','POST'])
def login():
	if 'username' in session:
		print ("Session user is: %s" % escape(session['username']))
		return redirect(url_for('homepage'))
	return render_template("login.html")

@webapp.route('/signup', methods=['GET','POST'])
def signup():
	if 'username' in session:
		print ("Session user is: %s" % escape(session['username']))
		return redirect(url_for('homepage'))
	return render_template("signup.html")

@webapp.route('/homepage', methods=['GET','POST'])
def homepage():
	if 'username' not in session:
		return render_template("main.html")
	print ("Session user is: %s" % escape(session['username']))
	username = escape(session['username'])
	image_names = db.get_imagelist(username)

	return render_template("homepage.html",image_names=image_names,username=username)

@webapp.route('/transform_image', methods=['GET','POST'])
def transforms():
	
	# Get User Input
	if request.method == 'GET':
		return render_template("transforms.html")

	image_name = request.form['image_name']

	if 'username' not in session:
		return render_template("main.html")

	username = escape(session['username'])

	image_names = db.get_transforms(username,image_name)

	return render_template("transforms.html",image_names=image_names,username=username)


@webapp.route('/login_submit', methods=['POST'])
def login_submit():

	#Get User Input
	username = request.form['username']
	password = request.form['password']
	
	#Login
	if (db.login_user(username, password)):
		session['username'] = request.form['username']
		return redirect(url_for('homepage'))
	else:
		return redirect(url_for('login'))

@webapp.route('/signup_submit', methods=['POST'])
def signup_submit():
	
	#Get User Input
	username = request.form['username']
	password = request.form['password']

	#Add User
	if (db.add_user(username, password)):
		session['username'] = request.form['username']
		return redirect(url_for('homepage'))
	else:
		return redirect(url_for('signup'))

@webapp.route('/logout_submit', methods=['POST'])
def logout_submit():
	
	#Get Session Information
	username = escape(session['username'])

	#Close Session
	session.pop('username',None)
	return redirect(url_for('main'))


@webapp.route('/delete_user_submit', methods=['POST'])
def delete_user_submit():
	
	#Get Session Information
	username = escape(session['username'])

	#Get User Input
	password = request.form['password']

	#Delete the User
	if (db.delete_user(username,password)):
		#Close Session
		session.pop('username',None)
		return redirect(url_for('main'))
	return redirect(url_for('homepage'))

@webapp.route('/upload_image_submit', methods=['POST'])
def upload_image_submit():
	#Get Session Information
	username = escape(session['username'])

	# Get User Input
	image = request.files['image']
	image_name = image.filename
	image_type = image.content_type

	# If user does not select file, browser also
	# submit a empty part without filename
	if image_name == '':
		flash("No image selected for upload.")
		return redirect(url_for('homepage'))

	# Check image file extension
	if not valid_image_extension(image_type):
		flash ("%s is not a valid image type. Must be of type [png,gif,jpeg,jpg]." % (image_type))
		return redirect(url_for('homepage'))
	
	# Create an S3 client
	s3 = boto3.client('s3', aws_access_key_id=config.AWS_KEY, aws_secret_access_key=config.AWS_SECRET)
	id = config.AWS_ID
	
	# Creating unique name
	timestamp = str(int(time.time()))
	randomnum = str(random.randint(0,10000))
	unique_name = timestamp + "_" + randomnum + "_" + image_name
	
	# Upload image to S3
	image_new_name = username + "/" + unique_name
	s3.upload_fileobj( image,
			   id,
			   image_new_name,
			   ExtraArgs={"Metadata": {"Content-Type": image_type}})
	image_url = (s3.generate_presigned_url('get_object', Params={'Bucket': id, 'Key': image_new_name},
										   ExpiresIn=100)).split('?')[0]

	# Download image
	destpath = os.path.abspath('app/static/images')
	new_image_path = os.path.join(destpath, unique_name)
	s3.download_file(id, image_new_name, new_image_path)

	# Upload Image URL to DB
	db.add_image(username,unique_name, image_url)

	# Create Transforms
	db.transform_image(new_image_path, username)

	# Delete Images from Virtual Disk
	if (db.delete_image(username, unique_name)):
		print("%s was deleted!" % (unique_name))

	return redirect(url_for('homepage'))

@webapp.route('/delete_image_submit', methods=['POST'])
def delete_image_submit():
	
	#Get Session Information
	username = escape(session['username'])

	#Get User Input
	filename = request.form['filename']

	#Delete Images from Virtual Disk
	if (db.delete_image(username,filename)):
		print ("%s was deleted!" % (filename))

	return redirect(url_for('homepage'))

@webapp.route('/test/FileUpload', methods=['GET','POST'])
def file_upload():

	if (request.method == 'GET'):
		return render_template("taform.html")

	# Get User Input
	username = request.form['userID']
	userpass = request.form['password']

	# Verify Login Credentials
	if not (db.login_user(username, userpass)):
		return redirect(url_for('file_upload'))

	# Attempt to Upload Image
	if 'uploadedfile' not in request.files:
		flash("Image missing in upload request.")
		return redirect(url_for('file_upload'))

	# Get User Input
	image = request.files['uploadedfile']
	image_name = image.filename
	image_type = image.content_type
	 
	# If user does not select file, browser also
	# submit a empty part without filename
	if image_name == '':
		flash("No image selected for upload.")
		return redirect(url_for('file_upload'))
	
	# Check image file exension	                                                                                                   
	if not valid_image_extension(image_type):
		flash ("%s is not a valid image type. Must be of type [png,gif,jpeg,jpg]." % (image_type))
		return redirect(url_for('file_upload'))
                                                   
	# Create an S3 client
	s3 = boto3.client('s3',aws_access_key_id=config.AWS_KEY,aws_secret_access_key=config.AWS_SECRET)
	id = config.AWS_ID
	
	# Creating unique name
	timestamp = str(int(time.time()))
	randomnum = str(random.randint(0,10000))
	unique_name = timestamp + "_" + randomnum + "_" + image_name
	
	# Upload image to S3
	image_new_name = username + "/" + unique_name
	s3.upload_fileobj( image,
			   id,
			   image_new_name,
			   ExtraArgs = {"Metadata": {"Content-Type":image_type }})
	image_url = (s3.generate_presigned_url('get_object', Params={'Bucket': id, 'Key': image_new_name},ExpiresIn=100)).split('?')[0]

	# Upload Image URL to DB
	db.add_image(username,unique_name, image_url)

	# Download image
	destpath = os.path.abspath('app/static/images')
	new_image_path = os.path.join(destpath, unique_name)
	s3.download_file(id, image_new_name, new_image_path)

	#Create Transforms
	db.transform_image(new_image_path, username)

	# Delete Images from Virtual Disk
	if (db.delete_image(username, unique_name)):
		print("%s was deleted!" % (unique_name))
	
	return 'OK'

@webapp.route('/test/FileUploadSubmit', methods=['POST'])
def file_upload_submit():

	# Get User Input
	username = request.form['username']
	userpass = request.form['password']

	# Verify Login Credentials
	if not (db.login_user(username, userpass)):
		return redirect(url_for('file_upload'))

	# Attempt to Upload Image
	if 'image' not in request.files:
		flash("Image missing in upload request.")
		return redirect(url_for('file_upload'))

	# Get User Input
	image = request.files['image']
	image_name = image.filename
	image_type = image.content_type
	 
	# If user does not select file, browser also
	# submit a empty part without filename
	if image_name == '':
		flash("No image selected for upload.")
		return redirect(url_for('file_upload'))
	
	# Check image file exension	                                                                                                   
	if not valid_image_extension(image_type):
		flash ("%s is not a valid image type. Must be of type [png,gif,jpeg,jpg]." % (image_type))
		return redirect(url_for('file_upload'))
                                                   
	# Create an S3 client
	s3 = boto3.client('s3',aws_access_key_id=config.AWS_KEY,aws_secret_access_key=config.AWS_SECRET)
	id = config.AWS_ID
	                    
	# Creating unique name
	timestamp = str(int(time.time()))                            
	randomnum = str(random.randint(0,10000))
	unique_name = timestamp + "_" + randomnum + "_" + image_name
	
	# Upload image to S3
	image_new_name = username + "/" + unique_name
	s3.upload_fileobj( image,
			   id,
			   image_new_name,
			   ExtraArgs = {"Metadata": {"Content-Type":image_type }})
	image_url = (s3.generate_presigned_url('get_object', Params={'Bucket': id, 'Key': image_new_name},ExpiresIn=100)).split('?')[0]

	# Upload Image URL to DB
	db.add_image(username,unique_name, image_url)

	# Download image
	destpath = os.path.abspath('app/static/images')
	new_image_path = os.path.join(destpath, unique_name)
	s3.download_file(id, image_new_name, new_image_path)

	#Create Transforms
	db.transform_image(new_image_path, username)

	# Delete Images from Virtual Disk
	if (db.delete_image(username, unique_name)):
		print("%s was deleted!" % (unique_name))

def valid_image_extension(ext):

	for extension in ALLOWED_IMAGE_EXTENSIONS:
		if (ext == extension):
			return True
	
	return False
