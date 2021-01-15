from flask import Flask, render_template, request, flash, url_for, redirect
from flask_cors import CORS
from PIL import Image
from io import BytesIO
from models import *

app = Flask(__name__) # creates server object
app.config['SECRET_KEY'] = 'GEBVNJKSDLEJQ'


# Homepage route redirects to login page
@app.route('/')
def index():
	return redirect(url_for('login'))

# Route to display a user's feed
# Loads all posts of people that the current user is following
# The default token of -1 will allow a user to look at public posts without logging in
@app.route('/feed/<token>', methods=['GET','POST'])
def feed(token="-1"):
	# if the token is default -1 then the user is not logged in
	if token == "-1":
		return redirect(url_for('login'))

	# check if the user is still authenticated
	user_id = authenticate_token(token)
	if user_id == -1:
		flash('Login expired due to inactivity')
		return redirect(url_for('login'))

	# get the posts of all the users that this user follows
	posts = get_posts_following(user_id)

	if len(posts) == 0:
		flash('Follow other users to see posts in your feed!')

	return render_template('feed.html', token=token, logged_in=True, posts=posts)



# Route to allow user input of login credentials
@app.route('/login', methods=['GET','POST'])
def login():
	# if the method is post then the user clicked submit, must check info
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		user_id = check_login_info(username, password)
		if user_id == -1:
			flash('Invalid Username or Password!')
		else:
			token = get_token(user_id)
			return redirect(url_for('feed',token=token))
	return render_template('login.html', logged_in=False, token=-1)


# Route for auser to create a new account
@app.route('/create-account', methods=['GET','POST'])
def create_account():

	name = "" # these filler values will be loaded in if the page is loaded for the first time
	username = ""
	bio = ""

	# if the method is post then the user entered account data
	# must check for valid inputs then add them to the database
	if request.method=='POST':
		name = request.form['name']
		username = request.form['username']
		bio = request.form['bio']
		password = request.form['password']
		confirm_password = request.form['confirm_password']

		# error checking for create account input forms
		# check for any empty field
		add_new_user = True # set this to False if any invalid field
		if name == "":
			add_new_user = False
			flash('Make sure to give yourself a name!')
		if username == "":
			add_new_user = False
			flash('Make sure to give yourself a username!')
		if bio == "":
			add_new_user = False
			flash('Make sure to give yourself a bio!')
		if len(password) < 4:
			add_new_user = False
			flash('Your password must be at least 4 characters')

		# check for matching passwords
		if password != confirm_password:
			add_new_user = False
			flash('Check again to make sure that your passwords match')

		# check for existing username
		if check_existing_username(username):
			add_new_user = False
			flash('That username already exists, pick another one')

		if add_new_user:
			user_id = add_user(name, bio, username, password)
			token = get_token(user_id)
			return redirect(url_for('feed', token=token))


	return render_template('create_account.html', logged_in=False, token=-1, name=name, username=username, bio=bio)


# Route for a user to view their profile
@app.route('/my-profile/<token>')
def my_profile(token):
	# check if the user is still authenticated
	user_id = authenticate_token(token)
	if user_id == -1:
		flash('Login expired due to inactivity')
		return redirect(url_for('login'))

	user_info = get_user_info(user_id)
	name = user_info[0][1]
	bio = user_info[0][2]
	profile_pic = user_info[0][3]
	username = user_info[0][4]

	posts = get_posts(user_id)

	return render_template('my_profile.html', token=token, user_id=user_id, name=name, bio=bio, profile_pic=profile_pic, username=username, logged_in=True, posts=posts)


