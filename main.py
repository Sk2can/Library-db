import base64
import re
import sys
from functools import reduce

import requests
import recources

from PIL import Image
from io import BytesIO
from PyQt6.QtCore import Qt, QDate
from PyQt6 import uic, QtWidgets, QtCore
from PyQt6.QtWidgets import QMainWindow, QDialog, QFileDialog, QLabel
from PyQt6.QtGui import QPixmap, QIcon

Current_login, info = "", ""


class SignInWindow(QMainWindow):
    def __init__(self):
        super(SignInWindow, self).__init__()
        uic.loadUi('Ui\\auth_window.ui', self)
        self.sign_up_label.setOpenExternalLinks(True)
        def mousePressEvent(event):
            self.sign_up_click()
        self.sign_up_label.mousePressEvent = mousePressEvent
        self.sign_in_button.clicked.connect(self.sign_in_click)

    def sign_in_click(self):
        global Current_login, info
        if requests.auth(self.login_lineEdit.text(), self.password_lineEdit.text()):
            Current_login = self.login_lineEdit.text()
            info = requests.parse_users(Current_login)
            self.main_window = MainWindow()
            self.main_window.show()
            self.close()
            self.main_window.Welcome_label.setText("Здравствуйте, " + str(requests.welcome(Current_login)).strip() + "!")
        else:
            self.error_label.setText("Веденные пароль или логин неверны!")
    def sign_up_click(self):
        self.sign_up_window = UserSignUpWindow()
        self.sign_up_window.show()
        self.close()


