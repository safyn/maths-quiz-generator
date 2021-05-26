from random import randint
from sympy import Eq, symbols, solve, Mul, Add, sqrt, simplify, expand, factor
from sympy.printing import latex

# initialise used symbols
x, y = symbols(" x y ")


def quadratic():
    # function that generates the question and solutions based on quadratic equation

    # quadrati equation variables generated as random integers
    root1 = 1
    root2 = randint(-20, 20)
    root3 = randint(-20, 20)

    # Assign quadratioc equation
    equation = x ** 2 + root2 * x + root3
    # convert equation into latex format
    e = latex(equation)
    # solve equation
    solution = solve(equation)

    # answer variables
    a = latex(solve(equation))
    b = "\\left[ "
    c = "\\left[ "
    d = "\\left[ "

    # generate random solutions by multiplying correct solution by random numbers
    for root in solution:
        b += latex(Mul(root, randint(-3, -1))) + ", "

        c += latex(Mul(root, randint(2, 3))) + ", "

        d += latex(Mul(root, (1 / 2))) + ", "

    # remove last two special signs
    b = b[:-2]
    c = c[:-2]
    d = d[:-2]

    """
        question dictionary where:
        question: holds question description
        equation: holds question equation
        solution: holds correct answer to the questionList
        variables a to d: hold correct and incorrect answers
        step: generates and holds the step-by-step solution to the quadratic equation. The solution is
        is of latex format and is ready to be displayed
    """
    question = {
        "question": r"$$\text{Use the quadratic formula: }$$" + r"$$x = {-b \pm \sqrt{b^2-4ac} \over 2a}$$ " +
                    r"$$\text{to find the roots of the following equation: }$$",
        "equation": e,
        "solution": a,
        "a": a,
        "b": b + " \\right]",
        "c": c + " \\right]",
        "d": d + " \\right]",
        "step":
                r"\[ \displaylines{ " +
                r"\text{The coefficients from quadratic equation are:} a = 1, b=" + latex(root2) + ", c=" + latex(
            root3) + r" \hfil \\ \\ " +
                r"\text{After substitution of the coefficients the formula looks as follows: }" + r" x ={-( " + latex(
            root2) +
                ") \pm \sqrt{" + latex(root2) + "^2- 4(" + latex(root1) + ")(" + latex(root3) + ")} \over 2(" + latex(
            root1) + r")} \hfil \\ \\" +
                r"\text{ After multiplying the above we get: }" + r"x ={-(" + latex(root2) + ") \pm \sqrt{" +
                latex(root2 * root2) + "-" + latex(4 * root1 * root3) + "} \over" + latex(
            2 * root1) + r"} \hfil \\ \\" +
                r"\text{Thus: }" + " x ={" + latex(-root2) + " \pm" + latex(
            sqrt(root2 * root2 - 4 * root1 * root3)) + "\over" +
                latex(2 * root1) + r"} \hfil \\ \\" +
                r"\text{After simplification we receive the following values for x: } " + " x ={" +
                latex((-root2 - sqrt(root2 * root2 - 4 * root1 * root3)) / 2 * root1) + r"} \text{  or  } " +
                "x ={" + latex((-root2 + sqrt(root2 * root2 - 4 * root1 * root3)) / 2 * root1) + "}" +
                r"\hfil } \]"
    }

    # return question dictionary
    return question


