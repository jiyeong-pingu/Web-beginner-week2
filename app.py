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
    # DB 연결을 한 번만 열어서 필요한 데이터를 가져옴
    conn = db()
    posts = conn.execute("SELECT * FROM post ORDER BY id DESC").fetchall()
    all_comments = conn.execute("SELECT * FROM comment ORDER BY id ASC").fetchall()
    conn.close() # 데이터를 다 가져왔으니 안전하게 닫아줌
    
    # 파이썬 메모리 상에서 게시글 ID에 맞게 분류
    posts_with_comments = []
    for post in posts:
        # 전체 댓글 중 현재 게시글(post["id"])에 속한 댓글들만 필터링합니다.
        comments = [c for c in all_comments if c["post_id"] == post["id"]]
        
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
        try:
            conn.execute("INSERT INTO user VALUES(?, ?)",
                         (request.form["username"], generate_password_hash(request.form["password"])))
        except sqlite3.IntegrityError:
            return redirect("/")
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
