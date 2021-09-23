from flask import Flask , Blueprint, render_template, request, flash, jsonify , redirect , session , url_for
from flask_login import login_user, login_required, logout_user, current_user , UserMixin , LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy import tuple_
from sqlalchemy.sql import func

#import flask_whooshalchemy as fwa 
from flask_msearch import Search
from whoosh.analysis import StemmingAnalyzer

import json 
from os import path
import pickle , os



db = SQLAlchemy()
DB_NAME = "database.db"


app = Flask(__name__  , static_url_path='' )
app._static_folder = ''


app.app_context().push()
app.config['SECRET_KEY'] = 'SaifProjectAphorismsSecretKey' # unsafe
app.config['DEBUG'] = False #True for auto restarts and debug messages
# check the last line of this package too , if __main__ wala

'''
views = Blueprint('views', __name__)
auth = Blueprint('auth', __name__)

app.register_blueprint(views, url_prefix='/')
app.register_blueprint( auth, url_prefix='/')
'''

###

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}' #SQLAlchemy is ORM
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db.init_app(app)
db.app = app


class User(db.Model, UserMixin):
    #__tablename__ = 'user'
    #__searchable__ = ['name']
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    name = db.Column(db.String(150))
    notes = db.relationship('Note')

    user_views_note_counter = db.Column(db.Integer , default = 0 ) # note_view should have a caller to this 


class Note(db.Model):
    __tablename__ = 'note'
    __searchable__ = ['data']
    __analyzer__ = StemmingAnalyzer()

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(4000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) 

    note_viewed_counter  = db.Column(db.Integer , default = 0 ) # note_view should have a caller to this 
    
    # linked_notes_counter = db.column(db.Integer) # create_note_links should have a caller to this 
    # this linked_notes_counter is a bad idea because the count  of linked_notes is update both wasy , ie for both notes ,
    # hence we have to implemented this the same way as we did for the index_interlink.pkl 
    # use a simple fucntion to go over the index and create a new dictionary containg the length of the lst of th e oriinal dictionary key value pairts




# here we will need to define one more schema , where we store the links between notes 
# need to conisder a good sdata structure her 
# simply using a RDBMS may not be the best way to model a netwrok 
# we need to store (all notes linked to a particular note) for  all notes 
   
# although the python class refernce by foreign key is User ( capital U ) , 
# in SQL tables are fernced with lowercase , so in the kibrary this will get taken care of 
# using Uppercase is convention for python classes

if not path.exists('/' + DB_NAME):
    db.create_all(app=app)
    print('Created Database!')


#######



login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

###
'''
# flask-whooshalchemy3 code 
# https://github.com/blakev/Flask-WhooshAlchemy3

app.config['WHOOSH_INDEX_PATH'] = 'whoosh_store'
fwa.search_index (app = app , model = Note )
fwa.create_index (app = app , model = Note )
'''

###

app.config["MSEARCH_INDEX_NAME" ] = 'msearch'
app.config["MSEARCH_BACKEND" ] = 'whoosh'  # 'whoosh' or 'simple'
app.config["MSEARCH_ENABLE" ] = True

search = Search( db = db  , analyzer = StemmingAnalyzer()) 
        # alternatively use : stemming_analyzer(gaps= True) for a different mapping behaviour
        # analyzer =  NgramWordAnalyzer (minsize = 4 , maxsize=12 )


search.init_app(app)
search.create_index(Note)
#search.update_index(Note)




####################

def note_interlink_counter_generate_dict(index_interlinks):
    interlink_counter_store = dict()
    for key in index_interlinks.keys() :
        links_list_length = int(len(index_interlinks[key]))
        interlink_counter_store[key] = links_list_length
    return interlink_counter_store


def commit_index( index_interlinks ) :
    with open('interlink_index.pkl' , "wb" ) as f:
        pickle.dump( index_interlinks , f )

    interlink_counter_store = note_interlink_counter_generate_dict(index_interlinks = index_interlinks)
    with open('interlink_counts.pkl' , "wb" ) as f:
        pickle.dump( interlink_counter_store , f )


def initialize_index() :
    if os.path.isfile("interlink_index.pkl") :
        with open('interlink_index.pkl' , "rb" ) as f:
            index_interlinks = pickle.load(f)
        print('index was available , read from DIR')

    else :
        index_interlinks = dict()
        print('index was unavailable , new empty dictionary created , and commited to DIR')
        commit_index( index_interlinks )
    return index_interlinks

index_interlinks = initialize_index()



def add_to_index(primary_note_id , list_of_to_link_ids , index_interlinks ):
    for secondary_note_id in list_of_to_link_ids :
        secondary_note_id = int(secondary_note_id)
        append_index(index_point = primary_note_id   , append_data = secondary_note_id , index_interlinks = index_interlinks )
        append_index(index_point = secondary_note_id , append_data = primary_note_id   , index_interlinks = index_interlinks )
        print('   linking done betweem ' , primary_note_id , ' and ' , secondary_note_id )
    print('links attached for ' , primary_note_id)
    commit_index( index_interlinks )
    return 


