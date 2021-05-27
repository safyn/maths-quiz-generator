import DBcm

from questions import generateQuestions
from datetime import datetime
from datetime import timedelta

connection = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "root",
    "database": "quiz",
}


def createQuiz(data):
    # The function creates quiz record inside of the database and generates quiz questions

    # insert quiz/ crate form quiz values into the database
    with DBcm.UseDatabase(connection) as mycursor:
        SQL = """INSERT into quiz (groupName,quizDate,startTime,endTime,quadraticQuestion,simultaneousQuestion,termsOfQuestion,quizName)
             VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"""

        # execute query
        mycursor.execute(SQL, (
            data["group"], data["quizDate"], data["startTime"], data["endTime"], data["quadratic"],
            data["simultaneous"],
            data["termof"], str(data["quizName"])))

        # get id of the last inserted row
        id = mycursor.lastrowid

    # create list with quiz question numbers
    qList = []
    qList.append(int(data["quadratic"]))
    qList.append(int(data["simultaneous"]))
    qList.append(int(data["termof"]))

    # use question numbers to generate quiz questions
    quizQuestions = generateQuestions(qList)
    # insert generated questions into the database
    questionsToDatabase(quizQuestions, id)


def questionsToDatabase(questions, quizID):
    # Insert generated questions into the database

    # List that holds insert query for each question
    questionList = []

    # create insert query for each question, also escape any special characters inside the query
    for i, mydict in enumerate(questions):

        columns = "quizID, " + "questionNumber," + ', '.join(str(x) for x in mydict.keys())
        values = '"' + str(quizID) + '",' + '"' + str(i) + '"' + ', ' + ','.join(
            '"' + str(x) + '"' for x in mydict.values())
        s = "INSERT INTO %s ( %s ) VALUES ( %s );" % ('question', columns, values)
        questionList.append(s.translate(str.maketrans({"-": r"\-",
                                            "]": r"\]",
                                            "\\": r"\\",
                                            "^": r"\^",
                                            "$": r"\$",
                                            "*": r"\*",
                                            ".": r"\.",
                                            "/": r"/"})))

    # insert each question inside the database
    with DBcm.UseDatabase(connection) as mycursor:
        for i in questionList:
            mycursor.execute(i)


def getQuizQuestions(quizID):
    # The function gets the quiz questions from the database. The quiz questions correspond to the quizID
    # get questions query
    SQL = "select * from question where quizID = %s" % quizID

    # empty list that will store each question in form of python dictionary
    qlist = []
    # get questions from the database
    with DBcm.UseDatabase(connection) as mycursor:
        mycursor.execute(SQL)
        data = mycursor.fetchall()

    # insert each section of the question into the python disctionary
    for i in data:
        q = {
            "quizID": i[0],
            "questionNumber": i[1],
            "question": i[2],
            "equation": i[3],
            "solution": i[4],
            "a": i[5],
            "b": i[6],
            "c": i[7],
            "d": i[8],
            "step": i[9]
        }
        # add question dictionary to the list
        qlist.append(q)
    # return list of questions
    return qlist


def checkQuizAvailability(group, date):
    # This functions checks if there is a quiz available to be taken

    t = datetime.now().strftime("%H:%M:%S")
    # get current time and and one hour to it. This is due to the database time setting
    # databaseTime = (datetime.now() + deltatime(hours=1)).strftime("%H:%M:%S")
    # check if there is a quiz that matches: student gorup, data,starting and ending time
    with DBcm.UseDatabase(connection) as mycursor:

        SQL = "select quizID from quiz where groupName = '%s' and DATE(quizDate) = '%s' and  " \
              "'%s' >= startTime and '%s' <= endTime" % (group, date, t, t)

        mycursor.execute(SQL)
        data = mycursor.fetchall()

    # if no data received - quiz is not available
    if len(data) == 0:
        return "No quiz available"
    # quiz is available = get quiz id
    elif data is not None:
        id = data[-1]
    # return none in case of error
    else:
        return None
    # return id of the available quiz
    return id


def getSelectedAnswers(quizID, userID):
    # This function gets the answers selected by the student from the database

    # get answers corresponding to quizID and userID
    with DBcm.UseDatabase(connection) as mycursor:
        SQL = "select selectedAnswer from result where quizID = '%s' and userID = '%s'" % (quizID, userID)
        mycursor.execute(SQL)
        data = mycursor.fetchall()

    # return list of answers and convert from tuple list to normal list
    return listTuplesToList(data)


def answersToDatabase(answers, quizID, userID, questions):
    # This function inserts the quiz answers selected by the student into the database
    # The function also corrects each question by checking if selected answer matches the actual answer
    # list that will store query for each answer
    answerList= []
    # correct each question
    for i, mydict in enumerate(answers):
        # if actual answer matches the selected answer: mark as correct
        if questions[i].get('solution') == answers[mydict]:
            isCorrect = 1
        # answers do not match: mark as incorrect
        else:
            isCorrect = 0

        # table columns
        columns = "quizID,userID,questionNumber,selectedAnswer,isCorrect"
        # query values
        values = '"' + str(quizID) + '",' + '"' + str(userID) + '",' + '"' + str(i + 1) + '",'  '"' + \
                 answers[mydict] + '",' + '"' + str(isCorrect) + '"'

        # insert statement
        sql = "INSERT INTO %s ( %s ) VALUES ( %s );" % ('result', columns, values)
        # escape special characters inside of the query and append the query to the answerList
        answerList.append(sql.translate(str.maketrans({"-": r"\-",
                                              "]": r"\]",
                                              "\\": r"\\",
                                              "^": r"\^",
                                              "$": r"\$",
                                              "*": r"\*",
                                              ".": r"\.",
                                              "/": r"/"})))

    # insert result of each complete question into the database
    with DBcm.UseDatabase(connection) as mycursor:
        for i in answerList:
            mycursor.execute(i)


