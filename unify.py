from flask import Flask, render_template, url_for, flash, redirect, request, jsonify
from mysql import connector
import mysql.connector
from Credentials import constants
import api

app = Flask(__name__)
# For pop up
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# index route


@app.route('/', methods=['GET'])
def index():
    conn = mysql.connector.connect(host=constants.HOST,
                                   port=constants.PORT,
                                   database=constants.DATABASE,
                                   user=constants.USER,
                                   password=constants.PASSWORD
                                   )
    cur = conn.cursor()
    query = cur.execute("""SELECT U.UniName
                 FROM unify_db.University U
                 ORDER BY U.UniName; """)
    cur.execute(query)
    uniinfo = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", uniinfo=uniinfo)


@app.route('/<getCat>')
def categoryByUniversity(getCat):
    conn = mysql.connector.connect(host=constants.HOST,
                                   port=constants.PORT,
                                   database=constants.DATABASE,
                                   user=constants.USER,
                                   password=constants.PASSWORD
                                   )
    cur = conn.cursor()
    # The database will use the specified type and value of getCat when executing the query,
    # offering protection from Python SQL injection.
    result = cur.execute("""SELECT DISTINCT Ca.CategoryName
                        FROM unify_db.Category Ca, unify_db.FacultyCategory FC, unify_db.Faculty F, unify_db.Courses C
                        WHERE Ca.CategoryID = FC.CategoryID
                        AND FC.FacultyID = F.FacultyID
                        AND C.FacultyID = F.FacultyID
                        AND C.UniName = %s
                        ORDER BY Ca.CategoryName
                        ;""", (getCat, ))
    category = cur.fetchall()
    categoryArray = []
    for row in category:
        categoryObj = {
            'id': row[0],
            'name': row[0]
        }
        categoryArray.append(categoryObj)
    return jsonify({'categoryList': categoryArray})

# dashboard routing


@app.route('/dashboard')
def dashboard():
    conn = mysql.connector.connect(host=constants.HOST,
                                   database=constants.DATABASE,
                                   user=constants.USER,
                                   password=constants.PASSWORD
                                   )
    # data parsing for top 10 salary in dashboard
    payload_salary = api.dashboard_salary(conn)
    salary_labels = [row[0] for row in payload_salary]
    salary_values = [row[1] for row in payload_salary]

    # data parsing for top 95 percentile for polytechnic applicants into university
    payload_polypercentile = api.dashboard_95percentile_POLY(conn)
    ppercentile_labels = [row[1] for row in payload_polypercentile]
    ppercentile_values = [row[0] for row in payload_polypercentile]
    return render_template('dashboard.html', labels=salary_labels, values=salary_values, ppercentile_labels=ppercentile_labels, ppercentile_values=ppercentile_values)

# courses route


