from flask import Flask, request, render_template, redirect, session, url_for
from flask import request as request
import mysql.connector
import db
import datetime
from qu import calculateResults
import DBcm

app = Flask(__name__)
app.secret_key = "abbcd"

connection = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "root",
    "database": "quiz",
}

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="quiz"
)


@app.route("/register", methods=["GET", "POST"])
def register():
    # Output message if something goes wrong...
    msg = ''
    studentGroups = db.getStudentGroups()
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        userType = request.form['teacher']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        if userType == "true":
            # Check if account exists using MySQL
            account = ""
            with DBcm.UseDatabase(connection) as cursor:
                cursor.execute('SELECT * FROM user WHERE username = %s', (username,))
                account = cursor.fetchone()
                if not account:
                    cursor.execute('SELECT * FROM teacher WHERE username = %s', (username,))
                    account = cursor.fetchone()

            # If account exists show error and validation checks
            if account:
                msg = 'Account already exists!'

            else:
                # Account doesnt exists and the form data is valid, now insert new account into accounts table
                with DBcm.UseDatabase(connection) as cursor:
                    cursor.execute("INSERT INTO teacher (username,password,email,teacher)" \
                                   " VALUES ('%s', '%s', '%s', '%s')" % (username, password, email, userType))

                msg = 'You have successfully registered!'
        else:
            group = request.form['group']
            # Check if account exists using MySQL
            account = ""
            with DBcm.UseDatabase(connection) as cursor:
                cursor.execute('SELECT * FROM user WHERE username = %s', (username,))
                account = cursor.fetchone()

            # If account exists show error and validation checks
            if account:
                msg = 'Account already exists!'

            else:
                # Account doesnt exists and the form data is valid, now insert new account into accounts table
                with DBcm.UseDatabase(connection) as cursor:
                    cursor.execute("INSERT INTO user (username,password,email,userGroup)" \
                                   " VALUES ('%s', '%s', '%s', '%s')" % (username, password, email, group))

                msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg, the_studentGroups=studentGroups)


@app.route("/", methods=["GET", "POST"])
def login():
    student = ""
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        with DBcm.UseDatabase(connection) as cursor:
            SQL = "select * from teacher where username='%s' and password='%s'" % (username, password)
            cursor.execute(SQL)
            teacher = cursor.fetchone()
            if teacher == None:
                SQL = "select * from user where username='%s' and password='%s'" % (username, password)
                cursor.execute(SQL)
                student = cursor.fetchone()

        if teacher:
            session['access'] = True
            session['username'] = teacher[1]
            session['id'] = teacher[0]
            session['teacher'] = teacher[4]
            session['group'] = 'A'

        elif student:
            session['access'] = True
            session['username'] = student[1]
            session['id'] = student[0]
            session['group'] = student[3]

        else:
            message = "Incorrect username or password"
            return render_template("index.html", msg=message)

        return redirect(url_for('home'))
    else:
        # message = "Incorrect username or password"
        return render_template("index.html")


@app.route("/logout")
def logout():
    session.clear()

    return redirect("/")


@app.route("/home", methods=["GET", "POST"])
def home():
    if 'access' in session:

        return render_template("home.html", user=session['username'])

    else:
        return redirect(url_for('login'))


@app.route("/quiz", methods=["GET", "POST"])
def results():
    if not 'access' in session:
        return redirect(url_for('login'))
    else:

        msg = "Quiz is not available"
        today = datetime.date.today()

        ID = db.checkQuiz(session['group'], today)
        quizID = ID[0]
        if isinstance(quizID, str):
            return render_template("quiz.html", the_message=msg)
        else:
            if db.isCompleted(quizID, session['id']):
                return render_template("quiz.html", the_message=msg)
            else:
                questions = db.getQuizQuestions(quizID)

                if request.method == "POST":
                    data = request.form

                    db.answersToDatabase(data, quizID, session['id'], questions)

                    result = calculateResults(data, questions)
                    r = "{:.2f}".format(result)
                    today = datetime.date.today()
                    with DBcm.UseDatabase(connection) as cursor:
                        SQL = "insert into results(userID,userGroup,result,quizDate,username,quizID)" \
                              " values('%s','%s','%s','%s','%s','%s')" % (
                                  session['id'], session['group'], r, str(today), session['username'], quizID)

                        cursor.execute(SQL)

                    return redirect(url_for('getTest', quizID=quizID))
                    # return render_template("quiz.html", the_questions=questions, the_data=data, the_result=r, the_id=quizID)

                else:

                    return render_template("quiz.html", the_questions=questions)


