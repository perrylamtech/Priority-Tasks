import os  # os is used to get environment variables IP & PORT
import re
from datetime import datetime

from flask import Flask, session
from flask import render_template
from flask import request, redirect, url_for

from database import db
from forms import CommentForm
from models import User, Todo, Comment, Team

app = Flask(__name__)  # create an app

# sqp setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.secret_key = "abc"
db.init_app(app)
user = User


@app.route("/")
def index():
    global user
    return render_template('index.html')


@app.route('/task')
def task():
    global user
    if user == User:
        return render_template('login.html', error="Please Log In To access this page")
    todo_list = Todo.query.all()
    team_list = Team.query.all()
    user_list = User.query.all()
    return render_template('task.html', todo_list=todo_list, user_list=user_list, user=user, teamlist=team_list)


@app.route("/add", methods=["POST"])
def add():
    global user
    title = request.form.get("title")
    description = request.form.get("description")
    due = request.form.get("due")
    assigned = ', '.join(request.form.getlist("assigned"))
    due = datetime.strptime(due, "%Y-%m-%d")
    new_todo = Todo(title=title, description=description, due=due, assigned=assigned, complete=0, createdBy=user.id)
    db.session.add(new_todo)
    db.session.commit()
    return redirect(url_for("task"))


@app.route("/update/<int:todo_id>")
def update(todo_id: int):
    global user
    todo = Todo.query.filter_by(id=todo_id).first()
    if todo.complete == 100:
        todo.complete = 0
    else:
        todo.complete = int(todo.complete) + 25
    db.session.commit()
    return redirect(url_for("task"))


@app.route("/delete/<int:todo_id>")
def delete(todo_id: int):
    global user
    todo = Todo.query.filter_by(id=todo_id).first()
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for("task"))


@app.route("/task/<string:sort_id>/<int:order_id>")
def sort_task(sort_id, order_id):
    global user
    if user == User:
        return render_template('login.html', error="Please Log In To access this page")
    todo_list = None
    if order_id == 0:  # 0 sorts in ascending order
        if sort_id == "Title":
            todo_list = Todo.query.order_by(Todo.title)
        if sort_id == "Description":
            todo_list = Todo.query.order_by(Todo.description)
        if sort_id == "Due":
            todo_list = Todo.query.order_by(Todo.due)
        if sort_id == "AssignedTo":
            todo_list = Todo.query.order_by(Todo.assigned)
        if sort_id == "Status":
            todo_list = Todo.query.order_by(Todo.complete.desc())
    elif order_id == 1:  # 1 sorts in descending order
        if sort_id == "Title":
            todo_list = Todo.query.order_by(Todo.title.desc())
        if sort_id == "Description":
            todo_list = Todo.query.order_by(Todo.description.desc())
        if sort_id == "Due":
            todo_list = Todo.query.order_by(Todo.due.desc())
        if sort_id == "AssignedTo":
            todo_list = Todo.query.order_by(Todo.assigned.desc())
        if sort_id == "Status":
            todo_list = Todo.query.order_by(Todo.complete)

    user_list = User.query.all()
    return render_template('task.html', todo_list=todo_list, user_list=user_list, user=user)


