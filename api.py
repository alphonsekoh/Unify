from typing import List, TypeVar
from mysql import connector
import mysql.connector
from Credentials import constants
from flask import request, flash, redirect, url_for, jsonify


MySQLConnection = TypeVar("MySQLConnection")

# Connection String for Database
conn = mysql.connector.connect(host=constants.HOST,
                               database=constants.DATABASE,
                               user=constants.USER,
                               password=constants.PASSWORD
                               )


def init_connection_sql():
    '''
    Initialise connection for MySQL
    '''
    return mysql.connector.connect(host=constants.HOST,
                                   database=constants.DATABASE,
                                   user=constants.USER,
                                   password=constants.PASSWORD
                                   )


def dashboard_salary(connection_string) -> List:
    '''
    Query to get top 10 salary from the University courses

    Args:
        connection_string (object): The database location mysql connector
    Returns:
            list: a list of tuples representing the queried payload   
    '''

    payload = []
    query = '''
SELECT courseName, avgGradPay 
FROM unify_db.Courses
ORDER BY avgGradPay DESC
LIMIT 10;
    '''
    cur = connection_string.cursor()
    cur.execute(query)
    cursor = cur.fetchall()
    for row in cursor:
        # print(f"{row}"
        payload.append(row)
    return payload


def dashboard_95percentile_POLY(connection_string) -> List:
    '''
    Query to get top 95 percentile grades of Polytechnic students applying for University courses

    Args:
        connection_string (object): The database location mysql connector
    Returns:
            list: a list of tuples representing the queried payload   
    '''

    payload = []
    query = '''
SELECT GP.Poly90thPerc, C.CourseName
FROM unify_db.GradeProfile GP
    INNER JOIN unify_db.Courses C
    ON C.CourseID = GP.CourseID
ORDER BY GP.Poly90thPerc DESC
LIMIT 20;
    '''
    cur = connection_string.cursor()
    cur.execute(query)
    cursor = cur.fetchall()
    for row in cursor:
        # print(f"{row}")
        payload.append(row)

    return payload


def admin_viewAll(connection_string) -> List:
    '''
    Query to get all course details from all universities for admins

    Args:
        connection_string (object): The database location mysql connector
    Returns:
            list: a list of tuples representing the queried payload   
    '''
    cur = connection_string.cursor()
    cur.execute('''
    SELECT C.CourseID,C.UniName,C.CourseName,
    G.Poly10thPerc,G.Poly90thPerc,G.Alevel10thPerc,G.Alevel90thPerc,
    intake,C.AvgGradPay 
    FROM unify_db.Courses C
    LEFT JOIN unify_db.GradeProfile G 
    ON C.CourseID = G.CourseID''')
    data = cur.fetchall()
    cur.close()
    connection_string.close()
    return data


def course_query(connection_string) -> List:
    '''
    Query to get all course details from all universities for users

    Args:
        connection_string (object): The database location mysql connector
    Returns:
            list: a list of tuples representing the queried payload   
    '''
    cur = connection_string.cursor()
    # Select all courses for courses card
    cur.execute("""
                    SELECT C.CourseName, C.CourseDesc, C.CourseURL, IFNULL(NULLIF(CAST(C.AvgGradPay AS char), "0"), "N/A") as AvgGradPay, U.UniImage, F.FacultyName, C.UniName
                    FROM unify_db.Courses C
                     INNER JOIN unify_db.University U
                     ON C.UniName = U.UniName
                     INNER JOIN unify_db.Faculty F
                     ON C.FacultyID = F.FacultyID;""")
    coursesinfo = cur.fetchall()
    # Select the category for dropdown
    cur.execute("""SELECT CategoryName
                    FROM unify_db.Category;""")
    categoryinfo = cur.fetchall()
    # Select the uniname for check box
    cur.execute("""SELECT UniName
                    FROM unify_db.University; """)
    uniinfo = cur.fetchall()

    if request.method == 'POST':
        UniList = request.form.getlist('uniFilter')
        category = request.form.get('category')
        FROMsalary = request.form.get('fromSalary')
        TOsalary = request.form.get('toSalary')
        if TOsalary < FROMsalary:
            flash('To Salary cannot be more than From Salary!')
            redirect(url_for('courses'))
        UNI_list = str(tuple([key for key in UniList])).replace(',)', ')')
        print(UNI_list)
        print(category)
        query = """
        SELECT C.CourseName, C.CourseDesc, C.CourseURL, IFNULL(NULLIF(CAST(C.AvgGradPay AS char), "0"), "N/A") as AvgGradPay, U.UniImage, F.FacultyName, C.UniName 
        FROM unify_db.Courses C, unify_db.University U, unify_db.Faculty F,  unify_db.Category Ca, unify_db.FacultyCategory FC
        WHERE C.UniName = U.UniName
        AND C.FacultyID = F.FacultyID
        AND F.FacultyID = FC.FacultyID
        AND Ca.CategoryID = FC.CategoryID
        AND Ca.CategoryName = %s
        AND C.AvgGradPay >= %s
        AND C.AvgGradPay <= %s
        AND C.UniName IN {UNI_list};""".format(UNI_list=UNI_list)
        cur.execute(query, (category, FROMsalary, TOsalary))
        coursesinfo = cur.fetchall()
    cur.close()
    connection_string.close()
    return coursesinfo, categoryinfo, uniinfo


