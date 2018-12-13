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

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = os.urandom(24)


@app.route('/', methods=["GET"])
@app.route('/index.html', methods=["GET"])
def home():
    if "username" not in session:
        return render_template("index.html")
    else:
        print("index page with username", session["username"])
        return render_template("index.html", username=session["username"])


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


@app.route('/users/login/action/', methods=["POST"])
def do_login():
    uname = str(request.form["username"])
    psw = str(request.form["password"])

    message = auth.login(uname, psw)

    if message == "Error: Username does not exist.":
        print("username does not exist, please sign up")
        return display_content(message)
    elif message == "Error: Someone else is currently logged in.":
        print("Someone else is currenly logged in.")
        return display_content(message)
    elif message == "Error: Incorrect password.":
        print("Incorrect password, please try again")
        return display_content(message)
    elif message == "Successfully logged in.":
        print("succesfully logged in")
        session['username'] = uname
        return home()


@app.route('/register/', methods=["GET"])
def signup():
    return render_template("register.html")


@app.route('/logout/', methods=["GET"])
def logout():
    auth.logout_current_user()
    session.pop('username', None)
    return redirect("index.html")


@app.route('/display/', methods=["GET"])
def display_content(title=''):
    if title:
        return render_template("display.html", title=title)
    else:
        return render_template("display.html")


@app.route('/users/signup/add/', methods=["POST"])
def add_account():
    username = str(request.form["username"])
    password = str(request.form["password"])
    occupation = str(request.form["occupation"])

    print("register", username, password, occupation)

    message = auth.register(username, password, occupation)

    return display_content(message)


if __name__ == "__main__":
    import click

    data, vocab, titles, topic_dict, document_topic_str_dict = process()
    auth = Authenticator(data.shape[0], topic_dict, document_topic_str_dict)

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
