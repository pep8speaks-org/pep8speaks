# -*- coding: utf-8 -*-
import os
import sys
from flask import Flask, render_template, request
from flask_session import Session
import requests


app = Flask(__name__)
sess = Session()


@app.route("/", methods=['GET', 'POST'])
def main():
    if request.method == "POST":
        form = request.form.to_dict()
        if True:
            reg_dict = project_register(request)
            return render_template('index.html' , flag=reg_dict["flag"] , msg=reg_dict["msg"],msgcode=reg_dict["msgcode"])
        else:
            return render_template('index.html' , flag=reg_dict["flag"] , msg=reg_dict["msg"],msgcode=reg_dict["msgcode"])
    else:
        return render_template('index.html')


"""
# @app.route("/student-register", methods=['GET', 'POST'])
def student_register(request):
    flag = None
    global conn, cursor
    if "LOCAL_CHECK" not in os.environ:
        msg = "Database Connection cannot be set since you are running website locally"
        msgcode = 0
        return {"web": 'index.html' , "flag":"True", "msg":msg,"msgcode":msgcode}

    if request.method == "POST":
        form_dict = request.form.to_dict()
        query = r"INSERT INTO student (f_name,l_name,email_id,roll_no,git_handle) values ('%s','%s','%s','%s','%s') " % (
            form_dict["fname"], form_dict["lname"], form_dict["emailid"], form_dict["rollno"], form_dict["githubhandle"])

        try:
            cursor.execute(query)
            conn.commit()
            mail_subject = "Successfully registered for Kharagpur Winter of Code!"
            #mail_body = 'Hello ' + form_dict["fname"] + '<br>You have been successfully registered for the <b>Kharagpur Winter of Code</b>. ' + \
            #            'Check out the <a href="http://kwoc.kossiitkgp.in/resources">Resources for KWoC</a> now.'

            mail_body = mail_body.format(form_dict['fname'])
            mail_check = send_mail(
                mail_subject, mail_body, form_dict["emailid"])
            if not mail_check:
                slack_notification("Unable to send mail to the following student :\n{}".format(
                    form_dict))
            flag="True"
            msg=form_dict["fname"] + ", You have been successfully registered. Please check your email for instructions."
            msgcode=1
            return {"web": 'index.html' , "flag":flag, "msg":msg,"msgcode":msgcode}
        except psycopg2.IntegrityError:
            conn.rollback()
            error_msg = "{}\n\nForm : {}".format(
                traceback.format_exc(), form_dict)
            slack_notification(error_msg)
            flag="True"
            msg="Registration Failed ! User already registered"
            msgcode=0
            return {"web": 'index.html' , "flag":flag, "msg":msg,"msgcode":msgcode}
        except:
            conn.rollback()
            error_msg = "{}\n\nForm : {}".format(
                traceback.format_exc(), form_dict)
            slack_notification(error_msg)
            flag="True"
            msg="Registration Failed ! Please try again."
            msgcode=0
            return {"web": 'index.html' , "flag":flag, "msg":msg,"msgcode":msgcode}
"""

app.secret_key = os.environ["APP_SECRET_KEY"]
app.config['SESSION_TYPE'] = 'filesystem'

sess.init_app(app)
app.debug = True
# app.run()
