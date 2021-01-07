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