def simultaneous():
    # function that generates the simultaneous equations question

    # variables used in equations
    x, y = symbols('x,y')

    # generation of first equation, making sure values of x and y are not zero
    # x variable generaton
    equation1x = randint(-10, 10)
    while equation1x == 0:
        equation1x = randint(-10,10)

    # y variable generation
    equation1y = randint(-10, 10)
    while equation1y == 0:
        equation1y = randint(-10, 10)

    # equation solution
    equation1sol = randint(1, 50)

    # generation of second equation
    # x variable generation, making sure variable is not zero, not equal to other x variable or that variables will
    # not cancel each other out.
    equation2x = 0
    while equation2x == 0 or equation2x == (equation1x * -1) or equation2x == equation1x: equation2x = randint(-10, 10)

    # y variable generation, making sure variable is not zero, not equal to other y variable or that variables will
    # not cancel each other out.
    equation2y = 0
    while equation2y == 0 or equation2y == (equation1y * -1) or equation2y == equation1y: equation2y = randint(-10, 10)

    # equation 2 solution
    equation2sol = randint(1, 50)

    # Assign the equations
    equation1 = Eq(equation1x * x + equation1y * y, equation1sol)
    equation2 = Eq(equation2x * x + equation2y * y, equation2sol)

    # generate solution
    result = solve(([equation1, equation2]), (x, y))

    # generate random solutions by adding or multiplying the correct solution by random integers
    b = {}
    c = {}
    d = {}
    for root in result:
        b[root] = Mul(result[root], randint(2, 4))
        c[root] = Add(result[root], randint(1, 10))
        d[root] = Add(result[root], randint(-10, -1))

    # Calculations necessary to generate step-by-step solution

    # change sign of the equation2 y variable
    if equation1y and equation2y < 0 or equation1y and equation2y > 0:
        equation2y *= -1

    # multiply both sides of the equations
    equation1afterMul = Eq(Mul(equation1.lhs, equation2y), Mul(equation1.rhs, equation2y))
    equation2afterMul = Eq(Mul(equation2.lhs, equation1y), Mul(equation2.rhs, equation1y))

    # Add equations
    xEquation = Eq(Add(equation1afterMul.lhs, equation2afterMul.lhs), Add(equation1afterMul.rhs, equation2afterMul.rhs))

    # solve new equation (after addition) for x
    xValue = solve(xEquation, x)[0]
    # substitute x value into original equation1
    yEquation = equation1.subs(x, xValue)
    # solve for y
    yValue = solve(yEquation, y)[0]

    """
        question dictionary where:
        question: holds question description
        equation: holds question equation
        solution: holds correct answer to the questionList
        variables a to d: hold correct and incorrect answers
        step: generates and holds the step-by-step solution to the simultaneous equation problem. The solution is
        is of latex format and is ready to be displayed
    """
    question = {
        "question": r"$$\text{Find the solution of the following system of equations: }$$",
        "equation": r"\begin{gather} " + latex(equation1) + r" \\ " + latex(equation2) + r" \end{gather}",
        "solution": latex(result),
        "a": latex(result),
        "b": latex(b),
        "c": latex(c),
        "d": latex(d),
        "step": r"\[\displaylines{  " +
                 r"\text{To solve the following system of equations we going to use the elimination method.} \hfil \\ \\ " +
                 r"\text{The first step is to eliminate one of the variables. Lets eliminate the variable y by} \hfil \\ \\" +
                 r"\text{multiplying both equations so that when added the variables y will produce 0. } \hfil \\ \\" +
                 latex(equation1) + " (" + latex(equation2y) + r") \hfil  \\" +
                 latex(equation2) + " (" + latex(equation1y) + r")  \hfil \\ \\  "
                 r"\text{After the multiplication we receive the following equations: } \hfil  \\ \\  " +
                 latex(Mul(equation1.lhs, equation2y)) + " = " + latex(
            Mul(equation1.rhs, equation2y)) + r" \hfil  \\ " +
                 latex(Mul(equation2.lhs, equation1y)) + " = " + latex(Mul(equation2.rhs, equation1y)) + r" \hfil \\ \\" +
                 r"\text{When added the equations produce: } \hfil  \\ \\  " +
                 latex(xEquation) + r" \hfil \\ " +
                 r"x = " + latex(xValue) + r" \hfil \\ \\"
                 r"\text{In order to find y, substitute x into one of the initial equations. } \hfil   \\  " +
                 r"\text{Lets use: }" + latex(equation1) + r"\hfil  \\ \\ " +
                 r"\text{After substitution we get: } \hfil \\ \\" + latex(yEquation) + r"\hfil  \\   " +
                 "y = " + latex(yValue) + r" \hfil  \\ \\   " +
                 r"\text{So, the solution is:} \hfil \\ \\" +
                 r"x = " + latex(xValue) + r", y = " + latex(yValue) + r"\hfil } \]"
    }

    return question


