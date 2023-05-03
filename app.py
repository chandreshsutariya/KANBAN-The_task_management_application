from flask import Flask, render_template, request, redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime,date
from matplotlib import pyplot as plt
from flask_restful import Api, Resource
import requests
import json
import matplotlib

matplotlib.use('Agg')

#START---USER-DEFINE FUNCTIONS---- FIND DIFFERENCE B|N DATE ENTERED AND TODAY'S DATE
def find_day_difference(d1):
    d1=datetime.strptime(d1, '%Y-%m-%d')
    d2 = datetime.today()
    de = d2 - d1
    return de.days
#END---USER-DEFINE FUNCTIONS---- FIND DIFFERENCE B|N DATE ENTERED AND TODAY'S DATE


#START---- REQUIRED objects
app = Flask(__name__)
db=SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI']= 'sqlite:///kanban.sqlite3'
api = Api(app)
#END---- REQUIRED objects


#START---- MODEL
class User(db.Model):
    user=db.Column(db.String(), primary_key=True)

class List(db.Model):
    l_user = db.Column(db.String(), db.ForeignKey('user.user'), primary_key=True)
    l_name=db.Column(db.String(), primary_key=True)
    l_description = db.Column(db.String())

class Card(db.Model):
    c_user = db.Column(db.String(),db.ForeignKey('user.user'), primary_key=True)
    c_list = db.Column(db.String(), db.ForeignKey('list.l_name'), primary_key=True)
    c_title = db.Column(db.String(), primary_key=True)
    c_content = db.Column(db.String())
    c_deadline = db.Column(db.String())
    c_doneornot = db.Column(db.String())
#END---- MODEL

class UserRc(Resource):
    def get(self, user_name):
        f_user=user_name
        if not User.query.get(f_user):
            return 'USER_EXIST_0:USER_NAME DOESN\'T EXIST.',230 #User_name does not exist.
        else:
            return 'USER_EXIST_1: USER NAME EXIST.',290 #user_name exist.

    def post(self, user_name):
        r_user_name=User.query.get(user_name)
        if r_user_name:
            return 'USER_ADD_0: USER_NAME IS ALREADY THERE.',230 #user_name is already there in DB.
        else:
            u=User(user=user_name)
            db.session.add(u)
            db.session.commit()
            return 'USER_ADD_1: USER_NAME IS SUCCESSFULLY ADDED.',290 #User_name added.

    def delete(self, user_name):
        r_user_name=User.query.get(user_name)
        if not r_user_name:
            return 'USER_DELETE_0: REQUEST USER_NAME IS NOT THERE IN DB.',230 #user_name is not there in DB.
        else:
            user=user_name

            cardss=Card.query.filter_by(c_user=user).all()
            for each in cardss:
                db.session.delete(each)
                db.session.commit()
            
            listss=List.query.filter_by(l_user=user).all()
            for each in listss:
                db.session.delete(each)
                db.session.commit()    

            u=User.query.get(user)
            db.session.delete(u)
            db.session.commit()

            return 'USER_DELETE_1: USER_NAME IS SUCCESSFULLY DELETED.',290 #user_name deleted.

api.add_resource(UserRc, '/api/user/<user_name>/')

