from flask import Flask, request, render_template, redirect, session, url_for
from flask import request as request
import mysql.connector
import db
import datetime
from qu import calculateResults
import DBcm
from flask_mail import Mail, Message
import secrets

app = Flask(__name__)
app.secret_key = "abbcd"

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'mathsquizgenerator@gmail.com'
app.config['MAIL_PASSWORD'] = 'Teacher123'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

connection = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "root",
    "database": "quiz",
}


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
                cursor.execute('SELECT * FROM student WHERE username = %s', (username,))
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
                cursor.execute('SELECT * FROM student WHERE username = %s', (username,))
                account = cursor.fetchone()

            # If account exists show error and validation checks
            if account:
                msg = 'Account already exists!'

            else:
                name = request.form['firstname']
                surname = request.form['surname']
                # Account doesnt exists and the form data is valid, now insert new account into student table
                with DBcm.UseDatabase(connection) as cursor:
                    cursor.execute("INSERT INTO student (username,password,email,userGroup,name,surname)" \
                                   " VALUES ('%s', '%s', '%s', '%s', '%s', '%s')" % (
                                       username, password, email, group, name, surname))
                    id = cursor.lastrowid
                msg = 'You have successfully registered!'
                sendAuthenticationEmail(id,username, name, surname, email, group)

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
        message = ""
        with DBcm.UseDatabase(connection) as cursor:
            SQL = "select * from teacher where username='%s' and password='%s'" % (username, password)
            cursor.execute(SQL)
            teacher = cursor.fetchone()
            if teacher == None:
                SQL = "select * from student where username='%s' and password='%s' and authenticated=1" % (
                    username, password)
                cursor.execute(SQL)
                student = cursor.fetchone()
                if student is None:
                    message = "Account is not authenticated or credentials are incorrect"

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
                    """
                    result = calculateResults(data, questions)
                    r = "{:.2f}".format(result)
                    today = datetime.date.today()
                    
                    with DBcm.UseDatabase(connection) as cursor:
                        SQL = "insert into results(userID,userGroup,result,quizDate,username,quizID)" \
                              " values('%s','%s','%s','%s','%s','%s')" % (
                                  session['id'], session['group'], r, str(today), session['username'], quizID)

                        cursor.execute(SQL)
                    """
                    return redirect(url_for('getTest', quizID=quizID))

                else:

                    return render_template("quiz.html", the_questions=questions)


@app.route("/createQuiz", methods=["GET", "POST"])
def createQuiz():
    if not 'access' in session:
        return redirect(url_for('login'))
    else:
        message = ""
        studentGroups = db.getStudentGroups(session['id'])
        data = request.form
        if request.method == "POST":
            message = "Quiz created"
            db.createQuiz(data)
            session['group'] = data['group']
        return render_template("createQuiz.html", the_message=message, the_data=data, the_studentGroups=studentGroups)


@app.route("/studentresults", methods=["GET", "POST"])
def resultsPage():
    results = db.userResults(session['id'])
    columnNames = ["Quiz ID", "Quiz Date", "Quiz Name", "Final Score", "Transcript"]
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
        info = db.quizUserInfo(userID, quizID)
        answers = db.getSelectedAnswers(id, userID)
    return render_template("transcript.html", the_questions=questions, the_answers=answers, userInfo=info)


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

        if 'groupName' in request.form:
            groupName = request.form['groupName']
            db.createGroup(session['id'], groupName)
            msg = "Group " + str(groupName) + " has been created"
            allgroups = db.getStudentGroups()
            teachersGroups = db.getStudentGroups(session['id'])
            return render_template("groupSettings.html", the_msg=msg, the_allGroups=allgroups,
                                   the_teachersGroups=teachersGroups)
        elif 'group' in request.form:
            selectedgroups = request.form
            db.changeTeacherGroups(selectedgroups, session['id'])
            allgroups = db.getStudentGroups()
            teachersGroups = db.getStudentGroups(session['id'])
            return render_template("groupSettings.html", the_allGroups=allgroups, the_teachersGroups=teachersGroups,
                                   the_selectedgroups=selectedgroups)
        elif 'studentGroup' in request.form:

            selectedGroup = request.form['studentGroup']
            students = db.getGroupStudents(selectedGroup)
            session['g'] = selectedGroup
            return render_template("groupSettings.html", the_allGroups=allgroups, the_teachersGroups=teachersGroups,the_students=students,the_a=selectedGroup)

        elif 'userInformation' in request.form:
            info = request.form

            b = session['g']
            db.authenticateUsers(info,b)
            students = db.getGroupStudents(b)
            return render_template("groupSettings.html", the_allGroups=allgroups, the_teachersGroups=teachersGroups,
                                   the_info=info,the_students=students,the_a=b)

    else:

        return render_template("groupSettings.html", the_allGroups=allgroups, the_teachersGroups=teachersGroups)


u = secrets.token_urlsafe()


def sendAuthenticationEmail(id,username,name,surname,emailAddress,group):
    global u

    email = Message('Student account requires authentication', sender='mathsquizgenerator@gmail.com',
                    recipients=['mathsquizgenerator@gmail.com'])
    part2 = secrets.token_hex(16)
    link = u + part2

    email.body = "This notification is generated automatically. \r\n\n" \
                 "A new account has been created and requests authorisation to join group: " + str(group) + ".\r\n\n" \
                 "Registration data: \r\n" \
                  "Name: " + str(name) + "\r\n" \
                  "Surname: " + str(surname) + "\r\n" \
                  "Group: " + str(group) + "\r\n" \
                  "Email: " + str(emailAddress) + "\r\n\n" \
                  "The account can be authenticated manually inside of the quiz application or" \
                                           " by clicking on the following link:  http://127.0.0.1:5000/" + str(link) + "/" + str(id)
    with mail.connect() as connector:
        connector.send(email)


@app.route("/" + u + "<string(length=32):key>/<int:id>")
def authenticate(key, id):
    userID = id

    with DBcm.UseDatabase(connection) as cursor:
        SQL = "update student set authenticated = 1 where userID = '%s'" % userID
        cursor.execute(SQL)

    return "Account has been authenticated"


if __name__ == '__main__':
    app.run(debug=True)
