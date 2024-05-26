import base64
import csv
import re
import sys
from datetime import datetime
from functools import reduce
import requests
import recources
from PIL import Image
from io import BytesIO
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6 import uic, QtWidgets, QtCore
from PyQt6.QtWidgets import QMainWindow, QDialog, QFileDialog, QLabel, QTableWidgetItem, QTableWidget, QPushButton, \
    QMessageBox
from PyQt6.QtGui import QPixmap, QIcon, QAction, QColor

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
        icon = QIcon(":/images/icon.ico")
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
        icon = QIcon(":/images/icon.ico")
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
    def __init__(self, book_info, main_window):
        super(BookRentWindow, self).__init__()
        self.main_window = main_window
        uic.loadUi('Ui\\book_rent_window.ui', self)
        self.book_pushButton.clicked.connect(self.rent_book)
        self.current_book = book_info
        icon = QIcon(":/images/icon.ico")
        self.setWindowIcon(icon)
        if requests.is_row_exist('Personal', 'Login', Current_login):
            self.book_pushButton.hide()
    def rent_book(self):
        requests.rent_book(self.current_book, Current_login)
        self.close()
        self.main_window.update_books()


class ClickableImageLabel(QLabel):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            book_info = requests.search_book(self.objectName())
            self.book_rent_window = BookRentWindow(book_info, self.main_window)
            self.book_rent_window.show()
            self.book_rent_window.book_name_label.setText(book_info[2].rstrip())
            self.book_rent_window.author_label.setText(book_info[1])
            self.book_rent_window.date_label.setText(book_info[3])
            self.book_rent_window.description_plainTextEdit.setPlainText(book_info[5])
            self.book_rent_window.quantity_label.setText(str(book_info[6]))
            self.book_rent_window.library_label.setText(book_info[0])


class RentButton(QPushButton):
    def __init__(self,table, window, parent=None):
        super().__init__(parent)
        self.table = table
        self.window = window

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            row = int(self.objectName())
            requests.unrent_book(int(self.table.item(row, 6).text()))
            self.table.setRowCount(0)
            self.window.show_rent()


class ChangePasswordWindow(QDialog):
    def __init__(self):
        super(ChangePasswordWindow, self).__init__()
        uic.loadUi('Ui\\change_password_window.ui', self)
        self.error_label.hide()
        self.pushButton.clicked.connect(self.password_change)
        icon = QIcon(":/images/icon.ico")
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
        icon = QIcon(":/images/icon.ico")
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
        self.add_staff_action.triggered.connect(self.staff_sign_up)
        self.change_staff_info_action.triggered.connect(self.change_staff_info)
        self.account_del_action.triggered.connect(self.del_acc)
        self.change_login_action.triggered.connect(self.change_login)
        self.change_password_action.triggered.connect(self.change_password)
        self.add_library_action.triggered.connect(self.add_library)
        self.menu_5 = QAction("Список взятых книг", self.menuBar)
        self.menu_5.setObjectName("menu_5")
        self.menuBar.addAction(self.menu_5)
        self.menu_5.triggered.connect(self.show_rented_books)
        self.debt_label.setText("У вас нет задолженностей.")
        debt = requests.show_expired_books(Current_login)
        if debt > 0:
            self.debt_label.setText("У вас есть долг по несданным книгам: {}".format(debt))
            self.debt_label.setStyleSheet("color: red;")
            self.debt_label.show()
        cur_lib = requests.select_libraries()[0]
        self.display_books(cur_lib)
        if info[0] == "Reader":
            self.menu.clear()
            self.menu.setTitle("")
            self.menu_2.clear()
            self.menu_2.setTitle("")
            self.menu_3.clear()
            self.menu_3.setTitle("")
        icon = QIcon(":/images/icon.ico")  # указываем путь к иконке в формате ":/путь/к/ресурсу"
        #reload_ico = QPixmap(":/images/images/reload.ico")
        #self.reload_icon.setPixmap(reload_ico)
        if (requests.is_row_exist('Personal', 'Login', Current_login)):
            self.debt_label.setText('')
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
            if notes[book][1].strip() != table.strip() or notes[book][8] == 0:
                continue
            pixmap = QPixmap()
            if note != None:
                image = Image.open(BytesIO(note))
                buffer = BytesIO()
                image.save(buffer, format="PNG")
                image_data = buffer.getvalue()
                pixmap.loadFromData(image_data)
            else:
                pixmap = QPixmap(":/images/default.png")
            #books_dict[notes[book][1]] = notes[book][0]
            scaled_pixmap = pixmap.scaled(200, 313)
            img = ClickableImageLabel(self, 'label')
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

    def del_acc(self):
        self.del_acc_window = DeleteAccountWindow()
        self.del_acc_window.show()

    def show_rented_books(self):
        self.show_rented_books_window = ShowRentedBooksWindow()
        self.show_rented_books_window.show()

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

    def staff_sign_up(self):
        self.staff_sign_up_window = StaffSignUp()
        self.staff_sign_up_window.show()


