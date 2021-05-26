from flask import Flask, request, render_template, redirect, session, url_for
from flask import request as request
import db
import datetime
import DBcm
from flask_mail import Mail, Message
import secrets

# crate app object
app = Flask(__name__)
# generate secret key for the application consisting of 64 hexadecimal numbers
app.secret_key = "87ewQZr"

# configure email settings
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

# registration page
@app.route("/register", methods=["GET", "POST"])
def register():
    # Output message if something goes wrong...
    msg = ''
    # get available groups that user can register to
    studentGroups = db.getStudentGroups()

    # Check if  username and password were submitted
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        isTeacher = request.form['teacher']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # check if user is creating the teacher account
        if isTeacher == "true":
            # Check if account exists using MySQL
            with DBcm.UseDatabase(connection) as cursor:
                cursor.execute("SELECT * FROM teacher WHERE username = '%s'" % username)
                account = cursor.fetchone()

            # If account exists show error and validation checks
            if account:
                msg = 'Account already exists!'

            else:
                # Account doesnt exists and the form data is valid, now insert new account into accounts table
                with DBcm.UseDatabase(connection) as cursor:
                    cursor.execute("INSERT INTO teacher (username,password,email,teacher)" \
                                   " VALUES ('%s', '%s', '%s', '%s')" % (username, password, email, isTeacher))

                msg = 'You have successfully registered!'

        else:
            group = request.form['group']
            # Check if account exists using MySQL
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
                sendAuthenticationEmail(id, username, name, surname, email, group)

    # Show registration form with message (if any)
    return render_template('register.html', msg=msg, the_studentGroups=studentGroups)

# login page
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
            if teacher is None:
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

        return render_template("index.html")

# logout page
@app.route("/logout")
def logout():
    # clear session data
    session.clear()
    # redirect to login page
    return redirect("/")

# home page consisting of student progres for both teacher and student
@app.route("/home", methods=["GET", "POST"])
def home():
    # if logged in
    if 'access' in session:
        # if logged in as teacher
        if 'teacher' in session:
            # get student groups assigned to the teacher
            studentGroups = db.getStudentGroups(session['id'])
            if request.method == "POST":
                group = request.form['studentGroup']

                studentData = db.getStudents(group)

                columnNames = ["Student ID", "Name", "Surname", "Current Progression"]
                return render_template("studentGroups.html", the_results=studentData,the_columnNames=columnNames)

            return render_template("home.html", the_studentGroups=studentGroups)
        # logged in as student
        else:
            # get student info and quiz results
            results = db.userResults(session['id'])
            # initialise empty lists for data necessary to draw the chart
            names = []
            scores = []
            movingAverage = []
            currentAverage = 0
            # for separate results data, calculate average and moving average values
            for index, i in enumerate(results):
                names.append((i[2]))
                scores.append(float(i[3]))
                currentAverage += float(i[3])
                movingAverage.append(currentAverage / (index + 1))
            # if student completed at least one quiz : get average and render page with progress chart
            if len(scores) > 0:
                overallAverage = round(sum(scores) / len(scores), 2)
                return render_template("home.html", user=session['username'], the_names=names, the_scores=scores,
                                    the_movingAverage=movingAverage, the_average=overallAverage)
            # Student did not complete any quiz: render page with a message
            else:
                return render_template("home.html", user=session['username'])
    # not logged in
    else:
        # redirect to login page
        return redirect("/")

# quiz page
@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    # if logged in
    if 'access' in session:

        # get todays date
        today = datetime.date.today()
        # check quiz availability
        ID = db.checkQuizAvailability(session['group'], today)
        quizID = ID[0]
        # if not quiz then display the message
        if isinstance(quizID, str):
            return render_template("quiz.html", the_message="Quiz is not available")
        # quiz is available
        else:
            # if quiz is already completed display the message
            if db.isCompleted(quizID, session['id']):
                return render_template("quiz.html", the_message="Quiz is already completed")
            # quiz is available and not completed yet
            else:
                # get quiz questions corresponding to the quizID
                questions = db.getQuizQuestions(quizID)

                # if quiz is submitted
                if request.method == "POST":
                    # request answers from the form
                    data = request.form
                    # send answers to the database
                    db.answersToDatabase(data, quizID, session['id'], questions)
                    # redirect to the quiz transcript that includes answers
                    return redirect(url_for('getTest', quizID=quizID))
                # Display quiz
                else:
                    return render_template("quiz.html", the_questions=questions)

    # redirect to login page if not logged in
    else:
        return redirect("/")