class UserSignUpWindow(QDialog):
    def __init__(self):
        super(UserSignUpWindow, self).__init__()
        uic.loadUi('Ui\\sign_up_window.ui', self)
        self.sign_up_pushButton.clicked.connect(self.data_check)

    def print_error(self,error_type):
        match error_type:
            case "phone":
                self.error_label.setText("Такой телефон уже зарегистрирован!")
            case "email":
                self.error_label.setText("Такая почта уже зарегистрирована!")
            case "login":
                self.error_label.setText("Такой логин уже зарегистрирован!")

    def data_check(self):
        phone_number = self.phone_number_lineEdit.text()
        rep = {'(': '', ')': '', '-': ''}
        rep = dict((re.escape(k), v) for k, v in rep.items())
        pattern = re.compile("|".join(rep.keys()))
        phone_number = pattern.sub(lambda m: rep[re.escape(m.group(0))], phone_number)
        if (self.login_lineEdit.text() != "" and self.password_lineEdit.text() != "" and
                self.password_confirm_lineEdit.text() != "" and self.name_label.text() != "" and
                self.surname_lineEdit.text() != "" and self.patronymic_lineEdit.text() != ""):
            if (self.password_lineEdit.text() ==  self.password_confirm_lineEdit.text()):
                if len(phone_number) == 12:
                    if requests.is_row_exist("Auth", "Login", self.login_lineEdit.text()):
                        self.print_error("login")
                        return
                    if requests.is_row_exist("Readers", "Contact_Number", phone_number):
                        self.print_error("phone")
                        return
                    if requests.is_row_exist("Readers", "Email", self.email_lineEdit.text()):
                        self.print_error("email")
                        return
                    requests.user_sign_up(self.login_lineEdit.text(),
                                          self.password_lineEdit.text(),
                                          self.name_lineEdit.text(),
                                          self.surname_lineEdit.text(),
                                          self.patronymic_lineEdit.text(),
                                          self.birthday_dateEdit.date().toString('yyyy-MM-dd'),
                                          phone_number,
                                          self.email_lineEdit.text())
                    self.close()
                    auth_window.show()

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('Ui\\main_window.ui', self)
        self.Exit_action.triggered.connect(self.exit)
        self.Info_action.triggered.connect(self.show_info)
        self.add_book_action.triggered.connect(self.add_book)
        self.remove_book_action.triggered.connect(self.remove_book)
        self.library_choose_comboBox.currentIndexChanged.connect(self.update_books)
        self.library_choose_comboBox.addItems(requests.select_libraries())
        self.change_number_action.triggered.connect(self.change_num)
        self.reload_pushButton.clicked.connect(self.update_books)
        cur_lib = requests.select_libraries()[0]
        self.display_books(cur_lib)
        if info[0] == "Reader":
            self.menu.clear()
            self.menu.setTitle("")
        icon = QIcon(":/images/images/icon.ico")  # указываем путь к иконке в формате ":/путь/к/ресурсу"
        #reload_ico = QPixmap(":/images/images/reload.ico")
        #self.reload_icon.setPixmap(reload_ico)
        self.setWindowIcon(icon)

    def update_books(self):
        selected_lib = self.library_choose_comboBox.currentText()
        self.display_books(selected_lib)

    def display_books(self, table):
        notes = requests.parse_notes("Books")
        layout = QtWidgets.QGridLayout()
        string = 0
        column = 0
        for book in range(requests.notes_count("Books")):
            note = notes[book][6]
            if notes[book][1].strip() != table.strip():
                continue
            pixmap = QPixmap()
            if note != None:
                image = Image.open(BytesIO(note))
                buffer = BytesIO()
                image.save(buffer, format="PNG")
                image_data = buffer.getvalue()
                pixmap.loadFromData(image_data)
            else:
                pixmap = QPixmap(":/images/images/default.png")
            scaled_pixmap = pixmap.scaled(200, 313)
            img = QtWidgets.QLabel('label')
            stack = QtWidgets.QWidget()
            title = QtWidgets.QLabel(notes[book][2])
            stack_layout = QtWidgets.QVBoxLayout()
            stack_layout.addWidget(img)
            stack_layout.addWidget(title)
            stack.setLayout(stack_layout)
            layout.addWidget(stack, string, column, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
            img.setPixmap(scaled_pixmap)
            column += 1
            if column == 3:
                string += 1
                column = 0
        scroll_widget = QtWidgets.QWidget()
        scroll_widget.setLayout(layout)
        self.scrollArea.setWidget(scroll_widget)
        self.scrollArea.setWidgetResizable(True)
        self.verticalLayout.addWidget(self.scrollArea)
        self.verticalLayout.setStretch(0, 1)
        self.verticalLayout.setStretch(1, 1)
        self.verticalLayout.setStretch(2, 10)
    def exit(self):
        self.auth_window = SignInWindow()
        app.closeAllWindows()
        self.auth_window.show()
    def show_info(self):
        self.user_info_window = UserInfoWindow()
        self.user_info_window.show()
    def change_num(self):
        self.change_number_of_books = ChangeNumberOfBooksWindow()
        self.change_number_of_books.show()
    def add_book(self):
        self.book_add_window = BookAddWindow()
        self.book_add_window.show()
    def remove_book(self):
        self.book_remove_window = BookRemoveWindow()
        self.book_remove_window.show()


class UserInfoWindow(QDialog):
    def __init__(self):
        super(UserInfoWindow, self).__init__()
        uic.loadUi('Ui\\user_info_window.ui', self)
        if info[0] == "Personal":
            self.name_value_label.setText(info[1][3])
            self.surname_value_label.setText(info[1][4])
            self.patronymic_value_label.setText(info[1][5])
            self.library_email_value_label.setText(info[1][2])
            self.ticket_contract_number_value_label.setText(info[1][1])
            self.pasport_phone_value_label.setText(info[1][6])
            self.SNILS_birthdate_value_label.setText(info[1][7])
            self.INN_value_label.setText(info[1][8])
        else:
            self.INN_value_label.hide()
            self.INN_label.hide()
            self.name_value_label.setText(info[1][2])
            self.surname_value_label.setText(info[1][3])
            self.patronymic_value_label.setText(info[1][4])
            self.library_email_value_label.setText(info[1][7])
            self.library_email_label.setText("Почта:")
            self.ticket_contract_number_value_label.setText(str(info[1][1]))
            self.ticket_contract_number_label.setText("Номер билета:")
            self.pasport_phone_value_label.setText(info[1][6])
            self.pasport_phone_label.setText("Телефон:")
            self.SNILS_birthdate_value_label.setText(info[1][5])
            self.SNILS_birthdate_label.setText("Дата рождения:")


class BookAddWindow(QDialog):
    def __init__(self):
        super(BookAddWindow, self).__init__()
        uic.loadUi('Ui\\book_add_window.ui', self)
        self.Library_comboBox.addItems(requests.select_libraries())
        self.Add_pushButton.clicked.connect(self.add)
        self.Image_pushButton.clicked.connect(self.browsefiles)
    def browsefiles(self):
        fname = QFileDialog.getOpenFileName(self, "Выбор картинки", "C:\\Users\\khmel\\Desktop\\6 семестр\\СУБД\\LibraryProject\\images", "Image Files (*.png *.jpg *.jpeg)")
        self.Image_lineEdit.setText(fname[0])
    def add(self):
        if (self.Library_comboBox.currentIndex() != 0 and self.Title_lineEdit.text() != "" and
                self.Author_lineEdit.text() != "" and self.Language_lineEdit.text() != "" and
                self.Release_dateEdit.text() != ""):
            requests.add_book(self.Library_comboBox.currentText(), self.Title_lineEdit.text(), self.Author_lineEdit.text(),
                      self.Release_dateEdit.date().toString("yyyy-MM-dd"), self.Language_lineEdit.text(),
                      self.Image_lineEdit.text(), self.Description_plainTextEdit.toPlainText(),
                      self.quantity_spinBox.value())
            self.Library_comboBox.setCurrentIndex(0)
            self.Title_lineEdit.clear()
            self.Author_lineEdit.clear()
            self.Language_lineEdit.clear()
            self.Image_lineEdit.clear()
            self.Description_plainTextEdit.clear()
            self.Release_dateEdit.setDate(QDate(2000, 1, 31))
            self.erorr_label.clear()
        else:
            self.erorr_label.setText("Заполните все обязательные поля!")


class BookRemoveWindow(QDialog):
    def __init__(self):
        super(BookRemoveWindow, self).__init__()
        uic.loadUi('Ui\\book_remove_window.ui', self)
        self.Library_comboBox.addItems(requests.select_libraries())
        self.Library_comboBox.currentTextChanged.connect(self.change_books_list)
        self.error_label.hide()

    def change_books_list(self):
        self.book_comboBox.clear()
        self.book_comboBox.insertItem(0,'')
        lib = self.Library_comboBox.currentText()
        self.book_comboBox.addItems(requests.select_books(lib))
        self.delete_pushButton.clicked.connect(self.delete)

    def delete(self):
        if self.book_comboBox.currentText() != "":
            requests.delete_book(id=self.get_id())
            self.Library_comboBox.setCurrentIndex(0)
            self.error_label.hide()
        else:
            self.error_label.show()

    def get_id(self):
        lib = self.Library_comboBox.currentText()
        book = self.book_comboBox.currentText()
        notes = requests.parse_notes("Books")
        id = 1
        for note in notes:
            if note[1].strip() == lib.strip() and note[2].strip() == book.strip():
                id = note[0]
                break
        return id


class ChangeNumberOfBooksWindow(QDialog):
    def __init__(self):
        super(ChangeNumberOfBooksWindow, self).__init__()
        uic.loadUi('Ui\\number_of_books_window.ui', self)
        self.quantity_spinBox.clear()
        self.Library_comboBox.addItems(requests.select_libraries())
        self.Library_comboBox.currentTextChanged.connect(self.change_books_list)
        self.book_comboBox.textActivated.connect(self.show_quantity)
        self.change_pushButton.clicked.connect(lambda: requests.change_quantity(id=self.get_id(), quantity=self.quantity_spinBox.value()))

    def get_id(self):
        lib = self.Library_comboBox.currentText()
        book = self.book_comboBox.currentText()
        notes = requests.parse_notes("Books")
        id = 1
        for note in notes:
            if note[1].strip() == lib.strip() and note[2].strip() == book.strip():
                id = note[0]
                break
        return id

    def change_books_list(self):
        self.quantity_spinBox.clear()
        self.book_comboBox.clear()
        self.book_comboBox.insertItem(0,'')
        lib = self.Library_comboBox.currentText()
        self.book_comboBox.addItems(requests.select_books(lib))

    def show_quantity(self):
        if self.book_comboBox.currentIndex() == 0:
            self.quantity_spinBox.clear()
            return
        id = self.get_id()
        self.quantity_spinBox.setValue(requests.parse_quantity(id))


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    auth_window = SignInWindow()  # Создаём объект класса ExampleApp
    auth_window.show()  # Показываем окно
    app.exec()  # и запускаем приложение