import sys
import sqlite3
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget,
                             QDialog, QLabel, QLineEdit, QComboBox, QPushButton, QFormLayout,
                             QMessageBox, QHeaderView, QAbstractItemView, QHBoxLayout, QMenu)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QFont, QIcon, QPixmap, QAction
from PyQt6.QtCore import Qt

APP_STYLE = """
    QMainWindow { 
        background-color: #FFFFFF; 
        font-family: "Constantia";
    }
    QTableView { 
        background-color: #BFD6F6; 
        gridline-color: #405C73;
        selection-background-color: #1D476B;
        selection-color: white;
    }
    QHeaderView::section { 
        background-color: #405C73; 
        color: white;
        padding: 4px;
        font-weight: bold;
    }
    QPushButton {
        background-color: #405C73;
        color: white;
        padding: 5px;
        border-radius: 3px;
    }
    QPushButton:hover {
        background-color: #1D476B;
    }
    QLineEdit, QComboBox {
        padding: 3px;
        border: 1px solid #BFD6F6;
        border-radius: 3px;
    }
    QLabel {
        font-weight: bold;
        color: #1D476B;
    }
"""


class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect('obraz_plus.db')

    def get_materials(self):
        query = """
                SELECT m.id,
                       m.name,
                       mt.name                                AS type_name,
                       m.stock_quantity,
                       m.min_quantity,
                       COALESCE(SUM(pm.required_quantity), 0) AS required_qty,
                       mt.id                                  AS type_id
                FROM Materials m
                         LEFT JOIN MaterialTypes mt ON m.type_id = mt.id
                         LEFT JOIN ProductMaterials pm ON m.id = pm.material_id
                GROUP BY m.id, mt.name
                """
        cursor = self.conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def get_material_types(self):
        query = 'SELECT id, name FROM MaterialTypes'
        cursor = self.conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def get_material_by_id(self, material_id):
        query = "SELECT * FROM Materials WHERE id = ?"
        cursor = self.conn.cursor()
        cursor.execute(query, (material_id,))
        return cursor.fetchone()

    def save_material(self, material_id, data):
        try:
            cursor = self.conn.cursor()
            if material_id:
                query = """
                        UPDATE Materials
                        SET name             = ?,
                            type_id          = ?,
                            unit_price       = ?,
                            stock_quantity   = ?,
                            min_quantity     = ?,
                            package_quantity = ?,
                            unit_of_measure  = ?
                        WHERE id = ?
                        """
                cursor.execute(query, (*data, material_id))
            else:
                query = """
                        INSERT INTO Materials
                        (name, type_id, unit_price, stock_quantity,
                         min_quantity, package_quantity, unit_of_measure)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """
                cursor.execute(query, data)
            self.conn.commit()
            return True
        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Ошибка сохранения: {str(e)}")
            return False

    def get_products_by_material(self, material_id):
        query = """
                SELECT p.name, pm.required_quantity, pt.coefficient
                FROM Products p
                         JOIN ProductMaterials pm ON p.id = pm.product_id
                         JOIN ProductTypes pt ON p.type_id = pt.id
                WHERE pm.material_id = ?
                """
        cursor = self.conn.cursor()
        cursor.execute(query, (material_id,))
        return cursor.fetchall()

    def calculate_product_quantity(self, product_type_id, material_type_id, raw_quantity, param1, param2):
        """Расчет количества продукции из сырья с учетом потерь"""
        try:
            cursor = self.conn.cursor()

            cursor.execute('SELECT coefficient FROM ProductTypes WHERE id = ?', (product_type_id,))
            product_coeff = cursor.fetchone()[0]

            cursor.execute('SELECT loss_percentage FROM MaterialTypes WHERE id = ?', (material_type_id,))
            loss_percent = cursor.fetchone()[0]

            raw_per_unit = param1 * param2 * product_coeff
            effective_raw = raw_quantity * (1 - loss_percent / 100)
            product_quantity = effective_raw / raw_per_unit

            return int(product_quantity) if product_quantity >= 0 else -1
        except Exception as e:
            print(f"Ошибка расчета: {e}")
            return -1