def append_index(index_point, append_data , index_interlinks ):
    if index_point in index_interlinks.keys() :
        if isinstance(index_interlinks[index_point] , list ):
            index_interlinks[index_point].append(append_data)
    else :
            index_interlinks[index_point] = []
            index_interlinks[index_point].append(append_data)
            print('index list initialized for point ' , index_point )
    return 


###


def get_linked_notes(note_id):
    if not note_id in index_interlinks.keys() :
        index_interlinks[note_id] = []
        print('note_id :' , note_id , ' was NOT in interlink index , now initialized')

    linked_notes = index_interlinks[note_id]
    return linked_notes
    

def get_similiar_notes(note_id):
    similiar_notes =  Note.query.msearch(Note.query.get(note_id).data , or_=True , rank_order=True ).all()
    return similiar_notes


def search_text_in_notes(search_text):
    note_ids = Note.query.msearch(search_text , or_=True , rank_order=True ).all()
    return note_ids

###




#####################


@app.route('/')
def home():
    return render_template("index.html", user=current_user)

@app.route('/contact_us')
def contact_us():
    return render_template("contact_us.html", user=current_user)


@app.route('/comparison')
def comparison():
    return render_template("comparison.html", user=current_user)


@app.route('/use_case')
def use_case():
    return render_template("use_case.html", user=current_user)

####

@app.route('/create_note/', methods=['GET', 'POST'])
@login_required
def create_note():
    if request.method == 'GET' :
        return render_template("add_note.html", user=current_user , Note = Note , note_id_to_link = None )
    
    elif request.method == 'POST':
        session['note']  = request.form.get('note')
        session['note_id_to_link'] = None
        print(session['note'] )
        print(session['note_id_to_link'] )

        if len(session['note']) < 1:
            flash('Please type a Note before trying to submit', category='error')
        else:
            return redirect("/create_note_link")



@app.route('/create_note/<int:note_id_to_link>', methods=['GET', 'POST'])
@login_required
def create_note_by_link(note_id_to_link):
    if request.method == 'GET' :
        return render_template("add_note.html", user=current_user , Note = Note , note_id_to_link = note_id_to_link )
    
    elif request.method == 'POST':
        session['note']  = request.form.get('note')
        session['note_id_to_link'] = int(note_id_to_link)
        print(session['note'] )
        print(session['note_id_to_link'] )

        if len(session['note']) < 1:
            flash('Please type a Note before trying to submit', category='error')
        else:
            return redirect("/create_note_link")



@app.route('/create_note_link', methods=['GET', 'POST'])
@login_required
def create_note_link_searched( ):# input title and content here
    search_text = session['note']
    note_id_to_link = session['note_id_to_link']
    print(search_text)
    print(note_id_to_link)

    if request.method == 'GET' :
        search_results = search_text_in_notes( search_text = search_text)
        print(search_results)
        return render_template("add_note_linking.html", user=current_user , search_results = search_results , User = User , Note = Note )
        
    elif request.method == 'POST':
        notes_to_link = list(request.form.getlist("checkbox"))
        print('Before1')
        print(notes_to_link)
        print('After1')
        if note_id_to_link is not None :
            notes_to_link.append(int(note_id_to_link))
        print('Before2')
        print(notes_to_link)
        print('After2')
        
        
        if len(notes_to_link) != 0 :
            new_note = Note(data=session['note'] , user_id=current_user.id )# , ids = ids ) 
            db.session.add(new_note)
            db.session.commit()
            #search.update_index(Note)

            add_to_index(primary_note_id = new_note.id , list_of_to_link_ids = notes_to_link , index_interlinks = index_interlinks )
                
            flash('Note added and linked!', category='success')
            print('Succesfully linked note > TEXT:' , session['note'] )
            return redirect("/")


        else :
            search_results = search_text_in_notes( search_text = search_text)
            print(search_results)

            if search_results :
                print('No Note was linked , resending same page with Flash')
                flash("Please select Atleast one Note to link" , category='error')
                return render_template("add_note_linking.html", user=current_user , search_results = search_results , User = User , Note = Note )
            
            else :
                flash('Note added and linked!', category='success')
                flash("Since there is no search result , A linkless note was be created ." , category='error')
                flash("If Authoring about new topics , find a related note in Explore and then create a linked note from there ." , category='alert')
                flash("Linkless notes risk being unread by the network users , try linking to them in other notes you author going forward ." , category='alert')
                
                new_note = Note(data=session['note'] , user_id=current_user.id )# , ids = ids ) 
                db.session.add(new_note)
                db.session.commit()
                #search.update_index(Note)
    
                add_to_index(primary_note_id = new_note.id , list_of_to_link_ids = notes_to_link , index_interlinks = index_interlinks )
                    
                print('Note created but without inital link , This is not good .' , session['note'] )
                return redirect("/")