@app.route("/register", methods=('GET', 'POST'))
def register():
    global user
    if request.method == 'POST':
        name = request.form.get("name")
        email = request.form.get("email")
        username = request.form.get("username").lower()
        password = request.form.get("password")
        if User.query.filter_by(email=email).first() or User.query.filter_by(username=username).first():
            message = []
            message.append("Username or Email already in use")
            return render_template('register.html', message=message)
        else:
            # calculating the length
            length_error = len(password) < 8

            # searching for digits
            digit_error = re.search(r"\d", password) is None

            # searching for uppercase
            uppercase_error = re.search(r"[A-Z]", password) is None

            # searching for lowercase
            lowercase_error = re.search(r"[a-z]", password) is None

            # overall result
            password_ok = not (length_error or digit_error or uppercase_error or lowercase_error)
            message = []
            if length_error:
                message.append('Password must be 8 characters')
            if digit_error:
                message.append('Password must contain at least one number')
            if uppercase_error:
                message.append('Password must have at least one uppercase character')
            if lowercase_error:
                message.append('Password must have at least one lowercase character')
            if password_ok:
                new_user = User(name=name, email=email, username=username, password=password, access=False)
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('login'))
            else:
                return render_template('register.html', message=message)
    return render_template('register.html', user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    global user
    error = None
    if request.method == 'POST':
        current_user = User.query.filter_by(username=request.form['username'].lower()).first()
        if current_user is None:
            error = 'Invalid Username. Please try again.'
        elif current_user.password != request.form['password']:
            error = 'Invalid Password. Please try again.'
            current_user = None
        else:
            session["user"] = current_user.id
            global user
            user = current_user
            return redirect(url_for('task'))
    return render_template('login.html', error=error)


@app.route("/updateUser/<int:user_id>", methods=['GET', 'POST'])
def update_user(user_id: int):
    global user
    user_list = User.query.all()
    team_list = Team.query.all()
    # user_list = User.query.all()
    if request.method == 'POST':
        edit_user = User.query.filter_by(id=user_id).first()

        if request.form.get("updatePass", False) != edit_user.password:
            global user
            if user.access == 1:
                edit_user.password = request.form["updatePass"]
            else:
                password = request.form.get("updatePass", False)
                # calculating the length
                length_error = len(password) < 8
                # searching for digits
                digit_error = re.search(r"\d", password) is None
                # searching for uppercase
                uppercase_error = re.search(r"[A-Z]", password) is None
                # searching for lowercase
                lowercase_error = re.search(r"[a-z]", password) is None
                # overall result
                password_ok = not (length_error or digit_error or uppercase_error or lowercase_error)
                message = []
                if length_error:
                    message.append('Password must be 8 characters')
                if digit_error:
                    message.append('Password must contain at least one number')
                if uppercase_error:
                    message.append('Password must have at least one uppercase character')
                if lowercase_error:
                    message.append('Password must have at least one lowercase character')
                if password_ok:
                    edit_user.password = request.form["updatePass"]
                else:
                    return render_template('ViewUsers.html', message=message, user=user)
        if request.form.get("editEmail", False) != edit_user.email:
            edit_user.email = request.form["editEmail"]
        if request.form.get("editUsername", False) != edit_user.username:
            if User.query.filter_by(username=request.form.get("editUsername")).first():
                return render_template('ViewUsers.html', user_list=user_list, user=user, team_list=team_list,
                                       error="Username or Email already in use")

            edit_user.username = request.form["editUsername"].lower()
        if request.form.get("editName", False) != edit_user.name:
            edit_user.name = request.form["editName"]
        if request.form['editTeam'] != edit_user.team:
            edit_user.team = request.form['editTeam']
        if user.access == 1:
            if request.form.get("editAccess", False) == "Basic":
                access = False
            elif request.form.get("editAccess", False) == "Admin":
                access = True
            if access != edit_user.access:
                edit_user.access = access
        db.session.commit()
    user = User.query.filter_by(id=user.id).first()
    return redirect(url_for("view_users"))


@app.route('/ViewUsers', methods=['GET', 'POST'])
def view_users():
    global user
    user_list = User.query.all()
    team_list = Team.query.all()
    if user == User:
        return render_template('login.html', error="Please Log In To access this page")
    if request.method == 'POST':
        name = request.form.get("name")
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        access = request.form.get("access")
        username = username.lower()
        if int(access) == 0:
            access = False
        elif int(access) == 1:
            access = True
        if User.query.filter_by(email=email).first() or User.query.filter_by(username=username).first():
            return render_template('ViewUsers.html', user_list=user_list, user=user, team_list=team_list,
                                   error="Username or Email already in use")
        else:
            new_user = User(name=name, email=email, username=username, password=password, access=access)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("view_users"))
    return render_template('ViewUsers.html', user_list=user_list, user=user, team_list=team_list)


@app.route("/deleteUser/<int:user_id>")
def delete_user(user_id: int):
    global user
    deleted_user = User.query.filter_by(id=user_id).first()
    db.session.delete(deleted_user)
    db.session.commit()
    return redirect(url_for("view_users"))


@app.route("/logout")
def logout():
    global user
    user = User
    return render_template('index.html')