def editcourse_query(connection_string) -> List:
    '''
    Query to editing course

    Args:
        connection_string (object): The database location mysql connector
    Returns:
        list: a list of tuples representing the queried payload   
    '''
    cur = connection_string.cursor()
    if request.method == 'POST':
        CourseID = request.form.get('CourseId')
        print(CourseID)
        query = """SELECT  C.CourseName, C.CourseDesc, C.CourseURL, C.AvgGradPay, C.CourseID
        FROM unify_db.Courses C
        WHERE C.CourseID = %s """
        cur.execute(query, (CourseID,))
        Editcoursesinfo = cur.fetchone()
        print(Editcoursesinfo)
    cur.close()
    connection_string.close()
    return Editcoursesinfo


def univeristy_query(connection_string: MySQLConnection) -> List:
    '''
    Query to get all the universities

    Args:
        connection_string (MySQLConnection): The database location mysql connector
    Returns:
        uniFilter (list): a list of tuples representing the queried payload   
    '''
    cur = connection_string.cursor()
    query = cur.execute("""SELECT U.UniName 
                        FROM unify_db.University U
                        ORDER BY U.UniName; """)
    cur.execute(query)
    uniFilter = cur.fetchall()
    cur.close()
    connection_string.close()
    return uniFilter


def categorise_uni(connection_string, getUniCat) -> List:
    '''
    Query to get all the categories according to the selected university

    Args:
        connection_string (object): The database location mysql connector
        getUniCat: get the selected university
    Returns:
            list: a list of tuples representing the queried payload 
    '''

    cur = connection_string.cursor()
    # The database will use the specified type and value of getUniCat when executing the query,
    # offering protection from Python SQL injection.
    cur.execute("""
                    SELECT DISTINCT Ca.CategoryName
                    FROM unify_db.Category Ca, unify_db.FacultyCategory FC, unify_db.Faculty F, unify_db.Courses C
                    WHERE Ca.CategoryID = FC.CategoryID
                    AND FC.FacultyID = F.FacultyID
                    AND C.FacultyID = F.FacultyID
                    AND C.UniName = %s
                    ORDER BY Ca.CategoryName
                    ;""", (getUniCat, ))
    category = cur.fetchall()
    categoryArray = []
    for row in category:
        categoryObj = {
            'id': row[0],
            'name': row[0]
        }
        categoryArray.append(categoryObj)
    cur.close()
    return jsonify({'categoryList': categoryArray})


def query_intake(connection_string) -> List:
    '''
    Query the total intake and faculty of the universities
    Args:
        connection_string (object): The database location mysql connector
    Returns:
        list: list of tuples representing the queried payload
    '''
    payload = []
    query = """
    SELECT  IFNULL(NULLIF(CAST(sum(C.Intake) AS char), "0"), "N/A") as Intake , F.FacultyName, C.UniName
    FROM unify_db.Courses C
        INNER JOIN unify_db.Faculty F
        ON C.FacultyID = F.FacultyID
    GROUP BY F.FacultyName ;
    """
    cur = connection_string.cursor()
    cur.execute(query)
    cursor = cur.fetchall()
    for row in cursor:
        payload.append(row)
    return payload


def all_data_count(connecttion_string) -> List:
    payload = []
    cur = connecttion_string.cursor()
    query = """ SELECT COUNT(*) FROM unify_db.Category;
    """
    cur.execute(query)
    cat = cur.fetchall()
    query = """SELECT COUNT(*) FROM unify_db.Courses"""
    cur.execute(query)
    course = cur.fetchall()
    query = """SELECT COUNT(*) FROM unify_db.Faculty"""
    cur.execute(query)
    fac = cur.fetchall()
    query = """SELECT COUNT(*) FROM unify_db.FacultyCategory"""
    cur.execute(query)
    faccat = cur.fetchall()
    query = """SELECT COUNT(*) FROM unify_db.GradeProfile"""
    cur.execute(query)
    grade = cur.fetchall()
    query = """SELECT COUNT(*) FROM unify_db.University"""
    cur.execute(query)
    uni = cur.fetchall()
    payload = cat + course + fac + faccat + grade + uni
    return payload


def sum_intake(connection_str):
    cur = connection_str.cursor()
    query = '''
    SELECT SUM(Intake) 
    FROM unify_db.Courses
    WHERE Intake >= 0;  
    '''
    cur.execute(query)
    intake = cur.fetchall()
    return intake[0][0]


def total_course(conn_str):
    cur = conn_str.cursor()
    query = '''
    SELECT COUNT(*)
    FROM unify_db.Courses'''
    cur.execute(query)
    courses = cur.fetchall()
    return courses


def total_uni(conn_str):
    cur = conn_str.cursor()
    query = '''
    SELECT COUNT(*)
    FROM unify_db.University'''
    cur.execute(query)
    uni = cur.fetchall()
    return uni


if __name__ == "__main__":
    # API testing
    # print(type(dashboard_salary(conn)))
    # print(dashboard_95percentile_POLY(conn))
    # print(admin_viewAll(conn))
    # print(course_query(conn))
    # print(editcourse_query(conn))
    # print(categorise_uni(conn))
    # print(type(conn))
    print(query_intake(conn))
    # print(all_data_count(conn))
    # print(sum_intake(conn))
    # print(total_course(conn))
    # print(total_uni(conn))
    pass