class ListRc(Resource):
    def get(self, user_name):

        if not User.query.get(user_name):
            return {"LIST_GET_USER_0": "Request user does not exist."}, 230

        listss=List.query.filter_by(l_user=user_name).all()
        d={}
        for each in listss:
            d[each.l_name]={'l_user':f'{each.l_user}' ,'l_name':f'{each.l_name}' ,'l_description':f'{each.l_description}'}
        return d, 290
    
    def post(self, user_name):
        form=json.loads(request.data)
        f_l_name=form['l_name']

        if not User.query.get(user_name):
            return 'LIST_ADD_USER_0: Request user does not exist.', 230

        if ' ' in f_l_name:
            return 'LIST_TITLE_0: Please dont add space in list title.',232

        if List.query.filter_by(l_user=user_name, l_name=f_l_name).first():
            return 'LIST_ADD_list_0:LIST_TITLE ALREADY EXIST',231 #List already exists
        else:
            f_l_description=form['l_description']
            l=List(l_user=user_name,l_name=f_l_name,l_description=f_l_description)
            db.session.add(l)
            db.session.commit()
        return 'LIST_ADD_1: LIST HAS BEEN SUCCESSFULLY ADDED.',290 #list has been successfully created.

    def put(self, user_name, l_name):
        r_user=user_name
        r_list=l_name
        r_l=List.query.filter_by(l_user=r_user, l_name=r_list).first()

        listss = List.query.filter_by(l_user=user_name).all()
        lists=[]
        for each in listss:
            lists.append(each.l_name)


        form=json.loads(request.data)
        f_l_name=form['l_name']
        
        if not User.query.get(user_name):
            return 'LIST_EDIT_USER_0: Request user does not exist.', 230

        if r_list not in lists:
            return 'LIST_EDIT_LIST_0: Request list does not exist.', 231
        else:
            lists.remove(r_list)

        if ' ' in f_l_name:
            return 'LIST_TITLE_0: Please dont add space in list title.',233

        if f_l_name in lists:
            return 'LIST_EDIT_list_title_0: FORM LIST TITLE ALREADY EXIST.',232 #The list can not be updated, because the same name title exist in the same user's account.
        else:            
            f_l_description=form['l_description']
            r_l.l_name=f_l_name
            r_l.l_description=f_l_description
            db.session.commit()
            cardss=Card.query.filter_by(c_user=r_user, c_list=r_list).all()
            for each in cardss:
                each.c_list=f_l_name
                db.session.commit()
            return 'LIST_EDIT_1: LIST IS SUCCESSFULLY UPDATED.',290 #list has been successfully updated!


    def delete(self,user_name, l_name):
        r_user=user_name
        r_list=l_name
        l=List.query.filter_by(l_user=r_user, l_name=r_list).first()

        if not User.query.get(user_name):
            return 'LIST_DELETE_USER_0: Request user does not exist.', 230

        if not l:
            return 'LIST_DELETE_LIST_0: REQUEST LIST does exist.',231 #List is not there.
        
        c=Card.query.filter_by(c_user=r_user,c_list=r_list).all()
        for each in c:
            db.session.delete(each)
            db.session.commit()
               
        db.session.delete(l)
        db.session.commit()
        return 'LIST_DELETE_1: LIST IS SUCCESSFULLY DELETD.',290 #List deleted.    

    
api.add_resource(ListRc, '/api/list/<user_name>/<l_name>/', '/api/list/<user_name>/')