# Route for user to edit their profile
@app.route('/edit-profile/<token>', methods=['GET', 'POST'])
def edit_profile(token):
	# check if the user is still authenticated
	user_id = authenticate_token(token)
	if user_id == -1:
		flash('Login expired due to inactivity')
		return redirect(url_for('login'))

	user_info = get_user_info(user_id)
	name = user_info[0][1]
	bio = user_info[0][2]
	profile_pic = user_info[0][3]
	username = user_info[0][4]
	password = user_info[0][5]
	num_posts = user_info[0][6]
	profile_count = user_info[0][7]

	original_username = username # will be used for checking if the new username exists already or not

	if request.method == 'POST':
		name = request.form['name']
		bio = request.form['bio']
		username = request.form['username']

		# error checking for create account input forms
		# check for any empty field
		update_profile = True # set this to False if any invalid field
		if name == "":
			update_profile = False
			flash('Make sure to give yourself a name!')
		if username == "":
			update_profile = False
			flash('Make sure to give yourself a username!')
		if bio == "":
			update_profile = False
			flash('Make sure to give yourself a bio!')

		# check for existing username
		if check_existing_username(username) and username != original_username:
			update_profile = False
			flash('That username already exists, pick another one')

		if update_profile:
			edit_user_info(user_id, name, bio, username, password, profile_pic, num_posts, profile_count)
			return redirect(url_for('my_profile', token=token))

	return render_template('edit_profile.html', token=token, name=name, bio=bio, username=username, logged_in=True)


# Route to change a profile picture
@app.route('/change-profile-pic/<token>')
def change_profile_pic(token):
	# check if the user is still authenticated
	user_id = authenticate_token(token)
	if user_id == -1:
		flash('Login expired due to inactivity')
		return redirect(url_for('login'))

	return render_template('change_profile_pic.html', token=token, logged_in=True)


# Route to execute the actual profile pic change
@app.route('/execute-change-profile-pic/<token>', methods=['POST'])
def execute_change_profile_pic(token):
	# check if the user is still authenticated
	user_id = authenticate_token(token)
	if user_id == -1:
		flash('Login expired due to inactivity')
		return redirect(url_for('login'))

	user_info = get_user_info(user_id)
	name = user_info[0][1]
	bio = user_info[0][2]
	profile_pic = user_info[0][3]
	username = user_info[0][4]
	password = user_info[0][5]
	num_posts = user_info[0][6]
	profile_count = user_info[0][7]

	if request.method == 'POST':
		f = request.files['file']
		f.seek(0)

		# url location of the profile pic in google cloud storage bucket
		profile_location = 'profile_pic-' + str(user_id) + '-' + str(profile_count)

		if user_info[0][3] == 'https://storage.googleapis.com/social_net_images/generic_profile_pic.png':
			valid = upload_blob(f, profile_location)
			# if the image is invalid flash warning and redirect to new post page
			if not valid:
				flash("Something went wrong. Make sure your image is of a supported type like JPG or PNG.")
				return redirect(url_for('change_profile_pic', token=token))

			edit_user_info(user_id, name, bio, username, password, 'https://storage.googleapis.com/social_net_images/'+profile_location, num_posts, profile_count+1)
		else:
			valid = upload_blob(f, profile_location)
			# if the image is invalid flash warning and redirect to new post page
			if not valid:
				flash("Something went wrong. Make sure your image is of a supported type like JPG or PNG.")
				return redirect(url_for('change_profile_pic', token=token))

			edit_user_info(user_id, name, bio, username, password, 'https://storage.googleapis.com/social_net_images/'+profile_location, num_posts, profile_count+1)


	return redirect(url_for('my_profile', token=token))


# Route to bring a logged in user to a page where they can logout
@app.route('/logout')
def logout():
	return redirect(url_for('login'))


# Route to allow a user to create a new post
@app.route('/new-post/<token>')
def new_post(token):
	# check if the user is still authenticated
	user_id = authenticate_token(token)
	if user_id == -1:
		flash('Login expired due to inactivity')
		return redirect(url_for('login'))

	return render_template('new_post.html', token=token, logged_in=True)


# Route to create a new post based on the form data from the new post page
@app.route('/new-post-execute/<token>', methods=['POST'])
def new_post_execute(token):
	# check if the user is still authenticated
	user_id = authenticate_token(token)
	if user_id == -1:
		flash('Login expired due to inactivity')
		return redirect(url_for('login'))

	# get form data
	f = request.files['file']
	f.seek(0)
	caption = request.form['caption']

	valid = add_post(user_id, f, caption)

	# if the image is invalid flash warning and redirect to new post page
	if not valid:
		flash("Something went wrong. Make sure your image is of a supported file type like JPG or PNG.")
		return redirect(url_for('new_post', token=token))

	return redirect(url_for('my_profile', token=token))