# create quiz page
@app.route("/createQuiz", methods=["GET", "POST"])
# Page where teacher is able to create quiz
def createQuiz():
    #  if logged in
    if 'access' in session:
        # get groups assigned to a given teacher
        studentGroups = db.getStudentGroups(session['id'])
        # if create quiz form is submitted
        msg = ""
        if request.method == "POST":
            # get form data
            data = request.form
            # Create quiz using form data
            db.createQuiz(data)
            # Assign teachers group to a group of created quiz
            session['group'] = data['group']
            msg = "Quiz created successfully"
        # display page with possible messages
        return render_template("createQuiz.html", the_message=msg, the_studentGroups=studentGroups)

    # redirect to login page if not logged in
    else:
        return redirect("/")

# student results page
@app.route("/studentresults", methods=["GET", "POST"])
def resultsPage():
    # get student results
    results = db.userResults(session['id'])
    # table column names
    columnNames = ["Quiz ID", "Quiz Date", "Quiz Name", "Final Score", "Transcript"]
    # if submited redirect to a transcript of selected quiz
    if request.method == 'POST':
        return redirect(url_for("transcript.html"))
    # not submited display table of student results
    return render_template("studentresults.html", the_results=results, the_columnNames=columnNames)

# transcript page for student and teacher
@app.route("/transcript/<string:quizID>", methods=["GET", "POST"])
@app.route("/transcript/<string:quizID>/<int:userID>", methods=["GET", "POST"])
def getTest(quizID, userID=None):
    id = quizID
    # get quiz questions corresponding to quiz ID
    questions = db.getQuizQuestions(id)
    # accessing as student
    if userID is None:
        # get quiz information
        info = db.quizUserInfo(session['id'], quizID)
        # get selected answers
        answers = db.getSelectedAnswers(id, session['id'])
    # accessing as teacher
    else:
        # get quiz information
        info = db.quizUserInfo(userID, quizID)
        # get selected answers
        answers = db.getSelectedAnswers(id, userID)
    # render page and display transcript
    return render_template("transcript.html", the_questions=questions, the_answers=answers, userInfo=info)


# Quiz results of students belonging to the teacher
@app.route("/teacherResults", methods=["GET", "POST"])
def teacherResults():
    # get student groups of the teacher
    studentGroups = db.getStudentGroups(session['id'])
    # if submited i.e group was selected
    if request.method == "POST":
        # get group
        group = request.form['studentGroup']
        # get all quizzes assigned to that group
        quizData = db.selectQuizes(group)

        columnNames = ["Quiz ID", "Quiz Name", "Quiz Date", "Quiz Participants"]
        # render page and display table with all the quizzes - click on the quiz to display participants
        return render_template("teacherResults.html", the_studentGroups=studentGroups, the_results=quizData,
                               the_columnNames=columnNames)
    # quiz not selected - display page with group select box
    return render_template("teacherResults.html", the_studentGroups=studentGroups)

# quiz participants viewed by the teacher
@app.route("/quizParticipants/<string:quizID>", methods=["GET", "POST"])
def quizParticipants(quizID):
    # get student participants of the quiz corresponding to quizID
    participants = db.getParticipants(quizID)
    columnNames = ["User ID", "Username", "Quiz Score", "Transcript"]
    # render page and display table with all quiz participants - click on the participant to see their quiz transcript
    return render_template("quizParticipants.html", the_results=participants, the_columnNames=columnNames, qID=quizID)

