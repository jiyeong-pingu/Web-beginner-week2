import sqlite3
from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret"


def db():
    conn = sqlite3.connect("board.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS user(username TEXT PRIMARY KEY, password TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS post(id INTEGER PRIMARY KEY, title TEXT, content TEXT, author TEXT)")
        #댓글
        conn.execute("""
            CREATE TABLE IF NOT EXISTS comment(
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                post_id INTEGER, 
                content TEXT, 
                author TEXT
            )
        """)


@app.route("/")
def index():
    posts = db().execute("SELECT * FROM post ORDER BY id DESC").fetchall()
    #게시글마다 댓글 매칭해서 딕셔너리로 묶어주기
    posts_with_comments = []
    for post in posts:
        comments = db().execute(
            "SELECT * FROM comment WHERE post_id=? ORDER BY id ASC", 
            (post["id"],)
        ).fetchall()
        
        posts_with_comments.append({
            "id": post["id"],
            "title": post["title"],
            "content": post["content"],
            "author": post["author"],
            "comments": comments
        })
        
    return render_template("index.html", posts=posts_with_comments, user=session.get("user"))


@app.route("/register", methods=["POST"])
def register():
    with db() as conn:
        conn.execute("INSERT INTO user VALUES(?, ?)",
                     (request.form["username"], generate_password_hash(request.form["password"])))
    return redirect("/")


@app.route("/login", methods=["POST"])
def login():
    row = db().execute(
        "SELECT * FROM user WHERE username=?", (request.form["username"],)
    ).fetchone()
    if row and check_password_hash(row["password"], request.form["password"]):
        session["user"] = row["username"]
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/write", methods=["POST"])
def write():
    if "user" in session:
        with db() as conn:
            conn.execute(
                "INSERT INTO post(title, content, author) VALUES(?, ?, ?)",
                (request.form["title"], request.form["content"], session["user"]),
            )
    return redirect("/")

@app.route("/write_comment", methods=["POST"])
def write_comment():
    if "user" in session:
        with db() as conn:
            conn.execute(
                "INSERT INTO comment(post_id, content, author) VALUES(?, ?, ?)",
                (request.form["post_id"], request.form["content"], session["user"])
            )
    return redirect("/")

@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    #  로그인 여부 확인
    if "user" in session:
        with db() as conn:
            # 본인이 쓴 글이 맞는지 검증하며 DELETE 수행
            conn.execute(
                "DELETE FROM post WHERE id=? AND author=?", 
                (post_id, session["user"])
            )
    return redirect("/")

@app.route("/edit/<int:post_id>", methods=["POST"])
def edit_post(post_id):
    # 로그인 여부 확인
    if "user" in session:
        with db() as conn:
            # 본인이 쓴 글이 맞는지 검증하며 REVISE 수행
            conn.execute(
                "UPDATE post SET title=?, content=? WHERE id=? AND author=?",
                (request.form["title"], request.form["content"], post_id, session["user"])
            )
    return redirect("/")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