class CardRc(Resource):
    def get(self, user_name):

        u=User.query.get(user_name)
        if not u:
            return 'LIST_GET_USER_0: Request user does not exist.', 230

        cardss=Card.query.filter_by(c_user=user_name).all()
        c={}
        for each in cardss:
            c[f'{each.c_user}_{each.c_list}_{each.c_title}']={'c_user':f'{each.c_user}' ,'c_list':f'{each.c_list}' ,'c_title':f'{each.c_title}', 'c_content':f'{each.c_content}','c_deadline':f'{each.c_deadline}','c_doneornot':f'{each.c_doneornot}'}
        return c, 290
    
    def post(self, user_name, l_name):
        user=user_name
        list=l_name
        today=date.today()

        form = json.loads(request.data)
        f_c_title=form['c_title']

        if not User.query.get(user_name):
            return 'CARD_ADD_USER_0: Request user does not exist.', 230
        
        if not List.query.filter_by(l_user=user_name, l_name = list).first():
            return 'CARD_ADD_LIST_0:Request list does not exist.',231

        if Card.query.filter_by(c_user=user, c_list=list, c_title=f_c_title).first():
            return "CARD_ADD_0:CARD_TITLE ALREADY EXIST.", 232 #CARD_TITLE already there.

        f_c_content=form['c_content']
        f_c_deadline=form['c_deadline']

        if find_day_difference(f_c_deadline)>0:
            return "CARD_ADD_1: CARD_DATE IS BEFORE OF TODAY'S.", 233

        if 'c_doneornot' in form:
            f_c_doneornot=form['c_doneornot']
        else:
            f_c_doneornot="0"
        if f_c_doneornot==None:
            f_c_doneornot=0

        c=Card(c_user=user, c_list=list, c_title=f_c_title, c_content=f_c_content, c_deadline=f_c_deadline, c_doneornot=f_c_doneornot)
        db.session.add(c)
        db.session.commit()
        return "CARD_ADD_2: CARD SUCCESSFULLY CREATED.", 290

    def put(self, user_name, l_name, c_title):
        r_user=user_name
        r_list=l_name
        r_c_title=c_title
        r_c=Card.query.filter_by(c_user=r_user, c_list=r_list, c_title= r_c_title).first()
        
        
        if not User.query.get(user_name):
            return 'CARD_EDIT_USER_0: Request user does not exist in the db.', 230
        
        if not List.query.filter_by(l_user=user_name, l_name = r_list).first():
            return 'CARD_EDIT_LIST_0:Request list does not exist in db.', 231

        if not r_c:
            return "CARD_EDIT_CARD_0:CARD_TITLE DOES NOT EXIST in db", 232 #CARD_TITLE DOES NOT EXIST.
        else:
            r_doneornot=r_c.c_doneornot

        form = json.loads(request.data)
        f_c_title=form['c_title']

        f_c_user=r_user
        f_c_list=form['list']
        f_c_title=form['c_title']
        f_c_content=form['c_content']
        f_c_deadline=form['c_deadline']
        if 'c_doneornot' in form:
            f_c_doneornot=form['c_doneornot']
        else:
            f_c_doneornot=[]

        f_c_titless=Card.query.filter_by(c_user=f_c_user, c_list=f_c_list).all()
        f_c_titles=[]
        for each in f_c_titless:
            f_c_titles.append(each.c_title)
        if f_c_list==r_list:
            f_c_titles.remove(r_c_title)
        if f_c_title in f_c_titles:
            return "CARD_EDIT_CARD_0: CARD TITLE ALREADY EXIST.",233
        
        if find_day_difference(f_c_deadline)>0:
                return "CARD_EDIT_DEADLINE_0: THE CARD DEDLINE IS OF BEFORE TODAY'S.", 234

        if f_c_doneornot:
            f_c_doneornot='1'
        else:
            f_c_doneornot='0'

        r_c.c_list=f_c_list
        r_c.c_title=f_c_title
        r_c.c_content=f_c_content
        r_c.c_deadline=f_c_deadline
        r_c.c_doneornot=f_c_doneornot
        db.session.commit()
        return 'CARD_EDIT_1: CARD HAS BEEN SUCCESSFULLY UPDATED.', 290
        


    def delete(self, user_name, l_name, c_title):
        user=user_name
        list=l_name
        card=c_title
        c=Card.query.filter_by(c_user=user, c_list=list, c_title=card).first()
        
        u=User.query.get(user_name)
        if not u:
            return "CARD_DELETE_USER_0: REQUEST USER_NAME DOES NOT EXIST.", 230
        
        L=List.query.filter_by(l_user=user_name, l_name=list).first()
        if not L:
            return "CARD_DELETE_LIST_0: Request list name doesn't exist.", 231
        
        if not c:
            return 'CARD_DELETE_0: Card title doesn\'t exist.', 232 #card is no there.
        db.session.delete(c)
        db.session.commit()
        return 'CARD_DELETE_1: card successfully deleted.', 290 #card deleted.

api.add_resource(CardRc, '/api/card/<user_name>/<l_name>/<c_title>/', '/api/card/<user_name>/', '/api/card/<user_name>/<l_name>/')