# group setting page
@app.route("/groupSettings", methods=["GET", "POST"])
def groupSettings():
    # get student groups belonging to teacher
    teachersGroups = db.getStudentGroups(session['id'])

    # if submitted
    if request.method == "POST":
        # if submitted form contains group name : then group was created
        if 'groupName' in request.form:
            # get entered group name
            groupName = request.form['groupName']
            # create group and assign it to the teacher
            db.createGroup(session['id'], groupName)
            # display confirmation message
            msg = "Group " + str(groupName) + " has been created"
            # get student groups belonging to teacher
            teachersGroups = db.getStudentGroups(session['id'])
            # render page with confirmation message and updated values
            return render_template("groupSettings.html", the_msg=msg,the_teachersGroups=teachersGroups)

        # if submitted form contains student group : then group was selected
        elif 'studentGroup' in request.form:
            # get selected group
            selectedGroup = request.form['studentGroup']
            # get student of selected group
            students = db.getGroupStudents(selectedGroup)
            # save selected group inside teachers session
            session['g'] = selectedGroup
            # render page with list of student belonging to the selected group
            return render_template("groupSettings.html",the_students=students, the_teachersGroups=teachersGroups)

        # if submitted form contains user information : then student authentication was updated
        elif 'userInformation' in request.form:
            # get student authentication information
            info = request.form
            # get group name from the session storage
            group = session['g']
            # update students authorisation info
            db.authenticateUsers(info, group)
            # get student list with updated authorisation information
            students = db.getGroupStudents(group)
            # render page with updated list of students
            return render_template("groupSettings.html", the_teachersGroups=teachersGroups,
                                   the_info=info, the_students=students)

    # not submitted: display last accessed tab
    else:
        return render_template("groupSettings.html", the_teachersGroups=teachersGroups)


# generate url token
u = secrets.token_urlsafe()

# function that sends notification/authentication requests email
def sendAuthenticationEmail(id, username, name, surname, emailAddress, group):
    # get previously generated url token
    global u
    # initialise email sender and recipients
    email = Message('Student account requires authentication', sender='mathsquizgenerator@gmail.com',
                    recipients=['mathsquizgenerator@gmail.com'])
    # generate second part of url token
    part2 = secrets.token_hex(16)
    # join two token parts
    link = u + part2
    # email body : last line generates an authentication link by joining host, generated token and id of created account
    email.body = "This notification is generated automatically. \r\n\n" \
                 "A new account has been created and requests authorisation to join group: " + str(group) + ".\r\n\n" \
                 "Registration data: \r\n" \
                "Name: " + str(name) + "\r\n" \
                "Surname: " + str(surname) + "\r\n" \
                "Group: " + str(group) + "\r\n" \
                "Email: " + str(emailAddress) + "\r\n\n" \
                 "The account can be authenticated manually inside of the quiz application or" \
                " by clicking on the following link:  http://127.0.0.1:5000/" + str(link) + "/" + str(id)

    # send email
    with mail.connect() as connector:
        connector.send(email)

# authentication link/ page, initialise url type
# if link is accessed authenticate student with id contained inside url
@app.route("/" + u + "<string(length=32):key>/<int:id>")
def authenticate(key, id):

    # authenticate student record
    with DBcm.UseDatabase(connection) as cursor:
        SQL = "update student set authenticated = 1 where userID = '%s'" % id
        cursor.execute(SQL)

    # return confirmation message
    return "Account has been authenticated"

# Page containing overall progress of the student i.e chart
@app.route("/studentProgress/<string:studentID>", methods=["GET", "POST"])
def studentProgress(studentID):
    # get student info and all results corresponding to studentID
    results = db.userResults(studentID)
    # initialise empty lists and variables that will contain the data necessary to draw the chart
    names = []
    scores = []
    movingAverage = []
    currentAverage = 0
    # Process and separate scores and quiz names, calculate moving average points
    for index, i in enumerate(results):
        names.append((i[2]))
        scores.append(float(i[3]))
        currentAverage += float(i[3])
        movingAverage.append(currentAverage / (index + 1))
        # if student completed at least one quiz. ie if results are present
    if len(scores) > 0:
        # calculate overall score average
        overallAverage = round(sum(scores) / len(scores), 2)
        # get name and surname of the student
        name = db.getStudentName(studentID)
        # render page with student info and chart representing the progress of the student
        return render_template("studentProgress.html", the_names=names, the_scores=scores,
                        the_movingAverage=movingAverage, the_average=overallAverage,the_name = name)
        # No quizzes completed: return page with a message
    else:
        return render_template("studentProgress.html")

# set debug mode to true


if __name__ == '__main__':
    app.run(debug=True)
