import pyodbc

con = pyodbc.connect(Trusted_Connection='yes', driver='{SQL Server}', server='ETNA\\SQLEXPRESS', database='Library')

def auth(login, password):
    cursor = con.cursor()
    cursor.execute("SELECT [Login], [Password] FROM [Library].[dbo].[Auth]")
    for string in cursor:
        if string[0].strip() == login and string[1].strip() == password:
            return True
    return False

def welcome(login):
    cursor = con.cursor()
    cursor.execute("SELECT Name FROM Library.dbo.Readers WHERE Login='{}'".format(login))
    for string in cursor:
        return string[0]
    cursor.execute("SELECT Name FROM Library.dbo.Personal WHERE Login='{}'".format(login))
    for string in cursor:
        return string[0]

def add_book(Library, Title, Author, Release_Date, Language, Image_path, Description, quantity):
    cursor = con.cursor()
    #Image = cursor.execute("SELECT * FROM OPENROWSET (BULK '{}', SINGLE_BLOB) AS IMAGE".format(Image_path))
    if Image_path != "":
        with open(Image_path, 'rb') as f:
            image_data = f.read()
        cursor.execute("INSERT INTO Books (Library, Title, Author, Release_Date, Language, Image, Description, Quantity) VALUES (?,?,?,?,?,?,?,?)",
                       Library, Title, Author, Release_Date, Language, image_data, Description, quantity)
    else:
        cursor.execute("INSERT INTO Books (Library, Title, Author, Release_Date, Language, Description, Quantity) VALUES (?,?,?,?,?,?,?)",
                       Library, Title, Author, Release_Date, Language, Description, quantity)
    con.commit()

def select_libraries():
    cursor = con.cursor()
    cursor.execute("SELECT Library_Name FROM Libraries")
    libraries = []
    for string in cursor:
        libraries.append(string[0].strip())
    return libraries

def select_books(library):
    cursor = con.cursor()
    cursor.execute("SELECT Title, Library FROM Books")
    books = []
    for string in cursor:
        if library == string[1].strip():
            books.append(string[0].strip())
    return books

def notes_count(table):
    cursor = con.cursor()
    cursor.execute("SELECT COUNT(*) FROM {}".format(table))
    for string in cursor:
        return string[0]

def parse_notes(table):
    cursor = con.cursor()
    cursor.execute("SELECT * FROM {}".format(table))
    return cursor.fetchall()

def parse_users(login):
    cursor = con.cursor()
    cursor.execute("SELECT * FROM Library.dbo.Personal WHERE Login='{}'".format(login))
    temp_fetch = cursor.fetchall()
    if temp_fetch == []:
        cursor.execute("SELECT * FROM Library.dbo.Readers WHERE Login='{}'".format(login))
        return ["Reader", cursor.fetchall()[0]]
    return ["Personal", temp_fetch[0]]

def parse_quantity(id):
    cursor = con.cursor()
    cursor.execute("SELECT Quantity FROM Books WHERE Book_Id ='{}'".format(id))
    quantity = cursor.fetchall()[0][0]
    return quantity

def change_quantity(id, quantity):
    cursor = con.cursor()
    cursor.execute("UPDATE Books SET Quantity = {} WHERE Book_Id = {}".format(quantity, id))
    con.commit()