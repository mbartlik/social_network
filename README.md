# Social Network
This is a web application that features the basics of a social network, including making posts, following other users, and creating a unique profile with a username, bio, and profile picture. Rather than a fully scaled up application that is meant to be marketed, this project is largely for personal development and demonstration of skills. 

[maxs-social-network.uk.r.appspot.com](maxs-social-network.uk.r.appspot.com)

## Details
The app as a whole is run on Google App Engine, and the backend is coded in python and built on the Flask framework. For data storage it relies on both Google Cloud SQL on a MySQL server and a Google Cloud Storage bucket used to store images. For security it implements JSON Web Tokens, where upon login each user is assigned a unique encrypted token that will last 6 hours. With every action on the application the user is authenticated to see if their token is valid. 

## More Functionalities
Upon going to the home page of the site, the user must enter their login info, which will then be checked with the information stored in the database. If it is correct the user will be logged in and given an encoded JSON Web Token which will be valid for 6 hours and will be checked for every action the user makes. A user also may create an account which will create a new SQL entry for that user with a unique username, bio, name, and password. Every user has a feed which features the posts, newest to oldest, of every user they follow. A user can follow or unfollow other users by going to the profiles of the desired users. When making a new post the picture that the user uploads is put in a google cloud storage bucket assigned to this site, and that picture can be accessed whenever necessary to load the given post. 