class DeleteAccountWindow(QDialog):
    def __init__(self):
        super(DeleteAccountWindow, self).__init__()
        uic.loadUi('Ui\\account_delete_window.ui', self)
        icon = QIcon(":/images/icon.ico")
        self.setWindowIcon(icon)
        self.error_label.hide()
        self.del_pushButton.clicked.connect(self.delete)

    def on_button_click(self):
        requests.delete_user(Current_login)
        app.closeAllWindows()
        app.exit()

    def delete(self):
        if requests.auth(Current_login, self.password_lineEdit.text()):
            if (requests.is_row_exist('Auth', 'Login', Current_login)):
                alert = QMessageBox()
                icon = QIcon(":/images/icon.ico")
                alert.setWindowIcon(icon)
                alert.setText("Вы действительно хотите удалить свой аккаунт?")
                alert.setWindowTitle("Осторожно!")
                alert.setStandardButtons(QMessageBox.StandardButton.Ok)
                button = alert.button(QMessageBox.StandardButton.Ok)
                button.setText('Подтвердить')
                button.clicked.connect(self.on_button_click)
                alert.exec()
        else:
            self.error_label.setText("Неверный пароль!")
            self.error_label.show()


class StaffSignUp(QDialog):
    def __init__(self):
        super(StaffSignUp, self).__init__()
        uic.loadUi('Ui\\add_staff_window.ui', self)
        icon = QIcon(":/images/icon.ico")
        self.setWindowIcon(icon)
        self.pushButton.clicked.connect(self.data_check)
        self.comboBox.addItems(requests.select_libraries())

    def data_check(self):
        passport_number = self.passport_lineEdit.text()
        rep = {' ': '', '-': ''}
        rep = dict((re.escape(k), v) for k, v in rep.items())
        pattern = re.compile("|".join(rep.keys()))
        passport_number = pattern.sub(lambda m: rep[re.escape(m.group(0))], passport_number)
        snils_number = pattern.sub(lambda m: rep[re.escape(m.group(0))], self.SNILS_lineEdit.text())
        
        if (self.login_lineEdit.text() != "" and self.password_lineEdit.text() != "" and
                self.password_confirm_lineEdit.text() != "" and self.name_lineEdit.text() != "" and
                self.surname_lineEdit.text() != "" and self.patronymic_lineEdit.text() != "" and
                passport_number != "" and snils_number != "" and self.INN_lineEdit.text() != "" and
                self.comboBox.currentText() != ""):
            if (self.password_lineEdit.text() == self.password_confirm_lineEdit.text()):
                if len(passport_number) == 10:
                    if requests.is_row_exist("Auth", "Login", self.login_lineEdit.text()):
                        self.print_error("login")
                        return
                    if requests.is_row_exist("Personal", "Passport_Number", passport_number):
                        self.print_error("passport")
                        return
                    if requests.is_row_exist("Personal", "SNILS_Number", snils_number):
                        self.print_error("snils")
                        return
                    if requests.is_row_exist("Personal", "INN_Number", self.INN_lineEdit.text()):
                        self.print_error("inn")
                        return
                    requests.personal_sign_up(self.comboBox.currentText(),
                                              self.login_lineEdit.text(),
                                              self.password_lineEdit.text(),
                                              self.name_lineEdit.text(),
                                              self.surname_lineEdit.text(),
                                              self.patronymic_lineEdit.text(),
                                              passport_number,
                                              snils_number,
                                              self.INN_lineEdit.text())
                    self.close()
            else:
                self.print_error("pass")
        else:
            self.print_error("miss")

    def print_error(self,error_type):
        match error_type:
            case "pass":
                self.error_label.setText("Введенные пароли не совпадают!")
            case "phone":
                self.error_label.setText("Такой телефон уже зарегистрирован!")
            case "email":
                self.error_label.setText("Такая почта уже зарегистрирована!")
            case "login":
                self.error_label.setText("Такой логин уже зарегистрирован!")
            case "miss":
                self.error_label.setText("Заполните все поля!")
            case "snils":
                self.error_label.setText("Данный номер СНИЛС уже зарегистрирован!")
            case "inn":
                self.error_label.setText("Данный номер ИНН уже зарегистрирован!")


