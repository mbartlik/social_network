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
		if " " in username:
			add_new_user = False
			flash('You cannot have spaces in your username')

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

	print(profile_pic)

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
		if " " in username:
			update_profile = False
			flash('You cannot have spaces in your username')

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

		if user_info[0][3] == 'https://storage.googleapis.com/social-network-images/generic_profile_pic.png':
			valid = upload_blob_from_file(f, profile_location)
			# if the image is invalid flash warning and redirect to new post page
			if not valid:
				flash("Something went wrong. Make sure your image is of a supported type like JPG or PNG.")
				return redirect(url_for('change_profile_pic', token=token))

			edit_user_info(user_id, name, bio, username, password, 'https://storage.googleapis.com/social-network-images/'+profile_location, num_posts, profile_count+1)
		else:
			valid = upload_blob_from_file(f, profile_location)
			# if the image is invalid flash warning and redirect to new post page
			if not valid:
				flash("Something went wrong. Make sure your image is of a supported type like JPG or PNG.")
				return redirect(url_for('change_profile_pic', token=token))

			edit_user_info(user_id, name, bio, username, password, 'https://storage.googleapis.com/social-network-images/'+profile_location, num_posts, profile_count+1)


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
	app.run()




# start cloud sql proxy on local - ./cloud_sql_proxy -instances=social-300422:us-east4:user-images=tcp:3306


