from flask import Flask, request, render_template
from flask import request as request
from sympy.printing import print_latex
import latex.jinja2 as l
import sympy
from random import randint
from sympy.printing import latex
from qu import quadratic, simultaneous, generateQuestions
import db

app = Flask(__name__)


@app.route("/")
def quiz():
    return render_template("home.html")


areQuestions = False
questions = ""


@app.route("/questions", methods=["GET", "POST"])
def questions():
    global questions
    global areQuestions
    if areQuestions == False:
        questions = quadratic()
        areQuestions = True

    errors = []

    data = request.form
    if request.method == "POST":
        solutions = data.get('solutions')
        # get url that the user has entered

        return render_template('questions.html', errors=errors, the_bob=data['answer'], the_equation=questions)

    else:

        questions = quadratic()
        return render_template('questions.html', the_equation=questions)


areQuestions = False
questions = []

@app.route("/results", methods=["GET", "POST"])
def results():
    global areQuestions
    global questions
    if areQuestions == False:
        questions = generateQuestions(db.getQuestionNumbers())
        areQuestions = True


    if request.method == "POST":
        data = request.form
        solutions = data.get('solutions')

        return render_template("quiz.html", the_questions=questions, the_data=data, the_solutions=solutions)

    else:

        return render_template("quiz.html", the_questions=questions)


@app.route("/createQuiz", methods=["GET", "POST"])
def createQuiz():
    message = ""
    data = request.form
    if request.method == "POST":
        message = "Quiz created"
        db.createQuiz(data)

    return render_template("createQuiz.html", the_message=message)


if __name__ == '__main__':
    app.run(debug=True)