# Route for a user to find other users
# Lists and links to all users in the database
@app.route('/find_users/<token>')
def find_users(token):
	# if the token is default -1 then the user is not logged in
	if token == "-1":
		logged_in = False
		user_id = -1
	else:
		# check if the user is still authenticated
		user_id = authenticate_token(token)
		if user_id == -1:
			flash('Login expired due to inactivity')
			return redirect(url_for('login'))
		logged_in = True

	users = get_users()

	return render_template('find_users.html', token=token, logged_in=logged_in, users=users, user_id=user_id)


# Route to display the profile information of a certain user given user id
@app.route('/profile/<profile_id>/<token>')
def profile(profile_id, token):
	# if the token is default -1 then the user is not logged in
	if token == "-1":
		logged_in = False
	else:
		# check if the user is still authenticated
		user_id = authenticate_token(token)
		if user_id == -1:
			flash('Login expired due to inactivity')
			return redirect(url_for('login'))
		logged_in = True

	# if the user id and the profile id are the same then it is this user
	# redirect to my_profile
	if logged_in:
		if user_id == int(profile_id):
			return redirect(url_for('my_profile', token=token))

	# get the data about the profile in question
	profile_info = get_user_info(profile_id)
	name = profile_info[0][1]
	bio = profile_info[0][2]
	profile_pic = profile_info[0][3]
	username = profile_info[0][4]

	posts = get_posts(profile_id) # posts for this profile

	following = False
	if logged_in: # if not logged in then following defaults to false, follow will link to login page
		all_followed_users = get_following(user_id)
		print(all_followed_users)
		print(profile_id)
		if int(profile_id) in all_followed_users:
			following = True

	return render_template('profile.html', token=token, logged_in=logged_in, profile_id=profile_id, name=name, bio=bio, profile_pic=profile_pic, username=username, posts=posts, following=following)

# Route that is executed when one user clicks the button to follow or unfollow another
@app.route('/follow-operation/<token>')
def follow_operation(token):
	# if the token is default -1 then the user is not logged in
	if token == "-1":
		logged_in = False
	else:
		# check if the user is still authenticated
		user_id = authenticate_token(token)
		if user_id == -1:
			flash('Login expired due to inactivity')
			return redirect(url_for('login'))
		logged_in = True

	# get profile data to pass back into the profile template
	profile_id = request.args.get('profile_id')
	name = request.args.get('name')
	bio = request.args.get('bio')
	profile_pic = request.args.get('profile_pic')
	username = request.args.get('username')
	following = request.args.get('following')

	# get boolean value of following string
	following = get_bool(following)				# ???????? MAYbe i changed something bad

	following = follow(user_id, profile_id)

	posts = get_posts(profile_id)

	return render_template('profile.html', token=token, logged_in=logged_in, profile_id=profile_id, name=name, bio=bio, profile_pic=profile_pic, username=username, posts=posts, following=following)


# Route that shows a user's followers
# Exectues when clicking links to a user's followers from their profile page
@app.route('/<profile_id>/followers/<token>')
def followers(profile_id, token):
	# if the token is default -1 then the user is not logged in
	if token == "-1":
		logged_in = False
	else:
		# check if the user is still authenticated
		user_id = authenticate_token(token)
		if user_id == -1:
			flash('Login expired due to inactivity')
			return redirect(url_for('login'))
		logged_in = True

	# get follower ids then get all info about each id
	followers_ids = get_followers(profile_id)
	followers = []
	for id in followers_ids:
		followers.append(get_user_info(id))

	# render template with the followers passed in and the boolean followers set true, meaning this is a followers list
	return render_template('followers_or_following.html', users=followers, followers=True, token=token, logged_in=logged_in)