class MaterialModel(QStandardItemModel):
    def __init__(self, data, headers, parent=None):
        super().__init__(parent)
        self.setHorizontalHeaderLabels(headers)
        self.load_data(data)

    def load_data(self, data):
        self.setRowCount(0)
        for row_data in data:
            row_items = []
            for item in row_data[1:-1]:  # Пропускаем ID и type_id
                cell = QStandardItem(str(item))
                cell.setEditable(False)
                row_items.append(cell)
            self.appendRow(row_items)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление материалами")
        self.setWindowIcon(QIcon('Образ плюс.ico'))
        self.setGeometry(100, 100, 1000, 600)
        self.setStyleSheet(APP_STYLE)
        self.db = DatabaseManager()
        self.init_ui()
        self.load_materials()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Заголовок с логотипом
        header_layout = QHBoxLayout()
        logo_label = QLabel()
        logo_pixmap = QPixmap('Образ плюс.png').scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio)
        logo_label.setPixmap(logo_pixmap)
        header_layout.addWidget(logo_label)
        title_label = QLabel("Образ Плюс - Управление материалами")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1D476B;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Таблица материалов
        self.table = QTableView()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.doubleClicked.connect(self.edit_material)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Включаем контекстное меню
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.table)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Добавить материал")
        add_btn.clicked.connect(self.add_material)
        btn_layout.addWidget(add_btn)
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_materials)
        btn_layout.addWidget(refresh_btn)
        layout.addLayout(btn_layout)

    def show_context_menu(self, position):
        menu = QMenu()
        view_products_action = QAction("Просмотреть продукцию", self)
        view_products_action.triggered.connect(self.view_products_for_selected)
        menu.addAction(view_products_action)
        menu.exec(self.table.viewport().mapToGlobal(position))

    def view_products_for_selected(self):
        selected = self.table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            material_data = self.db.get_materials()[row]
            material_id = material_data[0]
            material_name = material_data[1]

            # Получаем данные для расчета
            material_type_id = material_data[-1]  # Последний элемент - type_id
            stock_quantity = material_data[3]

            dialog = ProductListDialog(self.db, material_id, material_name, material_type_id, stock_quantity)
            dialog.exec()

    def load_materials(self):
        data = self.db.get_materials()
        headers = ["Материал", "Тип материала", "На складе", "Мин. кол-во", "Требуется"]
        self.model = MaterialModel(data, headers)
        self.table.setModel(self.model)

    def add_material(self):
        dialog = MaterialEditDialog(self.db)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_materials()

    def edit_material(self, index):
        material_id = self.db.get_materials()[index.row()][0]
        dialog = MaterialEditDialog(self.db, material_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_materials()


class MaterialEditDialog(QDialog):
    def __init__(self, db, material_id=None):
        super().__init__()
        self.db = db
        self.material_id = material_id
        self.setWindowIcon(QIcon('Образ плюс.ico'))
        title = "Редактирование материала" if material_id else "Новый материал"
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 350)
        self.init_ui()
        if material_id:
            self.load_data()

    def init_ui(self):
        layout = QFormLayout(self)
        self.name_edit = QLineEdit()
        self.type_combo = QComboBox()
        self.price_edit = QLineEdit()
        self.stock_edit = QLineEdit()
        self.min_edit = QLineEdit()
        self.package_edit = QLineEdit()
        self.unit_edit = QLineEdit()

        types = self.db.get_material_types()
        for type_id, type_name in types:
            self.type_combo.addItem(type_name, type_id)

        layout.addRow("Наименование:", self.name_edit)
        layout.addRow("Тип материала:", self.type_combo)
        layout.addRow("Цена единицы:", self.price_edit)
        layout.addRow("Количество на складе:", self.stock_edit)
        layout.addRow("Минимальное количество:", self.min_edit)
        layout.addRow("Количество в упаковке:", self.package_edit)
        layout.addRow("Единица измерения:", self.unit_edit)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save_material)
        btn_layout.addWidget(save_btn)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def load_data(self):
        material = self.db.get_material_by_id(self.material_id)
        if material:
            self.name_edit.setText(material[1])
            for index in range(self.type_combo.count()):
                if self.type_combo.itemData(index) == material[2]:
                    self.type_combo.setCurrentIndex(index)
                    break
            self.price_edit.setText(str(material[3]))
            self.stock_edit.setText(str(material[4]))
            self.min_edit.setText(str(material[5]))
            self.package_edit.setText(str(material[6]))
            self.unit_edit.setText(material[7])

    def save_material(self):
        try:
            name = self.name_edit.text().strip()
            if not name:
                raise ValueError("Наименование не может быть пустым")

            type_id = self.type_combo.currentData()
            unit_price = float(self.price_edit.text())
            stock_quantity = float(self.stock_edit.text())
            min_quantity = float(self.min_edit.text())
            package_quantity = float(self.package_edit.text())
            unit_of_measure = self.unit_edit.text().strip()

            if unit_price < 0:
                raise ValueError("Цена не может быть отрицательной")
            if min_quantity < 0:
                raise ValueError("Минимальное количество не может быть отрицательным")
            if not unit_of_measure:
                raise ValueError("Укажите единицу измерения")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            return

        data = (
            name, type_id, unit_price,
            stock_quantity, min_quantity,
            package_quantity, unit_of_measure
        )

        if self.db.save_material(self.material_id, data):
            self.accept()


