from email import message
from flask import Flask, render_template, request, url_for, session, redirect
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
import json
# import uuid
from flask_mail import Mail, Message
from datetime import datetime
import os
import math


with open('config.json', 'r') as c:
    params = json.load(c)["Params"]

local_server=True
app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD=  params['gmail-password']
)   #this is the form of gmail id mail send one mail come
mail = Mail(app)


if(local_server):                        # if our project run in local server
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']


db = SQLAlchemy(app)   # initializing


class contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)     # nullable false means doesnt blank 
    phone_num = db.Column(db.String(12), nullable=False)
    mes = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)

# model for post
class posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)     # nullable false means doesnt blank 
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=False)
    slug = db.Column(db.String(21), nullable=True)
    img_file = db.Column(db.String(12), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)


@app.route("/")          #We then use the route() decorator to tell Flask what URL should trigger our function.   
def home():
    Posts = posts.query.filter_by().all()
    last = math.ceil(len(Posts)/int(params['no_of_posts']))
    #[0: params['no_of_posts']]
    #posts = posts[]
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page= int(page)
    Posts = Posts[(page-1)*int(params['no_of_posts']): (page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]
    #Pagination Logic
    #First
    if (page==1):
        prev = "#"
        next = "/?page="+ str(page+1)
    elif(page==last):
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html', params=params, posts=Posts, prev=prev, next=next)

@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):     #compulsery 
    post = posts.query.filter_by(slug=post_slug).first()   #uniqly
    return render_template('post.html', params=params, post=post)

@app.route("/about")
def about():
    return render_template('about.html', params=params)


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():

    # if user already logedin
    if ('user' in session and session['user'] == params['admin_user']):
        post = posts.query.all()
        return render_template("dashboard.html", params=params, posts=post)

    if request.method=='POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username == params['admin_user'] and userpass == params['admin_password']):
            # set the session variable
            session['user'] = username
            post = posts.query.all()
            return render_template("dashboard.html", params=params, posts=post)

        # REDIRECT TO ADMIN PANEL
    return render_template('login.html', params=params)




@app.route("/edit/<string:sno>", methods=['POST', 'GET'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if sno=='0':
                post = posts(title=box_title, slug=slug, content=content, tagline=tline, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()
                # print("Successfully added...")
            else:                #sno not 0 then edit user data
                post = posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.tagline = tline
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/'+sno)
        post = posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, post=post, sno=sno)

@app.route("/uploader", methods = ['GET', 'POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):
        if (request.method == 'POST'):
            f= request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename) ))  
            # secure_filename is use to security purpose
            return "Uploaded successfully"


@app.route("/logout")
def logout():
    #session kill
    session.pop('user')
    return redirect('/dashboard')


@app.route("/delete/<string:sno>", methods=['POST', 'GET'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post = posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')


@app.route("/contact", methods=['POST', 'GET'])
def contact():
    if request.method=="POST":
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone_num')
        message = request.form.get('mes')
      
        entry = contacts(name=name,phone_num=phone, mes=message, date=datetime.now(), email=email)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients = [params['gmail-user']],
                          body = message + "\n" + phone + "\n" + email
                          )
    return render_template('contact.html', params=params)


# @app.route("/reset_password", methods=['POST', 'GET'])
# def reset_request():
#     if 'user' in session:
#         return redirect('/')

#     return render_template("reset_request.html", title="Reset Request", params=params)

if __name__ == "__main__":
    app.run(debug=True)