# Route to show the user's that a given user follows
@app.route('/<profile_id>/following/<token>')
def following(profile_id, token):
	# if the token is default -1 then the user is not logged in
	if token == "-1":
		logged_in = False
	else:
		# check if the user is still authenticated
		user_id = authenticate_token(token)
		if user_id == -1:
			flash('Login expired due to inactivity')
			return redirect(url_for('login'))
		logged_in = True

	following_ids = get_following(profile_id) # get following of this user
	
	# iterate through ever id that this user follows and get data about that user
	following = []
	for id in following_ids:
		following.append(get_user_info(id))

	# render template with the following passed in and the boolean followers set false, meaning this is a list of users followed
	return render_template('followers_or_following.html', users=following, followers=False, token=token, logged_in=logged_in)

# Endpoint to delete a post
# takes 
@app.route('/delete-post/<post_id>/<token>')
def delete_post(post_id, token):
	delete_post_operation(post_id)

	return redirect(url_for('my_profile', token=token))

# Endpoint to redirect to a page that is solely to explain the basics of this project
@app.route('/about/<token>')
def about(token):
	# if the token is default -1 then the user is not logged in
	if token == "-1":
		logged_in = False
	else:
		# check if the user is still authenticated
		user_id = authenticate_token(token)
		if user_id == -1:
			flash('Login expired due to inactivity')
			return redirect(url_for('login'))
		logged_in = True

	return render_template('about.html', token=token, logged_in=logged_in)




if __name__ == '__main__':
	app.run(debug=True)




# start cloud sql proxy on local - ./cloud_sql_proxy -instances=social-300422:us-east4:user-images=tcp:3306

# TODO
# Add error handling for all inputs
# Make it so you can't use a username that is taken or change to a username that is taken
# add a post preview before actually posting
# comment code better - add headers on top of documents and do better with commenting each endpoint - explain parameters
# do the README
# Make something so it only loads a certain number of posts at once rather than all at once




































from google.cloud import storage
import os
from os import path
import pymysql
import jwt
import datetime
from PIL import Image


ROOT = path.dirname(path.relpath(__file__)) # gets the location on computer of this directory

# info about signing into the google cloud sql database
db_user = 'root'
db_password = '1234'
db_name = 'master'
db_connection_name = 'social-300422:us-east4:user-images'

jwt_key = "ITENGPRFWCRE" # used for encoding and decoding json web token for authentication


# Given a username and password this function generates a json web token
# The token will be used for authentication throughout the application
def get_token(user_id):
	# get current time and add 6 hours to represent the time when the user's login expires
	current_time = datetime.datetime.now()
	time_to_expiration = datetime.timedelta(hours = 8)
	expiration_time = current_time + time_to_expiration
	expiration_string = expiration_time.strftime("%m/%d/%Y, %H:%M:%S") # convert to string to use in payload

	# generate payload which will go 
	payload = {
		"user_id": user_id,
		"expiration_time": expiration_string
	}

	encoded = jwt.encode(payload, jwt_key, algorithm="HS256") # get jwt

	return encoded

# Given a token this method authenticates the user
def authenticate_token(token):
	decoded = jwt.decode(token, jwt_key, algorithms="HS256") # decode using the same key and algorithm to encode

	expiration = datetime.datetime.strptime(decoded["expiration_time"], '%m/%d/%Y, %H:%M:%S') # convert expiration to datetime

	# compare expiration to current time, if it is too late then logout
	if expiration < datetime.datetime.now():
		return -1

	return decoded["user_id"]

# Establishes connection with Google Cloud SQL database
def get_connection():
	# when deployed to app engine the 'GAE_ENV' variable will be set to 'standard'
	if os.environ.get('GAE_ENV') == 'standard':
		# use the local socket interface for accessing Cloud SQL
		unix_socket = '/cloudsql/{}'.format(db_connection_name)
		conn = pymysql.connect(user=db_user, password=db_password, unix_socket=unix_socket, db=db_name)
	else:
		# if running locally use the TCP connections instead
		# set up Cloud SQL proxy (cloud.google.com/sql/docs/mysql/sql-proxy)
		host = '127.0.0.1'
		conn = pymysql.connect(user=db_user, password=db_password, host=host, db=db_name)

	return conn