@app.route('/editTask/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    global user
    if user:
        user_list = User.query.all()
        team_list = Team.query.all()
        if request.method == 'POST':
            edited_task = Todo.query.filter_by(id=task_id).first()
            if request.form.get("editTitle", False) != edited_task.title:
                edited_task.title = request.form["editTitle"]
            if request.form.get("editDescription ", False) != edited_task.description:
                edited_task.description = request.form["editDescription "]
            if request.form.get("editDue", False) != edited_task.due:
                due = datetime.strptime(request.form["editDue"], "%Y-%m-%d")
                edited_task.due = due
            if request.form.get("assigned", False) != edited_task.assigned:
                edited_task.assigned = ', '.join(request.form.getlist("assigned"))

            db.session.commit()
            return redirect(url_for("task"))
        return render_template('editTask.html', user_list=user_list, user=user,
                               todo=Todo.query.filter_by(id=task_id).first(), teamlist=team_list)
    else:
        redirect(url_for('view_task', task_id=task_id))


@app.route('/viewTask/<int:task_id>')
def view_task(task_id):
    global user
    user_list = User.query.all()
    if user == User:
        return redirect(url_for('login'))
    else:
        form = CommentForm()
        return render_template('viewTask.html', user=user, user_list=user_list,
                               todo=Todo.query.filter_by(id=task_id).first(), form=form)


@app.route('/task/<task_id>/comment', methods=['POST'])
def new_comment(task_id):
    global user
    if user == User:
        return render_template('login.html', error="Please Log In To access this page")
    else:
        comment_form = CommentForm()
        # validate_on_submit only validates using POST
        if comment_form.validate_on_submit():
            # get comment data
            comment_text = request.form['comment']
            new_record = Comment(comment_text, int(task_id), user.id)
            db.session.add(new_record)
            db.session.commit()

        return redirect(url_for('view_task', task_id=task_id))


@app.route("/deleteComment/<int:comment_id>")
def delete_comment(comment_id: int):
    global user
    comment = Comment.query.filter_by(id=comment_id).first()
    task_id = comment.todo_id
    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for('view_task', task_id=task_id))


@app.route('/pin/<task_id>')
def pin_task(task_id: str):
    global user
    user_id = user.id
    edit_user = User.query.filter_by(id=user_id).first()
    pinned = str(edit_user.pinnedTask)
    if edit_user.pinnedTask != "":
        if task_id not in pinned:
            pinned = pinned + '(' + task_id + ')'
    else:
        pinned = "(" + task_id + ")"
    edit_user.pinnedTask = pinned
    db.session.commit()
    user = User.query.filter_by(id=user.id).first()
    return redirect(url_for('task'))


@app.route('/unpin/<task_id>')
def unpin_task(task_id: str):
    global user
    user_id = user.id
    edit_user = User.query.filter_by(id=user_id).first()
    pinned = str(edit_user.pinnedTask)
    remove = '(' + task_id + ')'
    remove = str(remove)
    pinned = pinned.replace(remove, "")
    edit_user.pinnedTask = pinned
    db.session.commit()
    user = User.query.filter_by(id=user.id).first()
    return redirect(url_for('task'))


@app.route('/newTeam', methods=['GET', 'POST'])
def new_team():
    if request.method == 'POST':
        if Team.query.filter_by(name=request.form['name']).first() is None:
            new_team = Team(request.form.get("name"))
            db.session.add(new_team)
            db.session.commit()
        else:
            return render_template('viewTeam.html', error="Team name is already in use")
    return redirect(url_for('view_team'))


@app.route('/deleteTeam/<int:team_id>')
def delete_team(team_id):
    delete = Team.query.filter_by(id=team_id).first()
    db.session.delete(delete)
    db.session.commit()
    return redirect(url_for('view_team'))


@app.route('/viewTeam')
def view_team():
    global user
    if user == User:
        return render_template('login.html', error="Please Log In To access this page")
    else:
        user_list = User.query.all()
        team_list = Team.query.all()
        return render_template('viewTeam.html', user_list=user_list, team_list=team_list, user=user)


@app.route('/searchUsers', methods=['GET', 'POST'])
def search_users():
    global user
    if user is User:
        return render_template('login.html', error='Please log in to view this page')
    else:
        if request.method == 'POST':
            team_list = Team.query.all()
            name = request.form['name']
            email = request.form['email']
            username = request.form['username']
            access = request.form['access']
            team = request.form['team']
            user_list = User.query.filter(
                (User.name.like(request.form['name'])) | (User.email.like(request.form['email'])) |
                (User.username.like(request.form['username'])) | (
                        User.access == request.form['access']) |
                (User.team == request.form['team'])).all()
            return render_template('ViewUsers.html', user_list=user_list, user=user, team_list=team_list)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host=os.getenv('IP', '127.0.0.1'), port=int(os.getenv('PORT', 5000)), debug=True)

# To see the web page in your web browser, go to the url,
#   http://127.0.0.1:5000
