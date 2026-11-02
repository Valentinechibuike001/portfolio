import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "***REMOVED*** ")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///portfolio.db"
db = SQLAlchemy(app)

GITHUB_URL = "https://github.com/valentinechibuike001"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "***REMOVED***")


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    tech = db.Column(db.String(200), nullable=False)
    image = db.Column(db.String(200), default="")
    github = db.Column(db.String(300), default="#")
    live = db.Column(db.String(300), default="#")

    def tech_list(self):
        return [item.strip() for item in self.tech.split(",") if item.strip()]
    

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

with app.app_context():
    db.create_all()
    if Project.query.count() == 0:
        db.session.add_all([
            Project(
                title="Personal Portfolio",
                description="The website you are looking at, built with Python and Flask.",
                tech="Python, Flask, HTML, CSS",
                image="",
                github="#",
                live="#",
            ),
        ])
        db.session.commit()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/projects")
def projects_page():
    all_projects = Project.query.all()
    return render_template("projects.html", projects=all_projects)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            flash("Please fill in every box.", "error")
        elif len(name) > 100 or len(email) > 200 or len(message) > 5000:
            flash("Your message is too long.", "error")
        else:
            db.session.add(Message(name=name, email=email, body=message))
            db.session.commit()
            flash("Thanks! Your message has been sent.", "success")
            return redirect(url_for("contact"))

    return render_template("contact.html")

@app.route("/github")
def github():
    return redirect(GITHUB_URL)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("Wrong password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("home"))


@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        tech = request.form.get("tech", "").strip()
        image = request.form.get("image", "").strip()
        github_link = request.form.get("github", "").strip() or "#"
        live_link = request.form.get("live", "").strip() or "#"

        if not title or not description or not tech:
            flash("Title, description and tech are required.", "error")
        else:
            db.session.add(Project(
                title=title,
                description=description,
                tech=tech,
                image=image,
                github=github_link,
                live=live_link,
            ))
            db.session.commit()
            flash("Project added!", "success")
            return redirect(url_for("admin"))

    all_projects = Project.query.all()
    return render_template("admin.html", projects=all_projects, message_count=Message.query.count())

@app.route("/admin/delete/<int:project_id>", methods=["POST"])
@login_required
def delete_project(project_id):
    project = db.session.get(Project, project_id)
    if project:
        db.session.delete(project)
        db.session.commit()
        flash("Project deleted.", "success")
    return redirect(url_for("admin"))




@app.route("/admin/edit/<int:project_id>", methods=["GET", "POST"])
@login_required
def edit_project(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for("admin"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        tech = request.form.get("tech", "").strip()

        if not title or not description or not tech:
            flash("Title, description and tech are required.", "error")
        else:
            project.title = title
            project.description = description
            project.tech = tech
            project.image = request.form.get("image", "").strip()
            project.github = request.form.get("github", "").strip() or "#"
            project.live = request.form.get("live", "").strip() or "#"
            db.session.commit()
            flash("Project updated!", "success")
            return redirect(url_for("admin"))

    return render_template("edit.html", project=project)



@app.route("/admin/messages")
@login_required
def messages_page():
    all_messages = Message.query.order_by(Message.created.desc()).all()
    return render_template("messages.html", messages=all_messages)


@app.route("/admin/messages/delete/<int:message_id>", methods=["POST"])
@login_required
def delete_message(message_id):
    msg = db.session.get(Message, message_id)
    if msg:
        db.session.delete(msg)
        db.session.commit()
        flash("Message deleted.", "success")
    return redirect(url_for("messages_page"))



if __name__ == "__main__":
    app.run(debug=True)