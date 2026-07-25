import csv
from flask import Response
from flask import Flask, render_template, request, redirect, flash, session
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = "library123"

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'library_db'

mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    # Total Books
    cur.execute("SELECT COUNT(*) FROM books")
    total_books = cur.fetchone()[0]

    # Total Members
    cur.execute("SELECT COUNT(*) FROM members")
    total_members = cur.fetchone()[0]

    # Issued Books
    cur.execute("SELECT COUNT(*) FROM issue_books WHERE status='Issued'")
    issued_books = cur.fetchone()[0]

    # Returned Books
    cur.execute("SELECT COUNT(*) FROM issue_books WHERE status='Returned'")
    returned_books = cur.fetchone()[0]

    cur.close()

    return render_template(
        "dashboard.html",
        total_books=total_books,
        total_members=total_members,
        issued_books=issued_books,
        returned_books=returned_books
    )

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

@app.route('/export_books')
def export_books():

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM books")

    books = cur.fetchall()

    cur.close()

    def generate():

        data = csv.writer

        yield "ID,Book,Author,Category,Quantity,Available\n"

        for b in books:

            yield f"{b[0]},{b[1]},{b[2]},{b[3]},{b[4]},{b[5]}\n"

    return Response(
        generate(),
        mimetype='text/csv',
        headers={
            "Content-Disposition":
            "attachment;filename=books.csv"
        }
    )

@app.route('/books')
def books():

    search = request.args.get('search')

    cur = mysql.connection.cursor()

    if search:
        cur.execute(
            "SELECT * FROM books WHERE book_name LIKE %s",
            ("%" + search + "%",)
        )
    else:
        cur.execute("SELECT * FROM books")

    books = cur.fetchall()

    cur.close()

    return render_template('books.html', books=books)

@app.route('/add_book', methods=['POST'])
def add_book():

    book_name = request.form['book_name']
    author = request.form['author']
    category = request.form['category']
    quantity = request.form['quantity']

    cur = mysql.connection.cursor()

    cur.execute("""
        INSERT INTO books(book_name,author,category,quantity,available)
        VALUES(%s,%s,%s,%s,%s)
    """, (book_name, author, category, quantity, quantity))

    mysql.connection.commit()
    cur.close()

    return redirect('/books')

@app.route('/edit_book/<int:id>')
def edit_book(id):

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM books WHERE id=%s", (id,))

    book = cur.fetchone()

    cur.close()

    return render_template("edit_book.html", book=book)

@app.route('/update_book/<int:id>', methods=['POST'])
def update_book(id):

    book_name = request.form['book_name']
    author = request.form['author']
    category = request.form['category']
    quantity = request.form['quantity']

    cur = mysql.connection.cursor()

    cur.execute("""
        UPDATE books
        SET book_name=%s,
            author=%s,
            category=%s,
            quantity=%s,
            available=%s
        WHERE id=%s
    """,
    (book_name, author, category, quantity, quantity, id))

    mysql.connection.commit()

    cur.close()

    return redirect('/books')

@app.route('/delete_book/<int:id>')
def delete_book(id):

    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM books WHERE id=%s", (id,))

    mysql.connection.commit()

    cur.close()

    return redirect('/books')

@app.route('/save_user', methods=['POST'])
def save_user():
    try:
        fullname = request.form['fullname']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        cur = mysql.connection.cursor()

        cur.execute(
            "INSERT INTO users (fullname, email, phone, password) VALUES (%s, %s, %s, %s)",
            (fullname, email, phone, password)
        )

        mysql.connection.commit()
        cur.close()

        flash("Registration Successful")
        return redirect('/login')

    except Exception as e:
        return f"Error: {e}"

@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )

        user = cur.fetchone()

        cur.close()

        if user:
            session['user'] = user[1]
            session['email'] = user[2]

            return redirect('/dashboard')
        else:
            flash("Invalid Email or Password")
            return redirect('/login')

    return render_template('login.html')

# ---------------- MEMBER MANAGEMENT ----------------