@app.route("/createQuiz", methods=["GET", "POST"])
def createQuiz():
    if not 'access' in session:
        return redirect(url_for('login'))
    else:
        message = ""
        studentGroups = db.getStudentGroups()
        data = request.form
        if request.method == "POST":
            message = "Quiz created"
            db.createQuiz(data)
            session['group'] = data['group']
        return render_template("createQuiz.html", the_message=message, the_data=data, the_studentGroups=studentGroups)


@app.route("/studentresults", methods=["GET", "POST"])
def resultsPage():
    results = db.getStudentResults(session['id'])
    columnNames = ["Quiz ID", "Quiz Date", "Participant", "Final Score", "Transcript"]
    if request.method == 'POST':
        data = request.data
        return redirect(url_for("transcript.html"))

    return render_template("studentresults.html", the_results=results, the_columnNames=columnNames)


@app.route("/transcript/<string:quizID>", methods=["GET", "POST"])
@app.route("/transcript/<string:quizID>/<int:userID>", methods=["GET", "POST"])
def getTest(quizID, userID=None):
    id = quizID
    questions = db.getQuizQuestions(id)
    if userID is None:
        info = db.quizUserInfo(session['id'], quizID)
        answers = db.getSelectedAnswers(id, session['id'])
    else:
        info = db.quizUserInfo(userID,quizID)
        answers = db.getSelectedAnswers(id, userID)
    return render_template("transcript.html", the_questions=questions, the_answers=answers,userInfo=info)


@app.route("/teacherResults", methods=["GET", "POST"])
def teacherResults():
    quizIDs = ""
    studentGroups = db.getStudentGroups(session['id'])
    if request.method == "POST":
        group = request.form['studentGroup']
        s = group
        quizData = db.selectQuizes(s)

        columnNames = ["Quiz ID", "Quiz Name", "Quiz Date", "Quiz Participants"]
        return render_template("teacherResults.html", the_studentGroups=studentGroups, the_results=quizData,
                               the_columnNames=columnNames)
    return render_template("teacherResults.html", the_studentGroups=studentGroups, the_group=quizIDs)


@app.route("/quizParticipants/<string:quizID>", methods=["GET", "POST"])
def quizParticipants(quizID):
    id = quizID
    participants = db.getParticipants(id)
    columnNames = ["User ID", "Username", "Quiz Score", "Transcript"]

    return render_template("quizParticipants.html", the_results=participants, the_columnNames=columnNames, qID=id)


@app.route("/groupSettings", methods=["GET", "POST"])
def groupSettings():
    allgroups = db.getStudentGroups()
    teachersGroups = db.getStudentGroups(session['id'])

    if request.method == "POST":
        msg = ""
        groupName = request.form['groupName']
        if len(groupName) is not 0:
            db.createGroup(session['id'], groupName)
            msg = "Group " + str(groupName) + " has been created"
            return render_template("groupSettings.html", the_msg=msg,the_allGroups=allgroups, the_teachersGroups=teachersGroups)
        else:

            return render_template("groupSettings.html", the_allGroups=allgroups, the_teachersGroups=teachersGroups)
    else:

        return render_template("groupSettings.html", the_allGroups=allgroups, the_teachersGroups=teachersGroups)


if __name__ == '__main__':
    app.run(debug=True)