class m_a_c_o_lRc(Resource):
    def get(self, user_name, l_name, f_list):
        r_user=user_name
        r_list=l_name
        f_l_name=f_list

        if not User.query.get(r_user):
            return 'm_a_c_o_l_USER_0: REQUEST USER NAME IS NOT THERE IN DB.',230
        if not List.query.filter_by(l_user=r_user, l_name=r_list).first():
            return 'm_a_c_o_l_R_LIST_0: REQUEST LIST NAME IS NOT THERE IN DB.',231
        if not List.query.filter_by(l_user=r_user, l_name=f_l_name).first():
            return 'm_a_c_o_l_F_LIST_0: IN THE LIST YOU WANT TO TRANSFER THE CARDS DOES NOT EXIST.', 232
        r_cardss= Card.query.filter_by(c_user=r_user).all()

        r_cards=[]
        for each in r_cardss:
            if each.c_list==r_list:
                r_cards.append(each.c_title)
        f_cards=[]
        for each in r_cardss:
            if each.c_list==f_l_name:
                f_cards.append(each.c_title)
        
        for each in r_cards:
            if each in f_cards:
                return 'm_a_c_o_l_ADD_0: Some card/cards of r_list is/are in f_list.',233

        for each in r_cardss:
            if each.c_list==r_list:
                each.c_list=f_l_name
                db.session.commit()
        r_l = List.query.filter_by(l_user=r_user, l_name=r_list).first()
        db.session.delete(r_l)
        db.session.commit()
        return 'm_a_c_o_l_ADD_1: ALL CARDS HAS BEEN SUCCESSFULLY TRANSFERED TO THE F_LIST AND R_LIST IS SUCCESSFULLY DELETED.',290
        
api.add_resource(m_a_c_o_lRc, '/api/m_a_c_o_l/<user_name>/<l_name>/<f_list>/')


class SummaryApi(Resource):
    def get(self, user_name):
        r_user=user_name
        if not User.query.get(r_user):
            return 'SUMMARY_USER_0:REQUEST USER DOES NOT EXIST',230
        listss=List.query.filter_by(l_user=r_user).all()
        
        cardss=Card.query.filter_by(c_user=r_user).all()
        total_cards=0
        completed=0
        d_o_p_b_c=0
        d={}
        for each in listss:
            d[each.l_name]={'total_cards':0 ,'completed':0 ,'in_progress':0, 'd_o_p_b_c':0}
        for each in listss:
            for c in cardss:
                if each.l_name==c.c_list:
                    d[each.l_name]['total_cards']+=1
                    if c.c_doneornot=='1':
                        d[each.l_name]['completed']+=1
                    else:
                        if find_day_difference(c.c_deadline)>0:
                            d[each.l_name]['d_o_p_b_c']+=1
                        else:
                            d[each.l_name]['in_progress']+=1
        return d, 290
    
    def post(self, user_name):
        r_user=user_name
        if not User.query.get(r_user):
            return 'SUMMARY_USER_0:REQUEST USER DOES NOT EXIST',230
        listss=List.query.filter_by(l_user=r_user).all()
    
        cardss=Card.query.filter_by(c_user=r_user).all()
        res = requests.get(f'http://127.0.0.1:5000/api/summary/{r_user}/')
        d= res.json()
        
        for each in listss:
            slices=[]
            labels=[]
            for i in d[each.l_name]:
                v=d[each.l_name][i]
                if v>0:
                    labels.append(i)
                    slices.append(v)
            labels=labels[1:]
            slices=slices[1:]
            plt.pie(slices, labels=labels, autopct='%.2f%%')
            plt.savefig(f'static/{r_user}_{each.l_name}.png', bbox_inches='tight')
            plt.close()
        return 'SUMMARY_1', 290

api.add_resource(SummaryApi, '/api/summary/<user_name>/')




#START---- Home & add and delete user
@app.route('/', methods=['GET','POST'])
def home():
    if request.method=='GET':
        return render_template('home.html')
    else:
        f_user=request.form.get('user')
        res = requests.get(f'http://localhost:5000/api/user/{f_user}/')
        if res.status_code == 230:
            return render_template('home.html', note='notexist')
        if res.status_code==290:
            user=f_user
            return redirect(f'/board/{user}')

@app.route('/add_user/', methods=['POST'])
def add_user():
    f_user=request.form.get('user')
    res = requests.post(f'http://localhost:5000/api/user/{f_user}/')
    if res.status_code == 230:
        return render_template('home.html', note='alreadyexist')
    if res.status_code==290:
        return redirect('/')

@app.route('/delete_user/<user_name>/')
def delete_user(user_name):
    user=user_name
    res = requests.delete(f'http://localhost:5000/api/user/{user}/')
    if res.status_code==230:
        return res.text
    if res.status_code==290:
        return redirect(url_for('home'))
