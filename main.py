from flask import Flask, render_template, request, flash, url_for, redirect
from flask_cors import CORS
from PIL import Image
from io import BytesIO
from models import *

app = Flask(__name__) # creates server object
app.config['SECRET_KEY'] = 'GEBVNJKSDLEJQ'

# Route to display a user's feed
# Loads all posts of people that the current user is following
# The default user_id of -1 will allow a user to look at public posts without logging in
@app.route('/', methods=['GET','POST'])
def feed():
	user_id = request.args.get('user_id')
	if user_id == "":
		user_id = -1

	logged_in = check_logged_in(user_id)

	# redirect to login page if the user is not logged in
	if not logged_in:
		return redirect(url_for('login'))

	# get the posts of all the users that this user follows
	posts = get_posts_following(user_id)

	return render_template('feed.html',user_id=user_id, logged_in=logged_in, posts=posts)



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
			return redirect(url_for('feed',user_id=user_id))
	return render_template('login.html', logged_in=False)


# Route for auser to create a new account
@app.route('/create-account', methods=['GET','POST'])
def create_account():

	# if the method is post then the user entered account data
	# must check for valid inputs then add them to the database
	if request.method=='POST':
		name = request.form['name']
		username = request.form['username']
		bio = request.form['bio']
		password = request.form['password']
		confirm_password = request.form['confirm_password']

		# TODO: ERROR CHECKING HERE

		user_id = add_user(name, bio, username, password)

		return redirect(url_for('feed', user_id=user_id))

	return render_template('create_account.html', logged_in=False)


# Route for a user to view their profile
@app.route('/my-profile')
def my_profile():

	user_id = request.args.get('user_id')

	user_info = get_user_info(user_id)
	name = user_info[0][1]
	bio = user_info[0][2]
	profile_pic = user_info[0][3]
	username = user_info[0][4]

	posts = get_posts(user_id)
	print(posts)

	return render_template('my_profile.html', user_id=user_id, name=name, bio=bio, profile_pic=profile_pic, username=username, logged_in=True, posts=posts)


# Route for user to edit their profile
@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
	user_id = request.args.get('user_id')

	user_info = get_user_info(user_id)
	name = user_info[0][1]
	bio = user_info[0][2]
	profile_pic = user_info[0][3]
	username = user_info[0][4]
	password = user_info[0][5]
	num_posts = user_info[0][6]
	profile_count = user_info[0][7]

	if request.method == 'POST':
		name = request.form['name']
		bio = request.form['bio']
		username = request.form['username']
		edit_user_info(user_id, name, bio, username, password, profile_pic, num_posts, profile_count)
		return redirect(url_for('my_profile', user_id=user_id))

	return render_template('edit_profile.html', user_id=user_id, name=name, bio=bio, username=username, logged_in=True)


# Route to change a profile picture
@app.route('/change-profile-pic')
def change_profile_pic():
	user_id = request.args.get('user_id')
	return render_template('change_profile_pic.html', user_id=user_id, logged_in=True)


# Route to execute the actual profile pic change
@app.route('/execute-change-profile-pic', methods=['POST'])
def execute_change_profile_pic():
	user_id = request.args.get('user_id')

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
			upload_blob(f, profile_location)
			edit_user_info(user_id, name, bio, username, password, 'https://storage.googleapis.com/social_net_images/'+profile_location, num_posts, profile_count+1)
		else:
			upload_blob(f, profile_location)
			edit_user_info(user_id, name, bio, username, password, 'https://storage.googleapis.com/social_net_images/'+profile_location, num_posts, profile_count+1)
			print("executed 2")


	return render_template('my_profile.html', user_id=user_id, name=name, bio=bio, profile_pic=get_user_info(user_id)[0][3], username=username, logged_in=True)


# Route to bring a logged in user to a page where they can logout
@app.route('/logout')
def logout():
	return redirect(url_for('feed'))


# Route to allow a user to create a new post
@app.route('/new-post')
def new_post():
	user_id = request.args.get('user_id')
	return render_template('new_post.html', user_id=user_id, logged_in=True)


# Route to create a new post based on the form data from the new post page
@app.route('/new-post-execute', methods=['POST'])
def new_post_execute():
	user_id=request.args.get('user_id')

	# get form data
	f = request.files['file']
	caption = request.form['caption']

	add_post(user_id, f, caption)

	return redirect(url_for('my_profile', user_id=user_id))

