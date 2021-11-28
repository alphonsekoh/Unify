
from typing import List
from flask import Flask
from flask import request, flash, redirect, url_for, jsonify
from flask_pymongo import PyMongo
from pymongo import cursor
from pymongo.message import query
from Credentials import constants
import pymongo

app = Flask(__name__)

# connecting to mongo
app.config["MONGO_URI"] = constants.MONGO_CONNECT
mongo = PyMongo(app)
# getting the db and disable the SSL certificate for UNIX developers
mongo.init_app(app, tlsAllowInvalidCertificates=True)

# connecting to mongo
app.config["MONGO_URI"] = constants.MONGO_CONNECT
mongo = PyMongo(app)
# getting the db and disable the SSL certificate for UNIX developers
db = mongo.init_app(app, tlsAllowInvalidCertificates=True)


def fetch_Courses() -> object:
    '''
    Queries univeristy courses dataset from database
    Args:
        None
    Returns:
        cursor (object): queried dataset object address
    '''
    courses = mongo.db.courses
    cursor = courses.find()
    return cursor


def fetchById(CourseID):
    course = mongo.db.courses.find_one({"CourseID": CourseID})
    # print(course)
    return course


def fetch_Uninames():
    '''
    Query to get all the universities

    Args:
        connection_string (MySQLConnection): The database location mysql connector
    Returns:
        uniFilter (list): a list of tuples representing the queried payload
    '''
    univeristy = mongo.db.courses
    uniFilter = univeristy.distinct("University.UniName")
    return uniFilter


def fetch_CategoryNames_Raw():
    category = mongo.db.category
    courses = mongo.db.courses
    cursor = category.distinct("CategoryName")
    return cursor


def fetch_CategoryNames(getUniCat):
    '''
    Query to get all the categories according to the selected university

    Args:
        getUniCat: get the selected university
    Returns:
        list: a list of tuples representing the queried payload
    '''
    courses = mongo.db.courses
    category = mongo.db.category
    category_name = category.distinct("CategoryName")
    join_collection = courses.aggregate([{"$lookup": 
    {"from": "category", "localField": "Faculty.CategoryID", "foreignField": "CategoryID", "as": "Category_Info"}}, 
    {"$match": {"Category_Info": {"$elemMatch": {"University.UniName": {"$in": getUniCat}}}}}])
    return join_collection


def filter_Course(UniList, category_name, FROMsalary, TOsalary):
    if TOsalary < FROMsalary:
        flash('To Salary cannot be more than From Salary!')
        redirect(url_for('courses'))
    category = mongo.db.category
    courses = mongo.db.courses
    join_collection = courses.aggregate([{"$lookup": {"from": "category", "localField": "Faculty.CategoryID", 
    "foreignField": "CategoryID", "as": "Category_Info"}},
    {"$match": {"Category_Info": {"$elemMatch": {"CategoryName": category_name}}, 
    "AvgGradPay": {"$gte": FROMsalary, "$lte": TOsalary}, "University.UniName": {"$in": UniList}}}])
    return join_collection


def insert_Course():
    insertInfo = {"CourseID":request.form.get('courseID'),
    "University":{'UniName':request.form.get('university')},
    "CourseName":request.form.get('course'),"CourseDesc":request.form.get('description'),
        "GradeProfile":{
        'Poly10thPerc':request.form.get('poly10'),
        'Poly90thPerc':request.form.get('poly90'),
        'Alevel10thPerc':request.form.get('Alevel10'),
        'Alevel90thPerc':request.form.get('Alevel90')}
        ,
        "Intake":request.form.get('intake'),
        "AvgGradPay":request.form.get('avgpay'),
         }

    mongo.db.courses.insert(insertInfo)


def delete_Course(CourseID):
    mongo.db.courses.delete_one({"CourseID": CourseID})


def edit_Course(CourseID, CourseName, CourseURL, AvgGradPay, CourseDesc):
    print(CourseID)
    print(CourseName)
    mongo.db.courses.update({"CourseID": CourseID}, {"$set": {
                            "CourseName": CourseName, "CourseURL": CourseURL, "AvgGradPay": AvgGradPay, "CourseDesc": CourseDesc}})


def top_salary() -> List:
    courses = mongo.db.courses
    query = {}
    projection = {"CourseName": 1, "AvgGradPay": 1, "_id": 0}
    cur = courses.find(query, projection).sort([("AvgGradPay", -1)]).limit(10)
    return list(cur)


def top_grade() -> List:
    courses = mongo.db.courses
    query = {"GradeProfile.Poly90thPerc": {"$lte": "4.00"}}
    projection = {"CourseName": 1, "GradeProfile": {
        "Poly90thPerc": 1}, "_id": 0}
    cur = courses.find(query, projection).sort(
        [("GradeProfile.Poly90thPerc", -1)]).limit(20)
    return list(cur)


def count_docs() -> int:
    courses = mongo.db.courses
    category = mongo.db.category
    cur_courses = courses.count_documents({})
    cur_category = category.count_documents({})
    return cur_courses + cur_category


def total_courses() -> int:
    courses = mongo.db.courses
    cur = courses.count_documents({})
    return cur


def total_intake() -> int:
    courses = mongo.db.courses
    query = {"Intake": {"$gte": 0}}
    projection = {"Intake": 1, "_id": 0}
    cur = courses.find(query, projection)
    intake = list(cur)
    intake = sum([row['Intake'] for row in intake])
    return intake


def uni_total() -> int:
    courses = mongo.db.courses
    agg_res = courses.aggregate(
        [{
            "$group":
            {"_id": "$University.UniAbb"}
        }]
    )
    total_uni = len(list(agg_res))
    return total_uni


def dashboard_table() -> list:
    courses = mongo.db.courses
    agg_res_intake = courses.aggregate(
        [{
            "$group":
            {"_id": "$Faculty.FacultyName",
             "Intake": {"$sum": "$Intake"},
             "Uni": {"$first": "$University.UniName"}
             }
        }]
    )

    return list(agg_res_intake)


if __name__ == "__main__":
    # print statement here to test out whether API is working and what object is returning
    # just type python api_mongo.py in the cmd.
    # print(fetch_Courses())
    # filter_Course(UniList, category_name, FROMsalary, TOsalary)
    # print(top_salary())
    # print(top_grade())
    # print(count_docs())
    # print(total_intake())
    # print(uni_total())
    print(dashboard_table())
    pass