def termsof():
    # function that generates the question based on solving the equation in terms of y variable.

    # generate non zero variables for the equation
    topX = randint(-10, 15) * x
    while topX == 0:
        topX = randint(-10, 15) * x
    topY = randint(-10, 20) * y
    while topY == 0:
        topY = randint(-10, 20) * y
    botY = randint(-10, 10) * y
    while botY == 0:
        botY = randint(-10, 10) * y
    botNum = randint(-10, 10)
    while botNum == 0:
        botNum = randint(-10,10)

    # assign and seprate the vaiables into the top and bottom part of the equation
    top = topX + topY
    bot = botNum + botY


    # assign left side of the equation
    leftSide = top / bot

    # generate right side of the equation
    rightSide = randint(-10, 10) * x
    while rightSide == 0:
        rightSide = randint(-10, 10) *x

    # assign entire equation
    equation = Eq(leftSide, rightSide)

    # calculate equation in terms of y
    solution = solve(equation, y)
    # if solution is 0 , change one of the x variables as long as solution is not 0
    while solution == 0:
        topX = randint(-10, 15) * x

    # multiply both sides of equation by the divisor of the left side of the equation
    rightSideAfterMultiplication = expand(rightSide * bot)
    xy = rightSideAfterMultiplication.args[-1]

    # if x variable on left side is negative multiply by -1, so it can be added to both sides
    # ie. -2x = y  -->  0 = y + 2x
    if topX.subs(x, 1) <= -1:
        topX *= -1
    # variable is positive so change it to negative so it can be subtracted from both sides of equation
    # ie.  2x = y -->  0 = y -2x
    else:
        topX *= -1

    # substitute 1 into x and y of the xy variable to check if the variable is posibite
    xy1 = xy.subs(x, 1)
    xy2 = xy1.subs(y, 1)

    # if negative change to positive as if it is added to both sides
    if xy2 <= -1:
        xy *= -1
    # variable is positive so change to negative as if it is subtracted from both sides
    else:
        xy *= -1

    # factorise left side of the equation
    frac = simplify(top + topX + xy).args[-1]
    # simplify the equation
    n = simplify(top + topX + xy).args[0]
    # final check: if calculation is correct then left side is equal to y
    if n == y:
        # set multiplier to 1 for display purposes
        n = 1

    # answers
    b = []
    c = []
    d = []
    a = solution

    # generate incorrect answers by multiplying solution variables by random integers
    for i in solution:
        b.append(Mul(i, randint(-3, -1)))
        c.append(Mul(i, randint(2, 5)))
        d.append(Mul(i, 1 / 2))

    """
        question dictionary where:
        question: holds question description
        equation: holds question equation
        solution: holds correct answer to the questionList
        variables a to d: hold correct and incorrect answers
        step: generates and holds the step-by-step solution to the 'solve for y' problem. The solution is
        is of latex format and is ready to be displayed
    """
    ques = {
        "question": r"$$\text{Express and simplify the following equation in terms of $$y$$, where y }" + r"\ne" + r" 0$$",
        "equation": latex(equation),
        "solution": latex(solution),
        "a": latex(a),
        "b": latex(b),
        "c": latex(c),
        "d": latex(d),
        "step": r"$$\displaylines{ " +
                 r"\textrm{First lets multiply both sides of the equation by  } " + latex(bot) + r" \hfil   \\ \\ " +
                 latex(leftSide) + "(" + latex(bot) + ") = " + latex(rightSide) + r"(" + latex(
            bot) + r") \hfil \\ \\ " +
                 r"\textrm{We get:  } \hfil   \\  " +
                 latex(top) + r" = " + latex(rightSideAfterMultiplication) + r" \hfil\\ \\" +
                 r"\textrm{Now add }" + latex(
            topX) + r"\text{ to both sides of equation} \hfil \\  \\  " +
                 r"\textrm{Equation becomes: } \hfil  \\  " +
                 latex(top + topX) + r" = " + latex(rightSideAfterMultiplication + topX) + r"\hfil   \\" +
                 r"\textrm{Add }" + latex(xy) + r"\textrm{ to both sides of equation }\hfil   \\ \\ " +
                 r"\text{Equation becomes: }\hfil \\" +
                 latex(top + topX + xy) + " = " + latex(rightSideAfterMultiplication + topX + xy) + r" \hfil \\ \\"+
                 r"\textrm{Factorise left side of the equation } \hfil   \\ \\ " +
                 r"\text{We get: } \hfil \\" +
                 latex(simplify(top + topX + xy)) + " = " + latex(rightSideAfterMultiplication + topX + xy) +r"\hfil \\ \\"+
                 r"\textrm{Now isolate y by dividing both sides of the equation by } " +
                 latex(factor(n*frac)) + r" \hfil \\ \\ " +
                 r"\text{The answer is: } \hfil \\" +
                 latex(simplify((top + topX + xy) / factor(n*frac))) + " = " +
                 latex(simplify((rightSideAfterMultiplication + topX + xy) / (n*frac))) + r"\hfil } $$"
    }

    return ques


def generateQuestions(numberList):
    # this function generates the question from the number of questions selected during quiz generation

    # list that stores generated questions
    questionList = []

    # generate quadratic equation questions and append to question list
    for q in range(numberList[0]):
        a = quadratic()
        questionList.append(a)

    # generate simultaneous equation questions and append to question list
    for q in range(numberList[1]):
        b = simultaneous()
        questionList.append(b)

    # generate 'solve for y' questions and append to question list
    for q in range(numberList[2]):
        c = termsof()
        questionList.append(c)

    # return list of generated questions
    return questionList