def check_login_info(username, password):
	conn = get_connection()
	cur = conn.cursor()

	# select the user that has the username and password
	cur.execute('SELECT * FROM users WHERE username=%s AND password=%s', (username, password))
	user_info = cur.fetchall()
	# if there was not a matching username or password then return -1 as failure
	if len(user_info) == 0:
		return -1

	return user_info[0][0] # return user id

# Function to add a user to the database
def add_user(name, bio, username, password):

	# TODO-add check for existing username

	profile_pic = 'https://storage.googleapis.com/social_net_images/generic_profile_pic.png'

	conn = get_connection()
	cur = conn.cursor()
	cur.execute('INSERT INTO users (name, bio, profile_pic, username, password, num_posts, profile_count, following) values(%s,%s,%s,%s,%s,%s,%s,%s)', (name, bio, profile_pic, username, password, 0, 1, "[]"))
	conn.commit()

	cur.execute('SELECT user_id FROM users WHERE username=%s', (username,))
	user_id = cur.fetchone()

	conn.close()

	return user_id[0]


# Function to get a user's information from Cloud SQL
def get_user_info(user_id):
	conn = get_connection()
	cur = conn.cursor()
	cur.execute('SELECT * FROM users WHERE user_id=%s', (user_id,))

	user_info = cur.fetchall() # sample - ((1, 'Max Bartlik', 'test bio', 'https://storage.googleapis.com/social_network_images/generic_profile_pic', 'mbartlik', 'window', 0),)
	conn.close()

	return user_info


# Function to edit user info
def edit_user_info(user_id, name, bio, username, password, profile_pic, num_posts, profile_count):
	conn = get_connection()
	cur = conn.cursor()
	cur.execute('UPDATE users SET name=%s, bio=%s, username=%s, password=%s, profile_pic=%s, num_posts=%s, profile_count=%s WHERE user_id=%s', (name, bio, username, password, profile_pic, num_posts, profile_count, user_id))
	conn.commit()

	conn.close()
	


# function to upload an image to google cloud storage
def upload_blob(file, destination_blob_name):
	# open file with PIL Image to see if the file is of a proper type
	try:
		image = Image.open(file)
	except:
		return False # return false to signify the image is invalid

	file.seek(0)

	# boilerplate google cloud storage upload
	storage_client = storage.Client()
	bucket = storage_client.bucket('social_net_images')
	blob = bucket.blob(destination_blob_name)

	blob.upload_from_file(file)

	return True

# Function to delete a blob from google cloud storage
def delete_blob(blob_name):
	storage_client = storage.Client()

	bucket = storage_client.bucket('social_net_images')
	blob = bucket.blob(blob_name)
	blob.delete()

# Function to see if the user is logged in based on the stored user id
# Returns boolean
def check_logged_in(user_id):
	if not user_id:
		return False
	if int(user_id) > 0:
		return True
	return False

# Function to add a post to the database
# Requires a user id, a file object, and a caption
def add_post(user_id, file, caption):
	conn = get_connection()
	cur = conn.cursor()

	# get the number of posts by this user
	cur.execute('SELECT num_posts FROM users WHERE user_id=%s', (user_id,))
	num_posts = cur.fetchone()[0]
	
	# increment this user's post count
	cur.execute('UPDATE users SET num_posts=%s WHERE user_id=%s', (num_posts+1, user_id)) 

	# this is the url of where the image will be stored in the google cloud storage bucket
	post_image_identifier = 'user-' + str(user_id) + '-post-' + str(num_posts)
	post_image_url = 'https://storage.googleapis.com/social_net_images/' + post_image_identifier
	
	# upload image
	valid = upload_blob(file, post_image_identifier)

	# if the image was invalid then pass the false back through to main
	if not valid:
		return False

	# make strings that will later be populated to store comment and like data
	comments = "$&%*"
	likes_list = ""

	# get username of this user
	username = get_user_info(int(user_id))[0][4]

	# add post info to the cloud sql database
	cur.execute('INSERT INTO posts (image_link, caption, comments, likes_list, user_id, username) values(%s,%s,%s,%s,%s,%s)', (post_image_url, caption, comments, likes_list, user_id, username))

	conn.commit()
	conn.close()

	return True

