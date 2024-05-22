import base64
import re
import sys
from functools import reduce

import requests
import recources

from PIL import Image
from io import BytesIO
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6 import uic, QtWidgets, QtCore
from PyQt6.QtWidgets import QMainWindow, QDialog, QFileDialog, QLabel, QTableWidgetItem, QTableWidget
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
        icon = QIcon(":/images/images/icon.ico")
        self.setWindowIcon(icon)

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
        icon = QIcon(":/images/images/icon.ico")
        self.setWindowIcon(icon)

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


class BookRentWindow(QDialog):
    def __init__(self, book_info):
        super(BookRentWindow, self).__init__()
        uic.loadUi('Ui\\book_rent_window.ui', self)
        self.book_pushButton.clicked.connect(self.rent_book)
        self.current_book = book_info
        icon = QIcon(":/images/images/icon.ico")
        self.setWindowIcon(icon)
    def rent_book(self):
        requests.rent_book(self.current_book, Current_login)


class ClickableImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            book_info = requests.search_book(self.objectName())
            self.book_rent_window = BookRentWindow(book_info)
            self.book_rent_window.show()
            self.book_rent_window.book_name_label.setText(book_info[2])
            self.book_rent_window.author_label.setText(book_info[1])
            self.book_rent_window.date_label.setText(book_info[3])
            self.book_rent_window.description_plainTextEdit.setPlainText(book_info[5])
            self.book_rent_window.quantity_label.setText(str(book_info[6]))
            self.book_rent_window.library_label.setText(book_info[0])


class ChangePasswordWindow(QDialog):
    def __init__(self):
        super(ChangePasswordWindow, self).__init__()
        uic.loadUi('Ui\\change_password_window.ui', self)
        self.error_label.hide()
        self.pushButton.clicked.connect(self.password_change)
        icon = QIcon(":/images/images/icon.ico")
        self.setWindowIcon(icon)

    def password_change(self):
        if requests.auth(Current_login, self.current_pass_lineEdit.text()):
            requests.update_info('Auth', 'Password', 'Login', Current_login, self.new_pass_lineEdit.text())
            open_windows = app.topLevelWidgets()
            for window in open_windows:
                window.close()
            auth_window = SignInWindow()
            auth_window.show()


