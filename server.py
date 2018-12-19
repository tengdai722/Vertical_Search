from frontier_toolkit import *
import os
from flask import Flask, request, render_template, session, g, redirect, \
    Response  # session is a module that allows us to hold login information

"""
Webserver for VSearch
This file includes all server side logic for front end HTTP requests.
It utilizes the API specified in frontier_toolkit.py to process user requests, 
queries, and registration.
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


@app.route('/search/', methods=["GET", "POST"])
def search():
    srch = str(request.form["search_text"])
    print("query_string =", srch)

    if "username" not in session:
        print("search for guest user")
        res_titles, res_bodies, res_idx = query(srch, guest_user, data, vocab, titles, document_bodies)
        # if search not matched
        if len(res_titles) == 0:
            return render_template("display.html", title="Cannot match any document with query '%s'" % srch)
        else:
            return render_template("display.html", title="Search Results",
                                   results=search_result_to_html_tag(res_titles, res_bodies, res_idx))
    else:
        print("search for user %s" % session["username"])
        user = auth.get_current_login_user()
        res_titles, res_bodies, res_idx = query(srch, user, data, vocab, titles, document_bodies)

        # if search not matched
        if len(res_titles) == 0:
            return render_template("display.html", title="Cannot match any document with query '%s'" % srch,
                                   username=session["username"])
        else:
            return render_template("display.html", title="Search Results", username=session["username"],
                                   results=search_result_to_html_tag(res_titles, res_bodies, res_idx))


def search_result_to_html_tag(res_titles, res_bodies, res_idx):
    result = []
    for i in range(len(res_titles)):
        result.append({"doc_title": res_titles[i], "doc_body": res_bodies[i], "idx": res_idx[i]})
    return result


@app.route('/show_article/', methods=["GET"])
def show_article():
    try:
        click_index = int(request.args["click"])
        print("Clicked document idx:", click_index)
    except ValueError:
        display_content("Error: unknown document clicked.")
        return
    if "username" not in session:
        return render_template("display.html", title="View article",
                               results=[{"doc_title": titles[click_index], "doc_body": document_bodies[click_index]}])
    else:
        # update feedback for current logged in user.
        feedback(click_index, auth.get_current_login_user(), topic_dict, document_topic_str_dict)
        return render_template("display.html", title="View article", username=session["username"],
                               results=[{"doc_title": titles[click_index], "doc_body": document_bodies[click_index]}])


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

    data, vocab, titles, topic_dict, document_topic_str_dict, document_bodies = process()
    auth = Authenticator(data.shape[0], topic_dict, document_topic_str_dict)
    guest_vector = np.zeros(data.shape[0])
    guest_user = User(guest_vector, guest_vector, "guest", "guest")


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