class ShowRentedBooksWindow(QDialog):
    def __init__(self):
        super(ShowRentedBooksWindow, self).__init__()
        uic.loadUi('Ui\\unrent_window.ui', self)
        icon = QIcon(":/images/icon.ico")
        self.setWindowIcon(icon)
        self.export_pushButton.clicked.connect(self.exportToCSV)
        self.show_rent()

    def show_rent(self):
        if not(requests.is_row_exist('Personal', 'Login', Current_login)):
            for col in range(5):
                self.rent_tableWidget.removeColumn(3)
        #rented_books = requests.parse_notes("Rented_books")
        join_table = requests.join_rented_books()
        row = 0
        for book in join_table:
            self.rent_tableWidget.insertRow(self.rent_tableWidget.rowCount())
            for column, value in enumerate(book):
                item = QTableWidgetItem(str(value).rstrip())
                if column == 3 and requests.is_row_exist('Personal', 'Login', Current_login):
                    cleaned_text = ' '.join(value.split())
                    item = QTableWidgetItem(str(cleaned_text))
                if (column == 3 or column == 4 or column == 5) and not(requests.is_row_exist('Personal', 'Login', Current_login)):
                    continue
                if column == 2:
                    current_datetime = datetime.now()
                    if current_datetime > value:
                        value = value.strftime('%d-%m-%Y')
                        item = QTableWidgetItem(str(value).rstrip())
                        item.setForeground(QColor(255, 0, 0))
                        self.rent_tableWidget.setItem(row, column, item)
                        continue
                    value = value.strftime('%d-%m-%Y')
                    item = QTableWidgetItem(str(value).rstrip())
                    item.setForeground(QColor(0, 0, 0))
                self.rent_tableWidget.setItem(row, column, item)
            button = RentButton(self.rent_tableWidget, self)
            icon = QIcon(':/images/check.ico')
            button.setIcon(icon)
            button.setObjectName(str(row))
            self.rent_tableWidget.setCellWidget(row, 7, button)
            row += 1

    def exportToCSV(self):
        ind = 0
        if requests.is_row_exist('Personal', 'Login', Current_login):
            ind = 1
        else:
            ind = 0
        with open('table_data.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            for row in range(self.rent_tableWidget.rowCount()):
                row_data = []
                for column in range(self.rent_tableWidget.columnCount() - ind):
                    item = self.rent_tableWidget.item(row, column)
                    row_data.append(item.text())
                writer.writerow(row_data)


class ChangeUserInfoWindow(QDialog):
    def __init__(self):
        super(ChangeUserInfoWindow, self).__init__()
        uic.loadUi('Ui\\change_user_info_window.ui', self)
        self.applyButton.clicked.connect(self.change_data)
        icon = QIcon(":/images/icon.ico")
        self.setWindowIcon(icon)
        readers = requests.parse_notes("Readers")
        row = 0
        for user in readers:
            self.usersTable.insertRow(self.usersTable.rowCount())
            for column, value in enumerate(user):
                item = QTableWidgetItem(str(value).rstrip())
                if column == 0 or column == 1:
                    item.setFlags(Qt.ItemFlag.ItemIsEditable)
                if column == 5:
                    value = datetime.strptime(value, '%Y-%m-%d')
                    new_date_str = value.strftime('%d.%m.%Y')
                    item = QTableWidgetItem(str(new_date_str).rstrip())
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
        icon = QIcon(":/images/icon.ico")
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
        icon = QIcon(":/images/icon.ico")
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
        icon = QIcon(":/images/icon.ico")
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
        icon = QIcon(":/images/icon.ico")
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
        icon = QIcon(":/images/icon.ico")
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
            value = datetime.strptime(info[1][5], '%Y-%m-%d')
            new_date_str = value.strftime('%d.%m.%Y')
            self.SNILS_birthdate_value_label.setText(new_date_str)
            self.SNILS_birthdate_label.setText("Дата рождения:")


class BookAddWindow(QDialog):
    def __init__(self):
        super(BookAddWindow, self).__init__()
        uic.loadUi('Ui\\book_add_window.ui', self)
        self.Library_comboBox.addItems(requests.select_libraries())
        self.Add_pushButton.clicked.connect(self.add)
        self.Image_pushButton.clicked.connect(self.browsefiles)
        icon = QIcon(":/images/icon.ico")
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
        icon = QIcon(":/images/icon.ico")
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
        icon = QIcon(":/images/icon.ico")
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