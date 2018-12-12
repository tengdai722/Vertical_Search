from frontier_toolkit import *
import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, session, g, redirect, \
    Response  # session is a module that allows us to hold login information
from collections import defaultdict
import random  # module for random integer generator

"""
Webserver for News Feed
Course Project for CS510

"""

data, vocab, titles, topic_dict, document_topic_str_dict = process()
auth = Authenticator(data.shape[0], topic_dict, document_topic_str_dict)
try:
    user = auth.get_current_login_user()
except Exception as inst:
    print(inst)

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = os.urandom(24)


@app.route('/', methods=["GET"])
def home():
    return render_template("index.html")


@app.route('/search/', methods=["POST"])
def search():
    srch = str(request.form['search'])
    srch_result = []  # array instead of dictionary with a key since one search as key
    # getting questions match
    print(srch)

    srch_result = query(srch, user, data, vocab, titles)

    print("search successful!")

    context = dict(search=srch, search_result=srch_result)
    return render_template("search.html", **context)


@app.route('/users/login/', methods=["GET"])
def login():
    # return to columbia overflow (call the original)
    # from username and password, find uid (query)
    # keep track of uid throughout this session/interaction between the user and the site
    session["logged_in"] = False
    return render_template("login.html")


@app.route('/users/login/action/', methods=["POST"])
def do_login():
    uname = str(request.form["uname"])
    psw = str(request.form["psw"])

    message = auth.login(uname, psw)

    if message == "Error: Username does not exist.":
        print("username does not exist, please sign up")
        return signup()
    elif message == "Error: Someone else is currently logged in.":
        print("Someone else is currenly logged in.")
        return home()
    elif message == "Error: Incorrect password.":
        print("Incorrect password, please try again")
        return login()
    elif message == "Successfully logged in.":
        print("succesfully logged in")
        session['logged_in'] = True
        session['username'] = uname
        return home()


@app.route('/users/signup/', methods=["GET"])
def signup():
    return render_template("signup.html")


# USER SIGNS IN

@app.route('/users/signup/add/', methods=["POST"])
def add_account():
    username = str(request.form["username"])
    password = str(request.form["password"])
    occupation = str(request.form["occupation"])

    auth.register(username, password, occupation)

    return home()  # return to list of communities


if __name__ == "__main__":
    import click


    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='127.0.0.1')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):
        """
        This function handles command line parameters.
        Run the server using:

            python server.py

        Show the help text using:

            python server.py --help

        """

        HOST, PORT = host, port
        print("running on %s:%s" % (HOST, PORT))
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


    run()
