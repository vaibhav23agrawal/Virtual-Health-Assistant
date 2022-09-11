from flask import Flask, render_template, request, redirect, url_for, session, Response, flash, jsonify
import MySQLdb.cursors
import re
from flask_mysqldb import MySQL
import mysql.connector
from mysql import connector

app = Flask(__name__)
app.secret_key = 'your secret key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'pass123'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_DB'] = 'testing'

mysql = MySQL(app)

def exec_sql(cursor, sql_file):
    print("\n[INFO] Executing SQL script file: '%s'" % (sql_file))
    statement = ""

    for line in open(sql_file):
        if re.match(r'--', line):  # ignore sql comment lines
            continue
        if not re.search(r';$', line):  # keep appending lines that don't end in ';'
            statement = statement + line
        else:  # when you get a line ending in ';' then exec statement and reset for next statement
            statement = statement + line
            #print "\n\n[DEBUG] Executing SQL statement:\n%s" % (statement)
            try:
                cursor.execute(statement)
            except Exception as e:
                print("\n[WARN] MySQLError during execute statement \n\tArgs: '%s'" % (str(e.args)))

            statement = ""
# this code should execute only once
@app.before_first_request
def myfunc():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    exec_sql(cursor, "medico.sql")

@app.route("/", methods=["POST", "GET"])
def login():
    return render_template('login.html')


@app.route("/register", methods=["POST", "GET"])
def resister():
    msg = ''
    if request.method == 'POST' and 'name' in request.form and 'pwd' in request.form:
        name = request.form['name']
        mail = request.form['mail']
        pwd = request.form['pwd']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        sql = 'insert into patient (name,mail,pwd) values(%s,%s,%s)'
        values = (name, mail, pwd)
        cursor.execute(sql, values)
        mysql.connection.commit()
        print('hi')

        return jsonify({'success': 'Account not found'})
    return render_template('login.html')


@app.route("/home", methods=["POST", "GET"])
def home():
    msg = ''
    if request.method == 'POST' and 'mail' in request.form and 'pwd' in request.form:
        mail = request.form['mail']
        pwd = request.form['pwd']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'select * from patient where mail= %s and pwd =%s', (mail, pwd))
        account = cursor.fetchone()
        cursor.execute('select * from doctor')
        doctor = cursor.fetchall()

        cursor.execute('select * from queries')
        queries = cursor.fetchall()

        cursor.execute('select * from consult where patient_mail= %s', [mail])
        consult = cursor.fetchall()
        if consult:

            c = []
            for i in range(0, len(consult)):
                c.append(consult[i]['doctor_id'])
        else:
            c = []

        cursor.execute(
            "SELECT distinct a.name , a.dept, a.link, b.status , b.timing from doctor a, consult b where a.id=b.doctor_id and b.patient_mail= %s ", [mail])
        status = cursor.fetchall()
        if status:
            status = status
            len1 = len(status)
        else:
            status = 0
            len1 = 0

        if account:
            session['loggedin'] = True
            session['s_mail'] = account['mail']
            session['s_pwd'] = account['pwd']
            return render_template('index.html', doctor=doctor, len=len(doctor), patient=account, c=c, status=status, len1=len1, queries=queries, len2=len(queries))
        else:
            return render_template('login.html', msg='incorrect username/password')

    elif 's_mail' in session:
        mail = session.get('s_mail')
        pwd = session.get('s_pwd')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('select * from consult where patient_mail= %s', [mail])
        consult = cursor.fetchall()

        c = []
        for i in range(0, len(consult)):
            c.append(consult[i]['doctor_id'])

        cursor.execute(
            "SELECT distinct a.name , a.dept, a.link, b.status , b.timing from doctor a, consult b where a.id=b.doctor_id and b.patient_mail= %s ", [mail])

        status = cursor.fetchall()

        cursor.execute(
            'select * from patient where mail= %s and pwd =%s', (mail, pwd))
        account = cursor.fetchone()

        cursor.execute('select * from queries')
        queries = cursor.fetchall()

        cursor.execute('select * from doctor')
        doctor = cursor.fetchall()

        return render_template('index.html', doctor=doctor, len=len(doctor), patient=account, c=c, status=status,
                               len1=len(status), queries=queries, len2=len(queries))

    else:
        return redirect(url_for('login'))


@app.route("/consult", methods=["POST", "GET"])
def consult():
    if 's_mail' in session:
        patient_mail = request.args.get('a')
        doctor_id = request.args.get('b')
        # print(patient_mail)
        # print(doctor_id)

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'insert into consult (patient_mail,doctor_id) values (%s,%s)', (patient_mail, doctor_id))
        mysql.connection.commit()
        return redirect(url_for('home'))

    else:
        return redirect(url_for('login'))


@app.route("/update", methods=["POST", "GET"])
def update():
    if 's_mail' in session and request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        location = request.form['location']
        BMI = request.form['bmi']
        mail = session.get('s_mail')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('update patient set name = %s , age=%s, gender= %s , location=%s , BMI=%s where mail =%s',
                       (name, age, gender, location, BMI, mail))
        mysql.connection.commit()
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))


@app.route('/askquery', methods=["POST", "GET"])
def askquery():
    if 's_mail' in session and request.method == 'POST':
        usrquestion = request.form['usrquestion']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'insert into queries (question) values(%s)', [usrquestion])
        mysql.connection.commit()
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))


@app.route('/logout/')
def logout():
    if 's_mail' in session:
        # Remove session data, this will log the user out
        session.clear()

        # Redirect to login page
        return redirect(url_for('login'))



