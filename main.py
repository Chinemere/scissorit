from utils import db
from flask import Flask, redirect, url_for, flash, render_template, request, jsonify
import requests

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from random import randint


from flask import Flask, redirect, url_for, flash, render_template, request, jsonify
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from models import User, Url
from application_functions import analytics, linkhistory, generate_qr_code
from decouple import config
import re

basedir= os.path.abspath(os.path.dirname(__file__))


def create_app():
    app= Flask(__name__)
    # app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///' + os.path.join(basedir, 'database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = config("DATABASE_URL")

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = True
    app.config["SECRET_KEY"] = config('SECRET_KEY', 'secrete_keys')
    # postgres://scissorit:ggpNlia06yeRNmg13aZONp6ZFs95aFCG@dpg-cilc0llph6eg6k8e1lf0-a/scissorit_database
    #postgres://scissorit:ggpNlia06yeRNmg13aZONp6ZFs95aFCG@dpg-cilc0llph6eg6k8e1lf0-a.oregon-postgres.render.com/scissorit_database
    db.init_app(app)

    migrate = Migrate(app, db)
    login_manager = LoginManager(app)

    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # this is needed in order for database session calls (e.g. db.session.commit)
    with app.app_context():
      try:
          db.create_all()
      except Exception as exception:
          print("got the following exception when attempting db.create_all() in __init__.py: " + str(exception))
      finally:
          print("db.create_all() in __init__.py was successfull - no exceptions were raised")

    return app


app = create_app()


# if __name__=='__main__':
    
#     app.run(debug=True, port=8000)



@app.route('/')
def index():
     return render_template('index.html')

@app.route('/signup', methods=('GET', 'POST'))
def signup():
    from models import User
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        userExist= User.query.filter_by(username=username).first()
        if userExist:
            flash('Username is already taken', "error")
            return redirect(url_for("signup"))

        emailExist= User.query.filter_by(email=email).first()
        if emailExist:
            flash(' email already exist', "error")

            return redirect(url_for("shortner"))
        passwordharsh = generate_password_hash(password)
        new_user = User(username=username, email=email, passwordHash=passwordharsh ) 
        new_user.save()
        login_user(new_user)
        
        return redirect(url_for('shortner'))
    return render_template('signup.html')

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        old_user = User.query.filter_by(username=username).first()
        if old_user and check_password_hash(old_user.passwordHash, password):
            login_user(old_user)
        else:
            flash("Incorrect username or password ")
            return redirect(url_for('login'))
        return redirect(url_for('shortner'))
    return render_template('login.html')


@login_required
@app.route('/shortner', methods=('GET', 'POST') )
def shortner():
    if request.method == 'POST':
        url_source = request.form.get('url_source')
        if not url_source.startswith('http://') and not url_source.startswith('https://'):
            url_source =  "http://" + url_source
        userIdentity = current_user.username
        username = User.query.filter_by(username=userIdentity).first()
        url_record = Url.query.filter_by(url_source=url_source).first()
        
        #Check if the url is already in the database
        if url_record:
            # display  link analysis
            link_analysis = analytics(url_record.scissored_url)
            # the output of the scissored_url has a pattern like this - "scissorit/ujpoj...   i.e there is always scissorit/ before the name short strings"
            # so use regex to sort out the scissored_url in other to get only the string after the forward slash, i.e to get only "ujpoj" out of "scissorit/ujpoj"
            pattern = r"/([a-zA-Z0-9]+)"
            text = url_record.scissored_url
            pattern_match = re.findall(pattern, text)
            convert_patter_match_to_string= str(pattern_match[0])
            short_url=convert_patter_match_to_string
            if os.path.exists(f"static/images/{short_url}.png"):
                return render_template('shortner.html', new_url=url_record, link_analysis=link_analysis, short_url=short_url )
            # create a qr code
            qr_code_image = generate_qr_code(url_record.scissored_url)
            images_folder = os.path.join(app.root_path, 'static', 'images')
            qr_code_image.save(os.path.join(images_folder, short_url+'.png'))
            return render_template('shortner.html', new_url=url_record, link_analysis=link_analysis, short_url=short_url )
        
        short_url = Url.create_short_url(randint(4, 6))
        short_url_http = "http://127.0.0.1:8000/scissorit/"+ short_url
        
        new_url = Url(url_source=url_source, scissored_url=short_url_http, user=username.id)
        new_url.save()
        link_analysis = analytics(short_url_http)
        qr_code_image = generate_qr_code(url_source)
        images_folder = os.path.join(app.root_path, 'static', 'images')
        qr_code_image.save(os.path.join(images_folder, short_url+'.png'))
        # base_url= "http://127.0.0.1:8000/"
        return render_template('shortner.html', new_url=new_url, link_analysis=link_analysis, short_url=short_url)

    return render_template('shortner.html')


@app.route('/customlink', methods=('GET', 'POST') )
def customLink():
    if request.method == 'POST':
        url_source = request.form.get('custom_url_source')
        custom_name = request.form.get('custom_name')
        if not url_source.startswith('http://') and not url_source.startswith('https://'):
                url_source =  "http://" + url_source
        url_record = Url.query.filter_by(url_source=url_source).first()
        userIdentity = current_user.username
        username = User.query.filter_by(username=userIdentity).first()
        if url_record:
             # display  link analysis
            link_analysis = analytics(url_record.scissored_url)
            # the output of the scissored_url has a pattern like this - "scissorit/ujpoj...   i.e there is always scissorit/ before the name short strings"
            # so use regex to sort out the scissored_url in other to get only the string after the forward slash, i.e to get only "ujpoj" out of "scissorit/ujpoj"
            pattern = r"/([a-zA-Z0-9]+)"
            text = url_record.scissored_url
            pattern_match = re.findall(pattern, text)
            convert_patter_match_to_string= str(pattern_match[0])
            short_url=convert_patter_match_to_string
            if os.path.exists(f"static/images/{short_url}.png"):
                return render_template('shortner.html', new_url=url_record, link_analysis=link_analysis, short_url=short_url )
            # create a qr code
            qr_code_image = generate_qr_code(url_record.scissored_url)
            images_folder = os.path.join(app.root_path, 'static', 'images')
            qr_code_image.save(os.path.join(images_folder, short_url+'.png'))
            return render_template('shortner.html', new_url=url_record, link_analysis=link_analysis, short_url=short_url)
        

        short_url = Url.create_custom_url(custom_name)
        short_url_http = "scissorit/"+ short_url
        customise= True
        new_url = Url(url_source=url_source, scissored_url=short_url_http, user=username.id)
        new_url.save()
        link_analysis = analytics(short_url_http)
        qr_code_image = generate_qr_code(short_url_http)
        images_folder = os.path.join(app.root_path, 'static', 'images')
        qr_code_image.save(os.path.join(images_folder, short_url+'.png'))

        return render_template('shortner.html', new_url=new_url, customise=customise, link_analysis=link_analysis, short_url=short_url)


@app.route('/redirect/<path:new_url>')
def redirectUrl(new_url):
    url_record = Url.query.filter_by(scissored_url=new_url).first()
    if url_record:
        
        return redirect(url_record.url_source)
    else:
        return {"error": "url not found"}
    

@app.route('/logout/', methods=('GET', 'POST'))
def logout():
    logout = logout_user()
    flash('you have successfully logged out. Login to Create More Links', 'info')
    return render_template('login.html')

@app.route('/linkhistories')
def linkhistories():
    linklist = linkhistory()
    return render_template('linkhistory.html', linklist=linklist)










if __name__=='__main__':
    
    app.run(debug=True, port=8000)