#ENDED ---- Home & add and delete user


#START---- board
@app.route('/board/<user_name>/')
def board(user_name):
    user=user_name
    res = requests.get(f'http://localhost:5000/api/list/{user}')
    listss=res.json()
    if res.status_code==230:
        return res.text
    res = requests.get(f'http://localhost:5000/api/card/{user}')
    cardss= res.json()
    return render_template('board.html', user=user, listss=listss, cardss=cardss)
#END---- board

#START---- add, edit, delete list and move all cards to different list
@app.route('/board/<user_name>/add_list/', methods=['GET','POST'])
def add_list(user_name):
    user=user_name
    if request.method=='GET':
        return render_template('add_list.html', user=user)
    else:
        form={}
        for each in request.form:
            form[each]=f'{request.form[each]}'
        form=json.dumps(form) #converting dictionary into the string to transfer throug API URL.
        res = requests.post(f'http://localhost:5000/api/list/{user_name}/', data=form)
        if res.status_code==230:
            return res.text
        if res.status_code==232:
            return(render_template('add_list.html',note='spaceintitle',user=user)) 
        if res.status_code==231:
            return(render_template('add_list.html',note='alreadyexist',user=user))
        if res.status_code==290:
            return redirect(f'/board/{user}/')

@app.route('/board/<user_name>/edit_list/<l_name>/', methods=['GET','POST'])
def edit_list(user_name, l_name):
    r_user=user_name
    r_list=l_name
    res = requests.get(f'http://127.0.0.1:5000/api/list/{user_name}/')
    if res.status_code==230:
        return res.text
    r_listss=res.json()
    r_l=[]
    for each in r_listss:
        if r_listss[each]['l_name']==r_list:
            r_l=r_listss[each]
    if not r_l:
            return 'REQUEST LIST DOES NOT EXIST'

    if request.method=='GET':
        return render_template('edit_list.html',user=r_user, list=r_list, r_l=r_l)
    else:
        form = request.form
        form = json.dumps(form)
        res = requests.put(f'http://localhost:5000/api/list/{r_user}/{r_list}/', data = form)
        if res.status_code==230:
            return res.text
        if res.status_code==231:
            return res.text
        if res.status_code==233:
            return render_template('edit_list.html',note='spaceintitle',user=r_user, list=r_list, r_l=r_l)
        if res.status_code==232:
            return render_template('edit_list.html', note='alreadyexist',user=r_user, list=r_list, r_l=r_l)
        if res.status_code==290:
            return redirect(f'/board/{r_user}/')

@app.route('/board/<users_name>/delete_list/<l_name>')
def delete_list(users_name,l_name):
    user_name = users_name
    l_name = l_name
    res = requests.delete(f'http://localhost:5000/api/list/{user_name}/{l_name}/')    
    if res.status_code==230:
        return res.text
    if res.status_code==231:
        return res.text
    if res.status_code==290:
        return redirect(f'/board/{user_name}/')

@app.route('/board/<user_name>/move_all_cards_of_list/<l_name>/', methods=['GET','POST'])
def m_a_c_o_l(user_name,l_name):
    r_user=user_name
    r_list=l_name
    res = requests.get(f'http://localhost:5000/api/list/{r_user}')
    if res.status_code==230:
        return res.text

    r_listss= res.json()
    r_lists=[]
    for each in r_listss:
        r_lists.append(r_listss[each]['l_name'])
    

    if r_list not in r_lists:
        return 'REQUEST LIST IS NOT THERE IN DB.'
    else:
        r_lists.remove(r_list)

    if request.method=='GET':
        return render_template('m_a_c_o_l.html', user=r_user, l_name=l_name, lists=r_lists)
    else:
        f_list=request.form.get('list')
        res = requests.get(f'http://localhost:5000/api/m_a_c_o_l/{r_user}/{r_list}/{f_list}/')
        if res.status_code in [230,231,232]:
            return res.text
        if res.status_code==233:
            return render_template('m_a_c_o_l.html',note='cardexist', user=r_user, l_name=l_name, lists=r_lists)
        if res.status_code==290:
            return redirect(f'/board/{r_user}')   
