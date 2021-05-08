import DBcm
import mysql.connector
from qu import generateQuestions, calculateResults
from datetime import datetime
from datetime import timedelta


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


def createQuiz(data):
    id = ""

    with DBcm.UseDatabase(connection) as mycursor:
        SQL = """INSERT into quiz (groupName,quizDate,startTime,endTime,quadraticQuestion,simultaneousQuestion,termsOfQuestion,quizName)
             VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"""

        mycursor.execute(SQL, (
            data["group"], data["quizDate"], data["startTime"], data["endTime"], data["quadratic"],
            data["simultaneous"],
            data["termof"], str(data["quizName"])))

        id = mycursor.lastrowid

    qList = []
    qList.append(int(data["quadratic"]))
    qList.append(int(data["simultaneous"]))
    qList.append(int(data["termof"]))

    quizQuestions = generateQuestions(qList)
    questionsToDatabase(quizQuestions, id)


def questionsToDatabase(questions, quizID):
    sql = ""
    l = []
    s = ""
    for i, mydict in enumerate(questions):
        placeholders = ', '.join(['%s'] * len(mydict))
        columns = "quizID, " + "questionNumber," + ', '.join(str(x) for x in mydict.keys())
        values = '"' + str(quizID) + '",' + '"' + str(i) + '"' + ', ' + ','.join(
            '"' + str(x) + '"' for x in mydict.values())
        sql += "INSERT INTO %s ( %s ) VALUES ( %s );" % ('question', columns, values)
        s = "INSERT INTO %s ( %s ) VALUES ( %s );" % ('question', columns, values)
        l.append(s.translate(str.maketrans({"-": r"\-",
                                            "]": r"\]",
                                            "\\": r"\\",
                                            "^": r"\^",
                                            "$": r"\$",
                                            "*": r"\*",
                                            ".": r"\.",
                                            "/": r"/"})))
        s = ""

    with DBcm.UseDatabase(connection) as mycursor:
        for i in l:
            mycursor.execute(i)


def getQuizQuestions(quizID):
    SQL = "select * from question where quizID = %s" % quizID
    qlist = []
    with DBcm.UseDatabase(connection) as mycursor:
        mycursor.execute(SQL)
        data = mycursor.fetchall()

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
        qlist.append(q)
    return qlist


def checkQuiz(group, date):
    t = datetime.now().strftime("%H:%M:%S")
    # databaseTime = (datetime.now() + deltatime(hours=1)).strftime("%H:%M:%S")
    with DBcm.UseDatabase(connection) as mycursor:

        SQL = "select quizID from quiz where groupName = '%s' and DATE(quizDate) = '%s' and  " \
              "'%s' >= startTime and '%s' <= endTime" % (group, date, t, t)

        mycursor.execute(SQL)
        data = mycursor.fetchall()

    if len(data) == 0:
        return "No quiz available"
    elif data is not None:
        id = data[-1]
    else:
        return None

    return id


def getStudentResults(id):
    with DBcm.UseDatabase(connection) as mycursor:
        SQL = "select quizID,quizDate,username,result from results where userID = '%s'" % id
        mycursor.execute(SQL)
        data = mycursor.fetchall()

    return data


def getSelectedAnswers(quizID, userID):
    with DBcm.UseDatabase(connection) as mycursor:
        SQL = "select selectedAnswer from result where quizID = '%s' and userID = '%s'" % (quizID, userID)
        mycursor.execute(SQL)
        data = mycursor.fetchall()

    return listTuplesToList(data)


def answersToDatabase(answers, quizID, userID, questions):
    sql = ""
    l = []
    isCorrect = 0
    for i, mydict in enumerate(answers):
        if questions[i].get('solution') == answers[mydict]:
            isCorrect = 1
        else:
            isCorrect = 0

        columns = "quizID,userID,questionNumber,selectedAnswer,isCorrect"
        values = '"' + str(quizID) + '",' + '"' + str(userID) + '",' + '"' + str(i + 1) + '",'  '"' + \
                 answers[mydict] + '",' + '"' + str(isCorrect) + '"'

        sql = "INSERT INTO %s ( %s ) VALUES ( %s );" % ('result', columns, values)
        l.append(sql.translate(str.maketrans({"-": r"\-",
                                              "]": r"\]",
                                              "\\": r"\\",
                                              "^": r"\^",
                                              "$": r"\$",
                                              "*": r"\*",
                                              ".": r"\.",
                                              "/": r"/"})))
        sql = ""

    with DBcm.UseDatabase(connection) as mycursor:
        for i in l:
            mycursor.execute(i)


def isCompleted(quizID, userID):
    with DBcm.UseDatabase(connection) as mycursor:
        SQL = "select * from result where quizID = '%s' and userID = '%s'" % (quizID, userID)
        mycursor.execute(SQL)
        data = mycursor.fetchall()

    if len(data) is 0:
        return False
    else:
        return True


def getStudentGroups(teacherID=None):
    with DBcm.UseDatabase(connection) as mycursor:
        if teacherID is not None:
            SQL = "select groupName from teacherGroups where teacherID = '%s'" % teacherID
            mycursor.execute(SQL)
            studentGroups = mycursor.fetchall()
            if studentGroups is None:
                return False
        else:
            SQL = "select groupName from teachingGroups"
            mycursor.execute(SQL)
            studentGroups = mycursor.fetchall()

    return listTuplesToList(studentGroups)


def listTuplesToList(listTuples):
    resultList = []

    for tuple in listTuples:
        for record in tuple:
            resultList.append(record)

    return resultList


def selectQuizes(group):
    with DBcm.UseDatabase(connection) as mycursor:
        SQL = "select quizID,quizName,quizDate from quiz where groupName = '%s'" % group
        mycursor.execute(SQL)
        quizes = mycursor.fetchall()

    return quizes


def getParticipants(quizID):
    with DBcm.UseDatabase(connection) as mycursor:
        SQL = "select result.userID,user.username , cast(avg(isCorrect)*100 as decimal(6,2)) from result,user " \
              "where result.quizID = '%s' and user.userID = result.userID group by userID" % quizID

        mycursor.execute(SQL)
        participants = mycursor.fetchall()

    return participants


def createGroup(teacherID, groupName):
    with DBcm.UseDatabase(connection) as mycursor:
        SQL = "insert into teachingGroups values('%s')" % groupName
        mycursor.execute(SQL)
        SQL = "insert into teacherGroups values('%s','%s')" % (teacherID, groupName)
        mycursor.execute(SQL)


def quizUserInfo(userID, quizID):
    with DBcm.UseDatabase(connection) as mycursor:
        SQL = "select quiz.quizName, quiz.quizDate, user.username, cast(avg(isCorrect)*100 as decimal(6,2)) from " \
              "quiz,user,result" \
              " where result.userID = '%s' and result.quizID = '%s' and user.userID = result.userID group by result.userID" % (userID, quizID)

        mycursor.execute(SQL)
        userInfo = mycursor.fetchall()

        return listTuplesToList(userInfo)

def changeTeacherGroups(groups,teacherID):
    newgroups = groups.getlist('group')
    with DBcm.UseDatabase(connection) as mycursor:
        SQL = "delete from teacherGroups where teacherID = '%s'" % teacherID
        mycursor.execute(SQL)
        for group in newgroups:
            SQL = "insert into teacherGroups values('%s','%s')" % (teacherID,group)
            mycursor.execute(SQL)