# Function to return all of the posts of a given user
def get_posts(user_id):
	conn = get_connection()
	cur = conn.cursor()

	cur.execute('SELECT * FROM posts WHERE user_id=%s ORDER BY post_date DESC', (user_id,))
	posts = cur.fetchall()

	conn.close()
	
	return posts

# Function to return data about all users
# Returns tuple where each entry is a tuple that is a user id and username
def get_users():
	conn = get_connection()
	cur = conn.cursor()

	cur.execute('SELECT user_id, username FROM users')

	users = cur.fetchall()

	return users

# Function to get a list of user ids that the given user follows
# Returns list
def get_following(user_id):
	conn = get_connection()
	cur = conn.cursor()

	cur.execute('SELECT following FROM users WHERE user_id=%s', (user_id,))
	following_data = cur.fetchone()

	following_data = following_data[0] # get first element of tuple fetched

	# parse through the string data and make a list out of it
	this_user = ''
	following = []
	for char in following_data:
		if char == ',' or char == '[' or char == ']':
			if this_user != '':
				following.append(int(this_user))
				this_user = ''
			continue
		this_user += char

	conn.close()

	return following

# Function to get a list of user ids that follow a given user id
def get_followers(profile_id):
	profile_id = int(profile_id) # convert to int for comparisons later

	conn = get_connection()
	cur = conn.cursor()

	# get all user ids from database
	cur.execute('SELECT user_id FROM users')
	user_ids = cur.fetchall()

	# iterate through all user ids and see if this user is followed by that user
	# if so then add the id to followers
	followers = []
	for id in user_ids:
		if profile_id in get_following(id[0]):
			followers.append(id[0])

	print(followers)
	conn.close()

	return followers

# Helper function to get the boolean variable of a "True" or "False" string
# Used for parsing request arguments
def get_bool(arg):
	if arg == 'True':
		return True
	return False

# Function to send to users database an update to say that the current user follows or unfollows another user
# user_id is the logged in user, profile_id is the account that is to be followed or unfollowed 
# returns a boolean following, represents if after the operation there is or isn't a follow relationship
def follow(user_id, profile_id):
	# get list of ids the user is following
	following_list = get_following(user_id)

	# convert user_id and profile_id to ints
	user_id = int(user_id)
	profile_id = int(profile_id)

	print(following_list)
	print(profile_id)

	if profile_id in following_list: # already following, unfollow
		following_list.remove(profile_id)
		following = False # resulting follow relationship to be returned
	else: # must follow
		following_list.append(profile_id)
		following = True

	conn = get_connection()
	cur = conn.cursor()

	# update database
	cur.execute('UPDATE users SET following=%s WHERE user_id=%s', (str(following_list), user_id))
	conn.commit()
	conn.close()

	return following

# Function to get the posts of all the profiles that a given user follows
def get_posts_following(user_id):
	conn = get_connection()
	cur = conn.cursor()

	following = get_following(int(user_id))

	# make a string to query the posts database where user_id is one of the ids in following
	# in the format of ---- 1 or 2 or 5 or 8 or 10
	query_string = ''
	for id in following:
		query_string += 'user_id='
		query_string += str(id)
		query_string += ' OR '
	query_string += 'user_id=' + str(user_id)

	# format query string for a mysql query and fetch the posts
	query_string = 'SELECT * FROM posts WHERE {} ORDER BY post_date DESC'.format(query_string)

	cur.execute(query_string)
	posts = cur.fetchall()
	conn.close()

	return posts

# Function to delete a post given a post id
def delete_post_operation(post_id):
	conn = get_connection()
	cur = conn.cursor()

	cur.execute('DELETE FROM posts WHERE post_id=%s', (int(post_id),))

	conn.commit()
	conn.close()

# Function to check if a username is already in the database
def check_existing_username(username):
	conn = get_connection()
	cur = conn.cursor()

	# get all usernames from the dataabse
	cur.execute('SELECT username FROM users')
	existing_usernames = cur.fetchall()
	print(existing_usernames)

	for entry in existing_usernames: # each entry will be a tuple with one element which is the username
		if entry[0] == username:
			return True

	return False