@app.route('/members')
def members():

    search = request.args.get('search')

    cur = mysql.connection.cursor()

    if search:
        cur.execute(
            "SELECT * FROM members WHERE member_name LIKE %s",
            ("%" + search + "%",)
        )
    else:
        cur.execute("SELECT * FROM members")

    members = cur.fetchall()

    cur.close()

    return render_template("members.html", members=members)


@app.route('/add_member', methods=['POST'])
def add_member():

    member_name = request.form['member_name']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']

    cur = mysql.connection.cursor()

    cur.execute("""
        INSERT INTO members(member_name,email,phone,address)
        VALUES(%s,%s,%s,%s)
    """,(member_name,email,phone,address))

    mysql.connection.commit()

    cur.close()

    return redirect('/members')


@app.route('/edit_member/<int:id>')
def edit_member(id):

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM members WHERE id=%s",(id,))

    member = cur.fetchone()

    cur.close()

    return render_template("edit_member.html", member=member)


@app.route('/update_member/<int:id>', methods=['POST'])
def update_member(id):

    member_name = request.form['member_name']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']

    cur = mysql.connection.cursor()

    cur.execute("""
        UPDATE members
        SET member_name=%s,
            email=%s,
            phone=%s,
            address=%s
        WHERE id=%s
    """,(member_name,email,phone,address,id))

    mysql.connection.commit()

    cur.close()

    return redirect('/members')


@app.route('/delete_member/<int:id>')
def delete_member(id):

    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM members WHERE id=%s",(id,))

    mysql.connection.commit()

    cur.close()

    return redirect('/members')

@app.route('/save_issue', methods=['POST'])
def save_issue():

    member_id = request.form['member_id']
    book_id = request.form['book_id']
    issue_date = request.form['issue_date']

    cur = mysql.connection.cursor()

    cur.execute("""
        INSERT INTO issue_books(member_id,book_id,issue_date)
        VALUES(%s,%s,%s)
    """,(member_id,book_id,issue_date))

    cur.execute("""
        UPDATE books
        SET available = available - 1
        WHERE id=%s
    """,(book_id,))

    mysql.connection.commit()

    cur.close()

    return redirect('/issue_book')

@app.route('/return_book/<int:id>')
def return_book(id):

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT book_id
        FROM issue_books
        WHERE id=%s
    """,(id,))

    book = cur.fetchone()

    cur.execute("""
        UPDATE issue_books
        SET status='Returned',
            return_date=CURDATE()
        WHERE id=%s
    """,(id,))

    cur.execute("""
        UPDATE books
        SET available = available + 1
        WHERE id=%s
    """,(book[0],))

    mysql.connection.commit()

    cur.close()

    return redirect('/issue_book')

@app.route('/issue_book')
def issue_book():

    cur = mysql.connection.cursor()

    cur.execute("SELECT id, member_name FROM members")
    members = cur.fetchall()

    cur.execute("SELECT id, book_name FROM books WHERE available > 0")
    books = cur.fetchall()

    cur.execute("""
        SELECT issue_books.id,
               members.member_name,
               books.book_name,
               issue_books.issue_date,
               issue_books.return_date,
               issue_books.status,
               issue_books.fine
        FROM issue_books
        JOIN members ON issue_books.member_id = members.id
        JOIN books ON issue_books.book_id = books.id
    """)

    issued = cur.fetchall()

    cur.close()

    return render_template(
        "issue_book.html",
        members=members,
        books=books,
        issued=issued
    )

@app.route('/calculate_fine')
def calculate_fine():

    cur = mysql.connection.cursor()

    cur.execute("""
        UPDATE issue_books
        SET fine =
        CASE
            WHEN status='Returned'
            AND DATEDIFF(return_date, issue_date) > 15
            THEN (DATEDIFF(return_date, issue_date)-15)*5
            ELSE 0
        END
    """)

    mysql.connection.commit()

    cur.close()

    flash("Fine Calculated Successfully")

    return redirect('/issue_book')

if __name__ == "__main__":
    app.run(debug=True)