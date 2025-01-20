from flask import Flask, request, redirect, url_for, flash, session, jsonify, render_template, send_from_directory
from flask_socketio import SocketIO
import sqlite3
import uuid
import logging
import time
import os
import json
import datetime

app = Flask(__name__)
app.secret_key = 'ensamgip123'
socketio = SocketIO(app)
home_paths = json.loads(open("home.json", "r").read())
side_panel = json.loads(open("side_panel.json", "r").read())

UPLOAD_FOLDER = 'issues_pics'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ranks = {
    3: "administration",
    2: "chef", # dep dyalo
    1: "responsable", # suivi sans creer
    0: "prof",
    -1: "technicien infrastructures",
    -2: "technicien atelier", 
}

logging.basicConfig(level=logging.DEBUG)

def query_db(query, args=(), file="", one=False):
    try:
        with sqlite3.connect(file) as conn:
            conn.row_factory = sqlite3.Row 
            cur = conn.cursor()
            cur.execute(query, args)
            logging.debug(f"qdb Executed query: {query} with args: {args}")
            rv = cur.fetchall()
            if one:
                return rv[0] if rv else None 
            return rv  
            
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return None


def update_db(query, file="", args=()):
    try:
        with sqlite3.connect(file) as conn:
            cur = conn.cursor()
            cur.execute(query, args)
            conn.commit()
            logging.debug(f"udb Executed update: {query} with args: {args}")
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")

techniciens = query_db(f'SELECT * FROM users WHERE position IN (-1, -2)', one=False, file='users.db')

def allowed_file(filename):
    ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS, filename.rsplit('.', 1)[-1].lower()

@app.route('/', methods=['GET', 'POST'])
def login():
    if "email" in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']
        logging.debug(f"Attempting to log in with email: {email}")
        
        user = query_db('SELECT * FROM users WHERE email = ? AND password = ?', [email, password], one=True, file='users.db')
        
        if user:
            session_id = str(uuid.uuid4())
            session['email'] = user['email']
            session['username'] = user['username']
            session['pos'] = user['position']
            session['position'] = ranks[user['position']]
            session['phonenum'] = user['phonenum']
            session['session_id'] = session_id
            session['dep'] = user['dep']
            session['current_issue'] = ""
            
            logging.debug(f"User {email} logged in successfully.")
            
            return jsonify({'success': True, 'newPath': url_for('home')})
        else:
            logging.debug("No user found with that email.")
            return jsonify({'success': False, 'message': 'Invalid email or password'})

    return render_template('login.html')

@app.route('/home')
def home():
    if 'email' in session:
        print(session['position'])
        return render_template('home.html', username=session.get('username'), email=session.get('email'), layout=home_paths[session['position']], side_panel=side_panel[session['position']])
    else:
        flash("You need to be logged in.")
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()  
    flash("You have been logged out.")
    return redirect(url_for('login'))

@app.route("/new_demand", methods=['GET', 'POST'])
def new_demand():
    if "email" in session and session['pos'] >= 0:
        if request.method == 'POST':
            file = request.files.get('photo')
            print(file, "eee")
            if file:
                print(file.filename)
                allowed, extension = allowed_file(file.filename)
                if file and allowed:
                    filename = f"{time.time()}.{extension}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    print(filename)
            else:
                filename = ""        
            update_db('INSERT INTO issues VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', args=[str(uuid.uuid4()).split("-")[0], session['email'], session['phonenum'], datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), request.form.get('departement'), request.form.get('salle'), request.form.get('typeProbleme'), request.form.get('description'), filename, session['username'], 0, "", "", 1 if session['pos'] == 0 else 2], file='issues.db')
            # return redirect(url_for('home'))
            return jsonify({'success': True, 'newPath': url_for('home')})
        return render_template('new_demand.html', username=session.get('username'), email=session.get('email'), side_panel=side_panel[session['position']])
    else:
        return redirect(url_for('login'))

@app.route("/show_demands", methods=['GET', 'POST'])
def show_demands():
    status = {"en attente": "= 0", "en cours": "= 1", "traitees": "= 3", "non planifier": "IN ('0','1')", "planifier": "= 2", None: "IS NOT NULL"}[request.args.get('status')]
    typpe = {'infrastructures': "= 1", 'ateliers': "= 2", None: "IS NOT NULL"}[request.args.get('type')]
    if "email" in session:
        if session['position'] == "technicien":
            issues = query_db(f'SELECT * FROM issues WHERE technicien = ? AND valid {status}', [session['username']], one=False, file='issues.db')
        elif session['position'] == "responsable":
            issues = query_db(f"SELECT * FROM issues WHERE valid {status} AND typpe {typpe}", one=False, file='issues.db')
        elif session['position'] == "chef":
            issues = query_db(f"SELECT * FROM issues WHERE departement = ? AND valid {status} AND typpe {typpe}", [session['dep']], one=False, file='issues.db')
        elif session['position'] == "prof":
            issues = query_db(f'SELECT * FROM issues WHERE email = ? AND valid {status}', [session['email']], one=False, file='issues.db')
        else:
            issues = query_db(f'SELECT * FROM issues WHERE valid {status}', one=False, file='issues.db')
            
        return render_template('show_demands.html', username=session.get('username'), email=session.get('email'), side_panel=side_panel[session['position']], issues=issues or [], has_power = session['pos'] >= 2, request=request, session=session)
    else:
        return redirect(url_for('login'))
    
@app.route("/demandes", methods=['GET', 'POST'])
def demandes():
    if "email" in session:
        id = request.args.get('id')
        if not id and request.method != 'POST':
            return redirect(url_for('home'))

        if request.method == 'POST' and session['pos'] >= 1:
            try:
                technicien = request.form.get('technicien')
                id = request.form.get('uuidd')
                if technicien and id:
                    
                    update_db("UPDATE issues SET valid = ?, technicien = ? WHERE uuid = ?", 
                              args=(1, technicien, id), 
                              file="issues.db")
                    return redirect(url_for('home'))
                else:
                    return jsonify({'success': False, 'message': 'Missing required data'}), 400
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500
            
        if request.method == 'POST' and session['pos'] <= -1:
            try:
                id = request.form.get('uuidd')
                if id:
                    issue = query_db('SELECT * FROM issues WHERE uuid = ?', [id], one=True, file='issues.db')
                    if issue['valid'] == 1:
                        print(2, request.form.get("date"), id)
                        update_db("UPDATE issues SET valid = ?, dueto = ? WHERE uuid = ?", 
                                args=(2, request.form.get("date"), id), 
                                file="issues.db")
                    elif issue['valid'] == 2:
                        update_db("UPDATE issues SET valid = ?, dueto = ? WHERE uuid = ?", 
                                args=(3, "", id), 
                                file="issues.db")
                    return redirect(url_for('home'))
                else:
                    return jsonify({'success': False, 'message': 'Missing required data'}), 400
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        issue = query_db('SELECT * FROM issues WHERE uuid = ?', [id], one=True, file='issues.db')
        if issue:
            return render_template('demandes.html', username=session.get('username'), email=session.get('email'), 
                                   side_panel=side_panel[session['position']], issue=issue, pos=session['pos'] >= 1, technicien = session['pos'] == -1, techniciens = [i for i in techniciens if i['position'] == -1] if session['pos'] == 1 else [i for i in techniciens if i['position'] == -2])
        else:
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))
    
@app.route("/issues_pics/<filename>")
def issues_pics(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    socketio.run(app, host="localhost", port=5002, debug=True)