class ChangeLoginWindow(QDialog):
    def __init__(self):
        super(ChangeLoginWindow, self).__init__()
        uic.loadUi('Ui\\change_login_window.ui', self)
        self.error_label.hide()
        self.login_label.setText(Current_login)
        self.pushButton.clicked.connect(self.login_change)
        icon = QIcon(":/images/images/icon.ico")
        self.setWindowIcon(icon)
    def login_change(self):
        if requests.is_row_exist('Auth', 'Login', self.login_lineEdit.text()):
            self.error_label.setText('Этот логин уже занят!')
        else:
            if requests.auth(Current_login, self.password_lineEdit.text()):
                requests.update_info('Auth', 'Login', 'Login', Current_login, self.login_lineEdit.text())
                open_windows = app.topLevelWidgets()
                for window in open_windows:
                    window.close()
                auth_window = SignInWindow()
                auth_window.show()
            else:
                self.error_label.setText('Неверный пароль!')


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
        self.edit_library_action.triggered.connect(self.edit_lib)
        self.change_number_action.triggered.connect(self.change_num)
        self.reload_pushButton.clicked.connect(self.update_books)
        self.change_user_info_action.triggered.connect(self.change_user_info)
        self.delete_library_action.triggered.connect(self.delete_library)
        self.change_staff_info_action.triggered.connect(self.change_staff_info)
        self.change_login_action.triggered.connect(self.change_login)
        self.change_password_action.triggered.connect(self.change_password)
        self.add_library_action.triggered.connect(self.add_library)
        requests.del_expired_books()
        cur_lib = requests.select_libraries()[0]
        self.display_books(cur_lib)
        if info[0] == "Reader":
            self.menu.clear()
            self.menu.setTitle("")
            self.menu_2.clear()
            self.menu_2.setTitle("")
            self.menu_3.clear()
            self.menu_3.setTitle("")
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
        #books_dict = {}
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
            #books_dict[notes[book][1]] = notes[book][0]
            scaled_pixmap = pixmap.scaled(200, 313)
            img = ClickableImageLabel('label')
            stack = QtWidgets.QWidget()
            title = QtWidgets.QLabel(notes[book][2])
            stack_layout = QtWidgets.QVBoxLayout()
            stack_layout.addWidget(img)
            stack_layout.addWidget(title)
            stack.setLayout(stack_layout)
            layout.addWidget(stack, string, column, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
            img.setObjectName(str(notes[book][0]))
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
    def change_user_info(self):
        self.change_user_info_window = ChangeUserInfoWindow()
        self.change_user_info_window.show()
    def change_staff_info(self):
        self.change_staff_info_window = ChangeStaffInfoWindow()
        self.change_staff_info_window.show()
    def rent_book(self, book_info):
        self.book_rent_window = BookRentWindow()
        self.book_rent_window.show()
        self.book_rent_window.book_name_label.setText(book_info[2])

    def change_login(self):
        self.change_login_window = ChangeLoginWindow()
        self.change_login_window.show()

    def change_password(self):
        self.change_password_window = ChangePasswordWindow()
        self.change_password_window.show()

    def add_library(self):
        self.add_library_window = AddLibraryWindow()
        self.add_library_window.show()

    def delete_library(self):
        self.delete_library_window = DeleteLibraryWindow()
        self.delete_library_window.show()

    def edit_lib(self):
        self.edit_library_window = EditLibraryWindow()
        self.edit_library_window.show()

class ChangeUserInfoWindow(QDialog):
    def __init__(self):
        super(ChangeUserInfoWindow, self).__init__()
        uic.loadUi('Ui\\change_user_info_window.ui', self)
        self.applyButton.clicked.connect(self.change_data)
        icon = QIcon(":/images/images/icon.ico")
        self.setWindowIcon(icon)
        readers = requests.parse_notes("Readers")
        row = 0
        for user in readers:
            self.usersTable.insertRow(self.usersTable.rowCount())
            for column, value in enumerate(user):
                item = QTableWidgetItem(str(value).rstrip())
                if column == 0 or column == 1:
                    item.setFlags(Qt.ItemFlag.ItemIsEditable)
                self.usersTable.setItem(row, column, item)
            row +=1

    def change_data(self):
        all_rows = []
        num_rows = self.usersTable.rowCount()
        num_columns = self.usersTable.columnCount()
        for row in range(num_rows):
            current_row = []
            for column in range(num_columns):
                item = self.usersTable.item(row, column)
                if item is not None:
                    current_row.append(item.text())
                else:
                    current_row.append("")  # Если ячейка пуста, добавляем пустую строку
            all_rows.append(current_row)
        requests.update_users_info(all_rows)


class EditLibraryWindow(QDialog):
    def __init__(self):
        super(EditLibraryWindow, self).__init__()
        uic.loadUi('Ui\\changeLibraryInfo.ui', self)
        icon = QIcon(":/images/images/icon.ico")
        self.setWindowIcon(icon)
        self.library_comboBox.addItems(requests.select_libraries())
        self.library_comboBox.currentIndexChanged.connect(self.choose_lib)
        self.pushButton.clicked.connect(self.update_info)

    def choose_lib(self):
        lib_info = requests.parse_row("Libraries", "Library_Name", self.library_comboBox.currentText())
        if lib_info != None:
            self.adress_lineEdit.setText(lib_info[1].rstrip())
            open_time = QTime.fromString(lib_info[2][0:5], 'hh:mm')
            self.opening_timeEdit.setTime(open_time)
            close_time = QTime.fromString(lib_info[3][0:5], 'hh:mm')
            self.closing_timeEdit.setTime(close_time)
            self.phone_lineEdit.setText(lib_info[4])
            self.computer_class_checkBox.setChecked(bool(lib_info[5]))
            self.reading_room_checkBox.setChecked(bool(lib_info[6]))
        else:
            time = QTime.fromString('00:00', 'hh:mm')
            self.adress_lineEdit.clear()
            self.opening_timeEdit.setTime(time)
            self.closing_timeEdit.setTime(time)
            self.phone_lineEdit.clear()
            self.computer_class_checkBox.setChecked(False)
            self.reading_room_checkBox.setChecked(False)

    def update_info(self):
        requests.update_library_info(self.library_comboBox.currentText(),
                                     self.adress_lineEdit.text().rstrip(),
                                     self.opening_timeEdit.time().toString("HH:mm"),
                                     self.closing_timeEdit.time().toString("HH:mm"),
                                     self.phone_lineEdit.text().replace('(','').replace('-','').replace(')',''),
                                     str(self.computer_class_checkBox.isChecked()),
                                     str(self.reading_room_checkBox.isChecked()))

class DeleteLibraryWindow(QDialog):
    def __init__(self):
        super(DeleteLibraryWindow, self).__init__()
        uic.loadUi('Ui\\deleteLibraryWindow.ui', self)
        icon = QIcon(":/images/images/icon.ico")
        self.setWindowIcon(icon)
        self.del_pushButton.clicked.connect(self.delete)
        self.library_comboBox.addItems(requests.select_libraries())

    def delete(self):
        requests.del_library(self.library_comboBox.currentText())
        self.close()


class AddLibraryWindow(QDialog):
    def __init__(self):
        super(AddLibraryWindow, self).__init__()
        uic.loadUi('Ui\\addLibraryWindow.ui', self)
        icon = QIcon(":/images/images/icon.ico")
        self.setWindowIcon(icon)
        self.pushButton.clicked.connect(self.add_info)
        self.error_label.hide()
    def add_info(self):
        if (self.library_name_lineEdit.text() != '' and
            self.adress_lineEdit.text() != '' and
            len(self.phone_lineEdit.text()) == 17):
            requests.add_library(self.library_name_lineEdit.text(),
                                 self.adress_lineEdit.text(),
                                 self.open_timeEdit.time().toString("HH:mm"),
                                 self.close_timeEdit.time().toString("HH:mm"),
                                 self.phone_lineEdit.text().replace("-", "").replace("(", "").replace(")", ""),
                                 self.computer_class_checkBox.isChecked(),
                                 self.reading_room_checkBox.isChecked())
        else:
            self.error_label.setText("Заполните все поля!")

class ChangeStaffInfoWindow(QDialog):
    def __init__(self):
        super(ChangeStaffInfoWindow, self).__init__()
        uic.loadUi('Ui\\change_staff_info_window.ui', self)
        self.pushButton.clicked.connect(self.change_data)
        icon = QIcon(":/images/images/icon.ico")
        self.setWindowIcon(icon)
        readers = requests.parse_notes("Personal")
        row = 0
        for employee in readers:
            self.empoyeeTable.insertRow(self.empoyeeTable.rowCount())
            for column, value in enumerate(employee):
                item = QTableWidgetItem(str(value).rstrip())
                if column == 0 or column == 2 or column == 1:
                    item.setFlags(Qt.ItemFlag.ItemIsEditable)
                self.empoyeeTable.setItem(row, column, item)
            row +=1

    def change_data(self):
        all_rows = []
        num_rows = self.empoyeeTable.rowCount()
        num_columns = self.empoyeeTable.columnCount()
        for row in range(num_rows):
            current_row = []
            for column in range(num_columns):
                item = self.empoyeeTable.item(row, column)
                if item is not None:
                    current_row.append(item.text())
                else:
                    current_row.append("")  # Если ячейка пуста, добавляем пустую строку
            all_rows.append(current_row)
        requests.update_employee_info(all_rows)

class UserInfoWindow(QDialog):
    def __init__(self):
        super(UserInfoWindow, self).__init__()
        uic.loadUi('Ui\\user_info_window.ui', self)
        icon = QIcon(":/images/images/icon.ico")
        self.setWindowIcon(icon)
        if info[0] == "Personal":
            self.name_value_label.setText(info[1][3])
            self.surname_value_label.setText(info[1][4])
            self.patronymic_value_label.setText(info[1][5])
            self.library_email_value_label.setText(info[1][2])
            self.ticket_contract_number_value_label.setText(str(info[1][1]))
            self.ticket_contract_number_label.setText("Номер договора:")
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
        icon = QIcon(":/images/images/icon.ico")
        self.setWindowIcon(icon)

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
        icon = QIcon(":/images/images/icon.ico")
        self.setWindowIcon(icon)

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
        icon = QIcon(":/images/images/icon.ico")
        self.setWindowIcon(icon)
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