class ProductListDialog(QDialog):
    def __init__(self, db, material_id, material_name, material_type_id, stock_quantity):
        super().__init__()
        self.db = db
        self.material_type_id = material_type_id
        self.stock_quantity = stock_quantity
        self.setWindowTitle(f"Продукция для: {material_name}")
        self.setWindowIcon(QIcon('Образ плюс.ico'))
        self.setFixedSize(800, 500)

        layout = QVBoxLayout(self)

        # Параметры для расчета
        self.param1_edit = QLineEdit("1.0")
        self.param2_edit = QLineEdit("1.0")

        params_layout = QHBoxLayout()
        params_layout.addWidget(QLabel("Параметр 1:"))
        params_layout.addWidget(self.param1_edit)
        params_layout.addWidget(QLabel("Параметр 2:"))
        params_layout.addWidget(self.param2_edit)

        calculate_btn = QPushButton("Рассчитать возможное количество")
        calculate_btn.clicked.connect(self.calculate_quantities)

        layout.addLayout(params_layout)
        layout.addWidget(calculate_btn)

        # Таблица продукции
        self.table = QTableView()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.load_data(material_id)

    def load_data(self, material_id):
        data = self.db.get_products_by_material(material_id)
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["Продукция", "Требуемое количество", "Коэффициент", "Расчетное количество"])

        for product_name, required_qty, coefficient in data:
            row = [
                QStandardItem(product_name),
                QStandardItem(str(required_qty)),
                QStandardItem(str(coefficient)),
                QStandardItem("")  # Пока пусто, заполнится после расчета
            ]
            model.appendRow(row)

        self.table.setModel(model)

    def calculate_quantities(self):
        try:
            param1 = float(self.param1_edit.text())
            param2 = float(self.param2_edit.text())

            model = self.table.model()
            for row in range(model.rowCount()):
                product_name = model.item(row, 0).text()
                required_qty = float(model.item(row, 1).text())
                product_coeff = float(model.item(row, 2).text())

                # Получаем product_type_id (здесь упрощенно, в реальности нужно запрашивать из БД)
                # В реальном приложении нужно добавить запрос к БД для получения product_type_id
                product_type_id = 1  # Заглушка, нужно реализовать правильный запрос

                # Расчет количества продукции
                quantity = self.db.calculate_product_quantity(
                    product_type_id,
                    self.material_type_id,
                    self.stock_quantity,
                    param1,
                    param2
                )

                # Обновляем таблицу
                model.setItem(row, 3, QStandardItem(str(quantity)))

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", "Введите корректные числовые параметры")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('Образ плюс.ico'))
    font = QFont("Constantia", 10)
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())