#ENDED----add, edit, delete list and move all cards to different list


#START---- add, edit and delete card
@app.route('/board/<user_name>/<l_name>/add_card/', methods=['GET','POST'])
def add_card(user_name,l_name):
    user=user_name
    list=l_name
    today=date.today()

    res = requests.get(f'http://localhost:5000/api/list/{user}/')
    if res.status_code==230:
        return res.text

    listss=res.json()
    lists=[]
    for each in listss:
        lists.append(listss[each]['l_name'])
    

    if list not in lists:
        return 'REQUEST LIST IS NOT THERE IN DB.'
    else:
        lists.remove(list)

    if request.method=='GET':
        return render_template('add_card.html', user=user, list=list)
    else:
        form=json.dumps(request.form)
        res = requests.post(f'http://localhost:5000/api/card/{user}/{list}/', data=form)
        if res.status_code in [230,231]:
            return res.text
        if res.status_code==232:
            return render_template('add_card.html', note='alreadyexist', user=user, list=list)
        if res.status_code==233:
            return render_template('add_card.html', note='dateisearlier', user=user, list=list)
        if res.status_code==290:
            return redirect(f'/board/{user}/')


@app.route('/board/<user_name>/<l_name>/edit_card/<c_title>/', methods=['GET','POST'])
def edit_card(user_name,l_name,c_title):
    r_user=user_name
    r_list=l_name
    r_c_title=c_title
        #chech for user and list
    res = requests.get(f'http://localhost:5000/api/list/{r_user}/')
    if res.status_code==230:
        return res.text

    listss=res.json()
    lists=[]
    for each in listss:
        lists.append(listss[each]['l_name'])
    

    if r_list not in lists:
        return 'REQUEST LIST IS NOT THERE IN DB.'
    else:
        lists.remove(r_list)
        
        #check for cards
    res = requests.get(f'http://localhost:5000/api/card/{r_user}/')
    if res.status_code==230:
        return res.text
    r_cardss=res.json()
    r_c=[]
    for each in r_cardss:
        if r_cardss[each]['c_list']==r_list and r_cardss[each]['c_title']==r_c_title:
            r_c=r_cardss[each]
    if not r_c:
        return 'REQUEST CARD_TITLE IS NOT THERE IN THE LIST.'
    r_doneornot=r_c['c_doneornot']

    if request.method=='GET':
        return render_template('edit_card.html', user=r_user, list=r_list, lists=lists, card=r_c)
    
    else:
        form = json.dumps(request.form)
        res = requests.put(f'http://localhost:5000/api/card/{r_user}/{r_list}/{r_c_title}/', data = form)
        if res.status_code in [230, 231, 232]:
            return res.text
        if res.status_code==233:
            return render_template('edit_card.html',note='alreadyexist', user=r_user, list=r_list, lists=lists, card=r_c)
        if res.status_code==234:
            return render_template('edit_card.html', note='dateisearlier', user=r_user, list=r_list, lists=lists, card=r_c)
        if res.status_code==290:
            return redirect(f'/board/{r_user}/')
        else:
            return res

@app.route('/board/<user_name>/<l_name>/delete_card/<c_title>/')
def delete_card(user_name,l_name,c_title):
    user=user_name
    list=l_name
    card=c_title    
    res = requests.delete(f'http://127.0.0.1:5000/api/card/{user}/{list}/{card}/')
    if res.status_code in [230,231,232]:
        return res.text
    if res.status_code==290:
        return redirect(f'/board/{user}/')


@app.route('/board/<user_name>/summary/')
def summary(user_name):
    r_user=user_name

    res = requests.get(f'http://localhost:5000/api/list/{r_user}/')
    listss = res.json()

    res1 = requests.get(f'http://127.0.0.1:5000/api/summary/{r_user}/')
    if res1.status_code==230:
        return res1.text
    d=res1.json()
    res2 = requests.post(f'http://127.0.0.1:5000/api/summary/{r_user}/')
    if res1.status_code==res2.status_code==290:
        return render_template('summary.html', user=r_user, listss=listss, d=d) 


   

if __name__ == '__main__':
    app.run(debug=True)