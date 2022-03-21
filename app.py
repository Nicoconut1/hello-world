from flask import Flask, render_template, request, redirect, session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "lgfjh ahg lkg hg hldhg kjfxzh hds g;j"
DATABASE = "C:/Users/18488/OneDrive - Wellington College/13DTS/Smile/identifier.db"


def create_connection(db_file):
    """
    Create a connection with the database
    parameter: name of the database file
    returns: a connection to the file
    """
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
        return None


def is_logged_in():
    """
    A function to return whether the user is logged in or not
    """
    if session.get("email") is None:
        print("Not logged in")
        return False
    else:
        print("Logged in")
        return True


@app.route('/')
def render_homepage():
    return render_template('home.html', logged_in=is_logged_in())


@app.route('/menu')
def render_menu_page():
    con = create_connection(DATABASE)

    query = "SELECT name, description, volume, price, image, id FROM product"
    cur = con.cursor()  # Creates a cursor to write the query
    cur.execute(query)  # Runs the query
    product_list = cur.fetchall()
    con.close()

    return render_template('menu.html', products=product_list, logged_in=is_logged_in())


@app.route('/addtocart/<product_id>')
def render_addtocart_page(product_id):
    try:
        product_id = int(product_id)
    except ValueError:
        print("{} is not an integer".format(product_id))
        return redirect(request.referrer + "?error=Invalid+product+id")

    userid = session['customer_id']
    timestamp = datetime.now()
    print("Add {} to cart".format(product_id))

    query = "INSERT INTO cart(id,customerid,productid,timestamp) VALUES (NULL,?,?,?)"
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, (userid, product_id, timestamp))
    con.commit()
    con.close()
    return redirect(request.referrer)


@app.route('/contact')
def render_contact_page():
    return render_template('contact.html', logged_in=is_logged_in())


@app.route('/login', methods=['GET', 'POST'])
def render_login_page():
    if request.method == 'POST':
        print(request.form)
        email = request.form.get('email').strip()
        password = request.form.get('password')

        con = create_connection(DATABASE)
        query = "SELECT id, fname, password FROM customer WHERE email=?"
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()

        if user_data:
            user_id = user_data[0][0]
            first_name = user_data[0][1]
            db_password = user_data[0][2]
        else:
            return redirect("/login?error=Email+or+password+is+incorrect")
        # Set up a session for this login

        if not bcrypt.check_password_hash(db_password, password):
            return redirect("/login?error=Email+or+password+is+incorrect")

        session['email'] = email
        session['customer_id'] = user_id
        session['fname'] = first_name
        session['cart'] = []
        return redirect('/')
    return render_template('login.html', logged_in=is_logged_in())


@app.route('/logout')
def render_logout_page():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect('/?message=See+you+next+time')


@app.route('/signup', methods=['GET', 'POST'])
def render_signup_page():
    if request.method == 'POST':
        print(request.form)
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')

        if password != password2:
            return redirect('signup?error=Passwords+do+not+match')

        if len(password) < 8:
            return redirect('signup?error=Password+must+be+8+characters+or+more')

        hashed_password = bcrypt.generate_password_hash(password)
        con = create_connection(DATABASE)

        query = "INSERT INTO customer(id, fname, lname, email, password) VALUES(NULL,?,?,?,?)"

        cur = con.cursor()  # Creates a cursor to write the query
        try:
            cur.execute(query, (fname, lname, email, hashed_password))  # Runs the query
        except sqlite3.IntegrityError:
            return redirect('/signup?error=Email+is+already+used')
        con.commit()
        con.close()
        return redirect('/login')

    error = request.args.get('error')
    if error is None:
        error = ""

    return render_template('signup.html', error=error, logged_in=is_logged_in())


app.run(host='0.0.0.0', debug=True)
