import sys
import sqlite3
import datetime
from PyQt5 import QtWidgets, QtCore

# Veritabanı işlemlerini yöneten sınıf
class DatabaseManager:
    def __init__(self, db_name='notlar.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        query = '''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            date TEXT
        )
        '''
        self.conn.execute(query)
        self.conn.commit()

    def add_note(self, title, content, date):
        query = 'INSERT INTO notes (title, content, date) VALUES (?, ?, ?)'
        cur = self.conn.cursor()
        cur.execute(query, (title, content, date))
        self.conn.commit()
        return cur.lastrowid

    def update_note(self, note_id, title, content, date):
        query = 'UPDATE notes SET title = ?, content = ?, date = ? WHERE id = ?'
        self.conn.execute(query, (title, content, date, note_id))
        self.conn.commit()

    def delete_note(self, note_id):
        query = 'DELETE FROM notes WHERE id = ?'
        self.conn.execute(query, (note_id,))
        self.conn.commit()

    def get_notes(self, search=""):
        # Arama metni varsa başlıkta arama yapıyoruz.
        if search:
            query = "SELECT id, title, content, date FROM notes WHERE title LIKE ? ORDER BY date DESC"
            return self.conn.execute(query, ('%' + search + '%',)).fetchall()
        else:
            query = "SELECT id, title, content, date FROM notes ORDER BY date DESC"
            return self.conn.execute(query).fetchall()

    def get_note_by_id(self, note_id):
        query = "SELECT id, title, content, date FROM notes WHERE id = ?"
        return self.conn.execute(query, (note_id,)).fetchone()


# Ana pencere ve arayüz tanımlaması
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()  # Veritabanı yöneticisi
        self.current_note_id = None  # Seçili notun id'si
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Not Tutma Uygulaması")

        # Ana widget ve düzen
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QtWidgets.QHBoxLayout()
        main_widget.setLayout(main_layout)

        # Sol tarafta sidebar oluşturuluyor
        sidebar = QtWidgets.QWidget()
        sidebar_layout = QtWidgets.QVBoxLayout()
        sidebar.setLayout(sidebar_layout)
        sidebar.setFixedWidth(250)

        # Arama çubuğu
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Arama...")
        self.search_bar.textChanged.connect(self.load_notes)

        # Not Ekle butonu
        self.add_button = QtWidgets.QPushButton("Not Ekle")
        self.add_button.clicked.connect(self.new_note)

        # Not başlıklarının listeleneceği liste widget'ı
        self.notes_list = QtWidgets.QListWidget()
        self.notes_list.itemClicked.connect(self.load_note_details)

        sidebar_layout.addWidget(self.search_bar)
        sidebar_layout.addWidget(self.add_button)
        sidebar_layout.addWidget(self.notes_list)

        # Sağ tarafta not detaylarının gösterileceği alan
        details_widget = QtWidgets.QWidget()
        details_layout = QtWidgets.QVBoxLayout()
        details_widget.setLayout(details_layout)

        # Not başlığı için düzenleme alanı
        self.title_edit = QtWidgets.QLineEdit()
        self.title_edit.setPlaceholderText("Başlık")

        # Not içeriği için düzenleme alanı
        self.content_edit = QtWidgets.QTextEdit()

        # Not tarihinin görüntüleneceği etiket
        self.date_label = QtWidgets.QLabel("Tarih: ")

        # İşlem butonları (Artık arşivle butonu bulunmuyor)
        button_layout = QtWidgets.QHBoxLayout()
        self.save_button = QtWidgets.QPushButton("Kaydet")
        self.save_button.clicked.connect(self.save_note)
        self.delete_button = QtWidgets.QPushButton("Sil")
        self.delete_button.clicked.connect(self.delete_note)

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.delete_button)

        # Detay alanına widget'ların eklenmesi
        details_layout.addWidget(self.title_edit)
        details_layout.addWidget(self.content_edit)
        details_layout.addWidget(self.date_label)
        details_layout.addLayout(button_layout)

        # Ana düzen: sol (sidebar) ve sağ (detaylar) ekleniyor
        main_layout.addWidget(sidebar)
        main_layout.addWidget(details_widget)

        # Not listesini yükle
        self.load_notes()

    def load_notes(self):
        """Veritabanından notları çekip liste widget'ına ekler."""
        search_text = self.search_bar.text()
        notes = self.db.get_notes(search_text)
        self.notes_list.clear()
        for note in notes:
            note_id, title, content, date = note
            item = QtWidgets.QListWidgetItem(title)
            # Notun id'sini saklamak için
            item.setData(QtCore.Qt.UserRole, note_id)
            self.notes_list.addItem(item)

    def load_note_details(self, item):
        """Listeden seçilen notun detaylarını sağdaki alana yükler."""
        note_id = item.data(QtCore.Qt.UserRole)
        note = self.db.get_note_by_id(note_id)
        if note:
            self.current_note_id, title, content, date = note
            self.title_edit.setText(title)
            self.content_edit.setPlainText(content)
            self.date_label.setText("Tarih: " + date)
        else:
            self.current_note_id = None

    def new_note(self):
        """Yeni not oluşturmak için alanları temizler."""
        self.current_note_id = None
        self.title_edit.clear()
        self.content_edit.clear()
        self.date_label.setText("Tarih: ")

    def save_note(self):
        """Notu veritabanına kaydeder (yeni not ekler veya günceller)."""
        title = self.title_edit.text()
        content = self.content_edit.toPlainText()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.current_note_id:
            self.db.update_note(self.current_note_id, title, content, now)
        else:
            self.current_note_id = self.db.add_note(title, content, now)
        self.date_label.setText("Tarih: " + now)
        self.load_notes()

    def delete_note(self):
        """Seçili notu veritabanından siler."""
        if self.current_note_id:
            self.db.delete_note(self.current_note_id)
            self.current_note_id = None
            self.title_edit.clear()
            self.content_edit.clear()
            self.date_label.setText("Tarih: ")
            self.load_notes()


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