# Route for a user to find other users
# Lists and links to all users in the database
@app.route('/find_users')
def find_users():
	user_id = request.args.get('user_id')
	logged_in = request.args['logged_in']

	# get boolean value of logged_in string
	if logged_in == "True":
		logged_in = True
	else:
		logged_in = False



	users = get_users()

	int_user_id = int(user_id) # must be made to compare to user data so that the user doesn't see their own name

	return render_template('find_users.html', user_id=user_id, logged_in=logged_in, users=users, int_user_id=int_user_id)


# Route to display the profile information of a certain user given user id
@app.route('/profile/<profile_id>')
def profile(profile_id):

	logged_in = request.args.get('logged_in')
	user_id = request.args.get('user_id')

	# if the user id and the profile id are the same then it is this user
	# redirect to my_profile
	if int(user_id) == int(profile_id):
		return redirect(url_for('my_profile', user_id=user_id))

	# get boolean value of logged_in string
	logged_in = get_bool(logged_in)

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

	return render_template('profile.html', user_id=user_id, logged_in=logged_in, profile_id=profile_id, name=name, bio=bio, profile_pic=profile_pic, username=username, posts=posts, following=following)

# Route that is executed when one user clicks the button to follow or unfollow another
@app.route('/follow-operation')
def follow_operation():

	# get profile data to pass back into the profile template
	user_id = request.args.get('user_id')
	profile_id = request.args.get('profile_id')
	name = request.args.get('name')
	bio = request.args.get('bio')
	profile_pic = request.args.get('profile_pic')
	username = request.args.get('username')
	following = request.args.get('following')
	logged_in = request.args.get('logged_in')

	# get boolean value of logged_in string and following string
	logged_in = get_bool(logged_in)
	following = get_bool(logged_in)

	following = follow(user_id, profile_id)

	posts = get_posts(profile_id)

	return render_template('profile.html', user_id=user_id, logged_in=logged_in, profile_id=profile_id, name=name, bio=bio, profile_pic=profile_pic, username=username, posts=posts, following=following)


# Route that shows a user's followers
# Exectues when clicking links to a user's followers from their profile page
@app.route('/<profile_id>/followers')
def followers(profile_id):
	# get follower ids then get all info about each id
	followers_ids = get_followers(profile_id)
	followers = []
	for id in followers_ids:
		followers.append(get_user_info(id))

	print(followers)


	logged_in = get_bool(request.args.get('logged_in'))
	user_id = request.args.get('user_id')

	# render template with the followers passed in and the boolean followers set true, meaning this is a followers list
	return render_template('followers_or_following.html', users=followers, followers=True, user_id=user_id, logged_in=logged_in)

# Route to show the user's that a given user follows
@app.route('/<profile_id>/following')
def following(profile_id):
	logged_in = get_bool(request.args.get('logged_in'))
	user_id = request.args.get('user_id')

	following_ids = get_following(profile_id) # get following of this user
	
	# iterate through ever id that this user follows and get data about that user
	following = []
	for id in following_ids:
		following.append(get_user_info(id))

	print(following)

	# render template with the following passed in and the boolean followers set false, meaning this is a list of users followed
	return render_template('followers_or_following.html', users=following, followers=False, user_id=user_id, logged_in=logged_in)

# Endpoint to delete a post
# takes 
@app.route('/delete-post/<user_id>/<post_id>')
def delete_post(user_id, post_id):
	delete_post_operation(post_id)

	return redirect(url_for('my_profile', user_id=user_id))




if __name__ == '__main__':
	app.run(debug=True)




# start cloud sql proxy on local - ./cloud_sql_proxy -instances=social-300422:us-east4:user-images=tcp:3306

# TODO
# Add error handling for all inputs
# Make password field hidden
# Make it so you can't use a username that is taken
# Edit profile

# maybe find way to compress images on google cloud storage uploads
# Find how to check if an image is the right file type
# add a post preview before actually posting
# delete posts
# comment code better - add headers on top of documents and do better with commenting each endpoint - explain parameters
# TOKENS for users being logged in
# Figure out picture upload bug for large images