###


@app.route('/my_notes')
@login_required
def my_notes():
    mynotes = current_user.notes#Note.query.get(note_id)
    mynotes = list(mynotes)
    print(mynotes)
    #print(mynotes[1].data)
    return render_template("my_notes.html", user=current_user , mynotes = mynotes , User = User)


@app.route('/search_note', methods=['GET' , 'POST'] )
@login_required
def search_note():
    if request.method == 'POST':
        print('Search Explore Request received : ')
        search_text = request.form.get('search_input')
        print(search_text)

        similiar_notes = search_text_in_notes( search_text = search_text)
        return render_template("search_note.html", user=current_user , User = User ,
                                search_results = similiar_notes ,  search_bar_value = search_text )

    elif request.method == 'GET' :
        return render_template("search_note.html", user=current_user , User = User , 
                                    search_bar_value = "I want to explore .." )


@app.route('/note_view/<int:note_id>')
@login_required
def note_view(note_id):
    note = Note.query.get(note_id)
    author = User.query.get(note.user_id)
    print(author)
    print(note)
    
    linked_notes   = Note.query.filter( Note.id.in_(get_linked_notes(note_id))).all()
    #print('BEFORE : Linked Notes for ID :' , note_id)
    #print(linked_notes)
    #print('AFTER')

    similiar_notes = get_similiar_notes(note_id)
    #print('BEFORE : similiar Notes for ID :' , note_id)
    #print(similiar_notes)
    #print('AFTER')

    print('BEFORE : Unsplashify process query for text  : ' , str( note.data) )
    unsplash_query_text = unsplash_querify_text( str(note.data) )
    print('AFTER :  Unsplashify process fucntion result : ' , unsplash_query_text )
    

    #update_usage_stats
    print('this_user_view_counter : ', current_user.user_views_note_counter)
    current_user.user_views_note_counter = current_user.user_views_note_counter + 1
    print('this_user_view_counter : ', current_user.user_views_note_counter)

    print('note.note_viewed_counter : ', note.note_viewed_counter)    
    note.note_viewed_counter = note.note_viewed_counter + 1
    print('note.note_viewed_counter : ', note.note_viewed_counter)
        
    db.session.commit()
    


    return render_template("note_view.html", user=current_user , 
                            author= author.name , note = note , 
                            User = User ,
                            linked_notes = linked_notes , similiar_notes = similiar_notes , unsplash_query_text = unsplash_query_text )



import re

def unsplash_querify_text(text):
    result = ''
    '''
    for character in text:
        if character.isalnum():
            result += character
    '''
    result = re.sub(r"[^a-zA-Z0-9]+", ' ', text )
    result = result.replace(" ", ",")
    #print(result)
    return result


@app.route('/delete-note', methods=['POST'])
@login_required
def delete_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})


###

@app.route('/test_msearch', methods=['GET', 'POST'])
@login_required
def test_search():# input title and content here
    #search_term = request.args.get('query')
    search_term = 'hello world'
    #search_results = Note.query.first()
    search_results = Note.query.msearch(search_term,limit =10, or_=True , rank_order=True ).all()
    print('Hello from the backend')
    print(repr(search_results))
    print('Hello after')
    return render_template("home.html", user=current_user)


@app.route('/test_print_index')
@login_required
def test_print_index_interlinks(index_interlinks = index_interlinks):
    print(repr(index_interlinks))
    return redirect(url_for('home'))


#######################


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        #print(email,'',password)
        user = User.query.filter_by(email=email).first()
        print(user)
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                #return redirect(url_for('app.home'))
                return redirect(url_for('home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Account-email does not exist , Please Sign-Up', category='error')
    return render_template("login.html", user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    #flash('Testing error flash', category='error')
    if request.method == 'POST':
        email = request.form.get('email')
        name = str(request.form.get('name')).lower()
        password = request.form.get('password')
        password2 = request.form.get('password2')
        print(name,'',email,'',password,'',password2)


        user = User.query.filter_by(email=email).first()
        print(user)

        username = User.query.filter_by(name=name).first()
        print(username)

        if user:
            flash('Email already exists.', category='error')
        elif username:
            flash('Username taken : change letters , add numbers.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user, remember=True)
            flash('Account created!', category='success')#
            return redirect(url_for('home'))  # important for redirecting post event
    return render_template("sign_up.html", user=current_user)


@app.route('/user_onboard', methods=['GET', 'POST'])
def user_onboard():
    pass
    # return render_template("user-onboarding.html", user=current_user)



if __name__ == '__main__':
    app.run(debug=False)
