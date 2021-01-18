# Social Network
This is a web application that features the basics of a social network, including making posts, following other users, and creating a unique profile with a username, bio, and profile picture. Rather than a fully scaled up application that is meant to be marketed, this project is largely for personal development and demonstration of skills. 

[https://social-300422.uk.r.appspot.com](https://social-300422.uk.r.appspot.com/login)

## Details
The app as a whole is run on Google App Engine, and the backend is coded in python and built on the Flask framework. For data storage it relies on both Google Cloud SQL on a MySQL server and a Google Cloud Storage bucket used to store images. For security it implements JSON Web Tokens, where upon login each user is assigned a unique encrypted token that will last 6 hours. With every action on the application the user is authenticated to see if their token is valid. 