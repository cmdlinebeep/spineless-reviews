# Project 1 -- Spineless Reviews

#### Web Programming with Python and JavaScript

I tried to go above and beyond with this assignment.  It meets all the requirements, but is also visually appealing and easy to use.  I put a lot of thought into the UX.

User registration and authentication are all handled using Flask sessions.  The home screen includes a "quote of the day" about reading or books in general.

Once logged in, users can search for books by ISBN, author, or book title.  Partial matches work and the search is forgiving regarding spacing and capitalization.

Once a user finds a book to click on, more info is displayed, including the cover jacket of the book, the Goodreads review count, as well as stars are dynamically
generated.  If there are existing Spineless Reviews, these are also shown.  Users are enforced to be only able to add on review.

Finally, there is an API URL endpoint that other programs can use.

## Try it out first!
### http://spineless-reviews.herokuapp.com/

## Video in action
### https://youtu.be/M2o-WPxvDR8

## To clone and set it up yourself
1. You'll need a Postgres DB set up on Heroku first.  Create account.  Create new app.  Configured add-ons, add Heroku Postgres.  Use Hobby Dev free plan and Provision it.
2. You'll need to install Python 3.6 or higher, and Flask.  To download all project requirements, use `pip install -r requirements.txt`
      * I recommend using a virtual environment.  A link on that I found useful:  https://dev.to/codemouse92/dead-simple-python-virtual-environments-and-pip-5b56
3. You'll need to set these variables in your local terminal when running with the Flask dev server:
```
set FLASK_APP=application.py
set FLASK_DEBUG=1
set DATABASE_URL=postgres://<link from Heroku.  Log in and find your database, click View Credentials.  This was from the first step.>
set GOODREADS_API_KEY=<insert your own Goodreads API Key, just go to goodreads.com/api/keys and apply for one.  Don't need "secret key" for read-only>
```
4. You'll want to probably first seed your Postgres DB before you serve up the app on local host.  Running `python import.py` will seed the books, quotes, and a few reviews. 
It may take a while to run, there are 5000 books which can take some time.
5. Procfile and runtime.txt are used by Heroku.  More here and in the tutorial below:  https://devcenter.heroku.com/articles/getting-started-with-python?singlepage=true

## I found these resources helpful in my journey and perhaps you will too
1. Good bit on Python function decorators, which are used for the routing functions (and the login_required function) in Flask.  
https://flask.palletsprojects.com/en/1.0.x/patterns/viewdecorators/
2. Very helpful article to help deploy it to Heroku.   https://pybit.es/deploy-flask-heroku.html
3. Those variables you had set locally need to be set for Heroku too.  It's done slightly differently.  https://devcenter.heroku.com/articles/config-vars

Happy Reviewing!
--Joel