def isCompleted(quizID, userID):
    # This Function checks if the quiz was already completed by the student

    # check if result table contain records corresponding to quizID and userID
    with DBcm.UseDatabase(connection) as mycursor:
        SQL = "select * from result where quizID = '%s' and userID = '%s'" % (quizID, userID)
        mycursor.execute(SQL)
        data = mycursor.fetchall()

    # no results found ie. quiz not completed: return false
    if len(data) == 0:
        return False
    # results were found i.e quiz was completed: return true
    else:
        return True


def getStudentGroups(teacherID=None):
    # this function select student groups from the database. Depending if the teacherID is provided function
    # returns student groups belonging to the teacher or all existing student groups

    # db connection
    with DBcm.UseDatabase(connection) as mycursor:
        # if teacherID is provided, get student groups corresponding to the teacherID
        if teacherID is not None:
            SQL = "select groupName from teachergroups where teacherID = '%s'" % teacherID
            mycursor.execute(SQL)
            studentGroups = mycursor.fetchall()
            # if no groups assigned to the teacherID return false
            if studentGroups is None:
                return False
        # tacherID not provided: get all student groups
        else:
            SQL = "select groupName from teachinggroups"
            mycursor.execute(SQL)
            studentGroups = mycursor.fetchall()

    # return list of groups converted from tuple list to normal list
    return listTuplesToList(studentGroups)


def listTuplesToList(listTuples):
    # This function coverts tuple list to a normal list. The data received from the database is in form of the tuple
    # list and cannot be modified

    # normal list
    resultList = []
    # copy list of tuples to normal list
    for tuple in listTuples:
        for record in tuple:
            resultList.append(record)

    # return new list
    return resultList


def selectQuizes(group):
    # This function selects quizID,quizName and quizDate of all the quizzes assigned to specified student group
    with DBcm.UseDatabase(connection) as mycursor:
        SQL = "select quizID,quizName,quizDate from quiz where groupName = '%s'" % group
        mycursor.execute(SQL)
        quizes = mycursor.fetchall()

    # return quiz information
    return quizes


def getParticipants(quizID):
    # This function selects info about given quiz participants. It includes studentID, student name and quiz result
    with DBcm.UseDatabase(connection) as mycursor:
        SQL = "select result.userID,student.username , cast(avg(isCorrect)*100 as decimal(6,2)) from result,student " \
              "where result.quizID = '%s' and student.userID = result.userID group by userID" % quizID

        mycursor.execute(SQL)
        participants = mycursor.fetchall()
    # return participants info
    return participants


def createGroup(teacherID, groupName):
    # This function creates and assigns a new group to the teacher
    with DBcm.UseDatabase(connection) as mycursor:
        # create a new group
        SQL = "insert into teachinggroups values('%s')" % groupName
        mycursor.execute(SQL)
        #assign the group to the teacher
        SQL = "insert into teachergroups values('%s','%s')" % (teacherID, groupName)
        mycursor.execute(SQL)


def quizUserInfo(userID, quizID):
    with DBcm.UseDatabase(connection) as mycursor:
        SQL = "select quiz.quizName, quiz.quizDate, student.username, cast(avg(isCorrect)*100 as decimal(6,2)) from " \
              "quiz,student,result " \
              "where result.userID = '%s' and result.quizID = '%s' and quiz.quizID = result.quizID " \
              "and student.userID = result.userID group by result.userID" % (userID, quizID)

        mycursor.execute(SQL)
        userInfo = mycursor.fetchall()

        return listTuplesToList(userInfo)

def getGroupStudents(group):
    with DBcm.UseDatabase(connection) as mycursor:
        SQL = "select name, surname, authenticated,userID from student where student.userGroup='%s'" % group

        mycursor.execute(SQL)
        userInfo = mycursor.fetchall()

        return userInfo


def authenticateUsers(userIDs, group):
    users = userIDs.getlist('userInformation')
    with DBcm.UseDatabase(connection) as mycursor:
        SQL = "update student set authenticated = 0 where userGroup = '%s'" % group
        mycursor.execute(SQL)
        for user in users:
            SQL = "update student set authenticated = 1 where userID ='%s'" % user
            mycursor.execute(SQL)


def userResults(student):

    with DBcm.UseDatabase(connection) as mycursor:
        SQL =  "select quiz.quizID,quizDate,quizName, cast(avg(isCorrect)*100 as decimal(6,2))" \
               " from result,quiz where result.quizID = quiz.quizID and  userID = '%s' group by quizID" % student
        mycursor.execute(SQL)

        data = mycursor.fetchall()

        return data

def getStudents(groupID):
    with DBcm.UseDatabase(connection) as mycursor:
        SQL = "select userID,name,surname from student where userGroup = '%s'" % groupID

        mycursor.execute(SQL)

        data = mycursor.fetchall()

        return data

def getStudentName(studentID):

    with DBcm.UseDatabase(connection) as mycursor:
        SQL = "select name,surname from student where userID = '%s'" % studentID

        mycursor.execute(SQL)
        data = mycursor.fetchall()

        return listTuplesToList(data)