@app.route('/courses', methods=['GET', 'POST'])
def courses():
    conn = mysql.connector.connect(host=constants.HOST,
                                   port=constants.PORT,
                                   database=constants.DATABASE,
                                   user=constants.USER,
                                   password=constants.PASSWORD
                                   )
    cur = conn.cursor()
    # Select all courses for courses card
    result = cur.execute("""SELECT C.CourseName, C.CourseDesc, C.CourseURL, IFNULL(NULLIF(CAST(C.AvgGradPay AS char), "0"), "N/A") as AvgGradPay, U.UniImage, F.FacultyName, C.UniName
                    FROM unify_db.Courses C, unify_db.University U, unify_db.Faculty F
                    WHERE C.UniName = U.UniName
                    AND C.FacultyID = F.FacultyID;""")
    coursesinfo = cur.fetchall()
    # Select the category for dropdown
    result = cur.execute("""SELECT CategoryName
                    FROM unify_db.Category; """)
    categoryinfo = cur.fetchall()
    # Select the uniname for check box
    result = cur.execute("""SELECT UniName
                    FROM unify_db.University; """)
    uniinfo = cur.fetchall()

    if request.method == 'POST':
        category = request.form.get('category')
        FROMsalary = request.form.get('fromSalary')
        TOsalary = request.form.get('toSalary')
        UniList = request.form.getlist('uniinfo')
        print(category, FROMsalary, TOsalary, UniList)
        category = request.form.get('category')
        FROMsalary = request.form.get('fromSalary')
        TOsalary = request.form.get('toSalary')
        if TOsalary < FROMsalary:
            flash('To Salary cannot be more than From Salary!')
            redirect(url_for('courses'))
        UNI_list = str(tuple([key for key in UniList])).replace(',)', ')')
        print(UNI_list)
        query = """SELECT C.CourseName, C.CourseDesc, C.CourseURL, IFNULL(NULLIF(CAST(C.AvgGradPay AS char), "0"), "N/A") as AvgGradPay, U.UniImage, F.FacultyName, C.UniName 
        FROM unify_db.Courses C, unify_db.University U, unify_db.Faculty F,  unify_db.Category Ca, unify_db.FacultyCategory FC
        WHERE C.UniName = U.UniName
        AND C.FacultyID = F.FacultyID
        AND F.FacultyID = FC.FacultyID
        AND Ca.CategoryID = FC.CategoryID
        AND Ca.CategoryName = %s
        AND C.AvgGradPay >= %s
        AND C.AvgGradPay <= %s
        AND C.UniName IN {UNI_list};""".format(UNI_list=UNI_list)
        result = cur.execute(query, (category, FROMsalary, TOsalary))
        coursesinfo = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('courses.html', coursesinfo=coursesinfo, categoryinfo=categoryinfo, uniinfo=uniinfo)

# admin route (create courses)


@app.route('/addcourses')
def addcourses():
    return render_template('addcourses.html')

# admin route (create courses)


@app.route('/editcourses', methods=['GET', 'POST'])
def editcourses():
    conn = mysql.connector.connect(host=constants.HOST,
                                   port=constants.PORT,
                                   database=constants.DATABASE,
                                   user=constants.USER,
                                   password=constants.PASSWORD
                                   )
    cur = conn.cursor()
    if request.method == 'POST':
        CourseID = request.form.get('CourseId')
        print(CourseID)
        query = """SELECT  C.CourseName, C.CourseDesc, C.CourseURL, C.AvgGradPay, C.CourseID
        FROM unify_db.Courses C
        WHERE C.CourseID = %s """
        result = cur.execute(query, (CourseID,))
        Editcoursesinfo = cur.fetchone()
        print(Editcoursesinfo)
    cur.close()
    conn.close()
    return render_template('editcourses.html', Editcoursesinfo=Editcoursesinfo)

# admin route


@app.route('/admin-only/login/')
def admin():
    return render_template('admin/admin.html')


@app.route('/adminDash')
def adminDash():
    return render_template('admin/adminDashBoard.html')


@app.route('/adminViewData')
def adminViewData():
    conn = mysql.connector.connect(host=constants.HOST,
                                   database=constants.DATABASE,
                                   user=constants.USER,
                                   password=constants.PASSWORD
                                   )
    cur = conn.cursor()
    cur.execute("""SELECT C.CourseID,C.UniName,C.CourseName,C.CourseDesc,
    G.Poly10thPerc,G.Poly90thPerc,G.Alevel10thPerc,G.Alevel90thPerc,
    intake,C.AvgGradPay 
    FROM unify_db.Courses C
    LEFT JOIN unify_db.GradeProfile G 
    ON C.CourseID = G.CourseID""")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin/adminViewData.html', data=data)


@app.route('/adminEditData/<Course_ID>', methods=['GET', 'POST'])
def adminEditData(Course_ID):
    if(request.method == 'GET'):
        print(Course_ID)
        conn = mysql.connector.connect(host=constants.HOST,
                                       database=constants.DATABASE,
                                       user=constants.USER,
                                       password=constants.PASSWORD
                                       )
        cur = conn.cursor()
        cur.execute("""SELECT C.CourseName,G.Poly10thPerc,G.Poly90thPerc,G.Alevel10thPerc,G.Alevel90thPerc,intake,C.AvgGradPay 
        FROM unify_db.Courses C, unify_db.GradeProfile G 
        WHERE C.CourseID = %s """, (Course_ID))
        dataToEdit = cur.fetchall()
        print(dataToEdit)
        cur.close()
        conn.close()
        return render_template('admin/adminEditData.html', dataToEdit=dataToEdit)
    # else:

