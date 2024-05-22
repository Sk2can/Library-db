from datetime import datetime, timedelta
import pyodbc

con = pyodbc.connect(Trusted_Connection='yes', driver='{SQL Server}', server='ETNA\\SQLEXPRESS', database='Library')

def del_library(lib_name):
    cursor = con.cursor()
    cursor.execute("DELETE FROM Libraries WHERE Library_Name = '{}'".format(lib_name))
    con.commit()

def add_library(name, adress, open, close, phone, pc, room):
    cursor = con.cursor()
    cursor.execute(
        "INSERT INTO Libraries (Library_Name, Address, Opening_Hours, Closing_Hours,"
        " Contact_Number, Computer_Class, Reading_Room) VALUES (?,?,?,?,?,?,?)",
        name, adress, open, close, phone, pc, room)
    con.commit()

def update_info(table, column, key_column, key, new_value):
    cursor = con.cursor()
    cursor.execute("UPDATE {} SET {} = '{}' WHERE {} = '{}'".format(
        table, column, new_value, key_column, key))
    con.commit()

def del_expired_books():
    cursor = con.cursor()
    cursor.execute("UPDATE Books SET Quantity = Quantity + 1 WHERE EXISTS(SELECT 1 FROM Rented_Books WHERE CAST(Return_Date AS DATETIME) < GETDATE());")
    cursor.execute("DELETE FROM Rented_Books WHERE CAST(Return_Date AS DATETIME) < GETDATE()")
    con.commit()

def rent_book(book_info, login):
    cursor = con.cursor()
    current_date = datetime.now()
    one_month_later = (current_date + timedelta(days=30))
    cursor.execute("INSERT INTO Rented_Books (Book_Id, Return_Date, Reader_Login) VALUES (?,?,?)",
        int(book_info[7]), one_month_later, login)
    cursor.execute("UPDATE Books SET Quantity = Quantity - 1 WHERE Book_Id = '{}'".format(book_info[7]))
    con.commit()

def search_book(id):
    cursor = con.cursor()
    cursor.execute("SELECT Library, Author, Title, Release_Date, Language, Description, Quantity, Book_Id "
                   "FROM Library.dbo.Books WHERE Book_Id='{}'".format(id))
    return cursor.fetchone()

def update_users_info(new_table):
    cursor = con.cursor()
    cursor.execute("DELETE FROM Readers")
    for row in new_table:
        cursor.execute("INSERT INTO Readers (Login, Name, Surname, Patronymic, Birth_Date, Contact_Number, Email) "
                       "VALUES (?,?,?,?,?,?,?)",
                       row[0], row[2], row[3], row[4], row[5], row[6], row[7])
    con.commit()

def update_library_info(lib, adr, op_hr, cls_hr, p_num, pc, rm):
    cursor = con.cursor()
    print("UPDATE Libraries SET Address = {}, Opening_Hours = {}, Closing_Hours = {}, "
                   "Contact_Number = {}, Computer_Class = {}, Reading_Room = {} WHERE Library_Name = {}".format(
        adr, op_hr, cls_hr, p_num, pc, rm, lib))
    cursor.execute("UPDATE Libraries SET Address = '{}', Opening_Hours = '{}', Closing_Hours = '{}', Contact_Number = '{}', Computer_Class = '{}', Reading_Room = '{}' WHERE Library_Name = '{}'".format(
        adr, op_hr, cls_hr, p_num, pc, rm, lib))
    con.commit()

def update_employee_info(new_table):
    cursor = con.cursor()
    cursor.execute("DELETE FROM Personal")
    for row in new_table:
        cursor.execute("INSERT INTO Personal (Login, Library, Name, Surname, Patronymic, Passport_Number, SNILS_Number, INN_Number) "
                       "VALUES (?,?,?,?,?,?,?,?)",
                       row[0], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
    con.commit()

def is_row_exist(table, column, value):
    cursor = con.cursor()
    cursor.execute("SELECT * FROM Library.dbo.{} WHERE {}='{}'".format(table, column, value))
    row = cursor.fetchone()
    if row:
        return True
    else:
        return False

def auth(login, password):
    cursor = con.cursor()
    cursor.execute("SELECT [Login], [Password] FROM [Library].[dbo].[Auth]")
    for string in cursor:
        if string[0].strip() == login and string[1].strip() == password:
            return True
    return False

def add_user(login, password):
    cursor = con.cursor()
    cursor.execute(
        "INSERT INTO Auth (Login, Password) VALUES (?,?)",
        login, password)
    con.commit()

def user_sign_up(login, password, name, surname, patronymic, birthday, phone_number, email):
    add_user(login, password)
    cursor = con.cursor()
    cursor.execute(
        "INSERT INTO Readers (Login, Name, Surname, Patronymic, Birth_Date, Contact_Number, Email) VALUES (?,?,?,?,?,?,?)",
        login, name, surname, patronymic, birthday, phone_number, email)
    con.commit()

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

def parse_row(table, column_key, key):
    cursor = con.cursor()
    cursor.execute("SELECT * FROM {} WHERE {} = '{}'".format(table, column_key, key))
    return cursor.fetchone()

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

def delete_book(id):
    cursor = con.cursor()
    cursor.execute("DELETE FROM Books WHERE Book_Id = {}".format(id))
    con.commit()