# admin route
@app.route('/adminAddCourse', methods=['GET', 'POST'])
def adminAddCourse():
    conn = mysql.connector.connect(host=constants.HOST,
                                   port=constants.PORT,
                                   database=constants.DATABASE,
                                   user=constants.USER,
                                   password=constants.PASSWORD
                                   )
    cur = conn.cursor()
    cur.execute("SELECT UniName FROM unify_db.University")
    universities = cur.fetchall()
    if request.method == 'POST':
        university = request.form.get('university')
        courseName = request.form.get('course')
        CourseURL = request.form.get('course_url')
        CourseDesc = request.form.get('description')
        CourseID = request.form.get('courseID')
        poly10 = request.form.get('poly10')
        poly90 = request.form.get('poly90')
        Alevel10 = request.form.get('Alevel10')
        Alevel90 = request.form.get('Alevel90')
        intake = request.form.get('intake')
        avgpay = request.form.get('avgpay')
        print(courseName,CourseDesc,CourseID,CourseURL,avgpay,intake,university)
        # cur.execute("""INSERT INTO unify_db.Courses(CourseName,CourseDesc,CourseID,CourseURL,AvgGradPay,Intake,UniName)
        # VALUES(%s,%s,%s,%s,%s,%s,%s)""",(courseName,CourseDesc,CourseID,CourseURL,avgpay,intake,university))
        # conn.commit()
        # cur.execute("""INSERT INTO unify_db.GradeProfile(poly10thPerc,poly90thPerc,Alevel90thPerc,Alevel10thPerc,CourseID)
        # VALUES(%s,%s,%s,%s,%s)""",(poly10,poly90,Alevel10,Alevel90,CourseID))
        conn.commit()
        cur.close()
        conn.close()
    return render_template('admin/adminAddCourse.html',universities = universities)




@app.route('/SuccessfulEdit', methods=['GET', 'POST'])
def SuccessfulEdit():
    conn = mysql.connector.connect(host=constants.HOST,
                                   port=constants.PORT,
                                   database=constants.DATABASE,
                                   user=constants.USER,
                                   password=constants.PASSWORD
                                   )
    cur = conn.cursor()
    if request.method == 'POST':
        CourseID = request.form.get('CourseId')
        CourseName = request.form.get('CourseName')
        CourseURL = request.form.get('CourseURL')
        CourseSalary = request.form.get('AvgGradPay')
        CourseDesc = request.form.get('CourseDesc')
        cur.execute("""  UPDATE unify_db.Courses C
                    SET C.CourseName = %s, C.CourseDesc = %s, C.CourseURL = %s, C.AvgGradPay = %s
                    WHERE C.CourseID = %s""",
                    (CourseName, CourseDesc, CourseURL, CourseSalary, CourseID,))
        conn.commit()
    cur.close()
    conn.close()

    return render_template('admin/SuccessfulEdit.html')


# admin route
@app.route('/deletecourses', methods=['GET', 'POST'])
def deletecourses():
    conn = mysql.connector.connect(host=constants.HOST,
                                   port=constants.PORT,
                                   database=constants.DATABASE,
                                   user=constants.USER,
                                   password=constants.PASSWORD
                                   )
    cur = conn.cursor()
    if request.method == 'POST':
        CourseID = request.form.get('CourseId')
        print(CourseID)
        cur.execute("""DELETE FROM unify_db.Courses C 
                        WHERE C.CourseID =%s """,
                    (CourseID,))
        conn.commit()
    cur.close()
    conn.close()
    return render_template('deletecourses.html')


if __name__ == "__main__":
    # Error will be displayed on web page
    app.run(debug=True)
