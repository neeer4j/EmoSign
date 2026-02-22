"""
Admin Page
Built-in dashboard for the 'admin' user to manage the application.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QMessageBox, QTextEdit, QLineEdit, QDialog, QFormLayout,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from ui.styles import COLORS


class StatCard(QFrame):
    """A compact stat card for the admin dashboard header."""
    
    def __init__(self, icon, title, value="0", accent=None, parent=None):
        super().__init__(parent)
        accent = accent or COLORS['primary']
        self.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 14px;
                border-left: 4px solid {accent};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)
        
        top_row = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 22px; background: transparent;")
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 12px; font-weight: 600;
            color: {COLORS['text_muted']};
            letter-spacing: 0.5px; background: transparent;
        """)
        top_row.addWidget(icon_label)
        top_row.addWidget(title_label)
        top_row.addStretch()
        layout.addLayout(top_row)
        
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet(f"""
            font-size: 28px; font-weight: 800;
            color: {accent};
            background: transparent;
        """)
        layout.addWidget(self.value_label)
    
    def set_value(self, value):
        self.value_label.setText(str(value))


class AdminPage(QWidget):
    """Admin dashboard widget."""
    
    def __init__(self, db_service=None, parent=None):
        super().__init__(parent)
        self.db = db_service
        self._setup_ui()
        
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        header.setSpacing(12)
        
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("🛡️ Admin Dashboard")
        title.setStyleSheet(f"""
            font-size: 26px; font-weight: 800;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        subtitle = QLabel("Manage users, translations, and system data")
        subtitle.setStyleSheet(f"""
            font-size: 13px; color: {COLORS['text_muted']};
            background: transparent;
        """)
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header.addLayout(title_col)
        header.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 13px; font-weight: 700;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """)
        refresh_btn.clicked.connect(self.refresh_all)
        header.addWidget(refresh_btn, alignment=Qt.AlignVCenter)
        main_layout.addLayout(header)
        
        # Stat cards row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)
        
        self.stat_users = StatCard("👥", "TOTAL USERS", "0", COLORS['primary'])
        self.stat_translations = StatCard("📜", "TRANSLATIONS", "0", COLORS['success'])
        self.stat_recent = StatCard("🕐", "RECENT (24h)", "0", COLORS['warning'])
        
        stats_row.addWidget(self.stat_users)
        stats_row.addWidget(self.stat_translations)
        stats_row.addWidget(self.stat_recent)
        main_layout.addLayout(stats_row)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS['border']};
                background: {COLORS['bg_card']};
                border-radius: 12px;
                padding: 8px;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {COLORS['text_muted']};
                padding: 10px 24px;
                font-size: 13px; font-weight: 600;
                border: none;
                border-bottom: 2px solid transparent;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                color: {COLORS['primary']};
                border-bottom: 2px solid {COLORS['primary']};
            }}
            QTabBar::tab:hover {{
                color: {COLORS['text_primary']};
            }}
        """)
        
        self.users_tab = QWidget()
        self._setup_users_tab()
        
        self.trans_tab = QWidget()
        self._setup_trans_tab()
        
        self.tabs.addTab(self.users_tab, "👥 Users")
        self.tabs.addTab(self.trans_tab, "📜 Translations")
        
        main_layout.addWidget(self.tabs, 1)
    
    def _styled_table(self):
        """Create a consistently styled table widget."""
        table = QTableWidget()
        table.setStyleSheet(f"""
            QTableWidget {{
                background: {COLORS['bg_card']};
                border: none;
                gridline-color: {COLORS['border']};
                color: {COLORS['text_primary']};
                font-size: 13px;
            }}
            QTableWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid {COLORS['border']};
            }}
            QTableWidget::item:hover {{
                background-color: {COLORS['bg_hover']};
            }}
            QTableWidget::item:selected {{
                background-color: {COLORS['primary']}25;
                color: {COLORS['text_primary']};
            }}
            QHeaderView::section {{
                background: {COLORS['bg_input']};
                color: {COLORS['text_muted']};
                font-size: 11px; font-weight: 700;
                letter-spacing: 0.5px;
                padding: 10px 12px;
                border: none;
                border-bottom: 2px solid {COLORS['border']};
            }}
            QTableCornerButton::section {{
                background: {COLORS['bg_input']};
                border: none;
            }}
        """)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(False)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        return table
        
    def _setup_users_tab(self):
        layout = QVBoxLayout(self.users_tab)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(10)
        
        # Actions bar
        actions = QHBoxLayout()
        actions.setSpacing(8)
        
        del_btn = QPushButton("🗑️ Delete User")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['danger']};
                border: 1px solid {COLORS['danger']};
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{
                background: rgba(239, 68, 68, 0.1);
            }}
        """)
        del_btn.clicked.connect(self._delete_user)
        actions.addWidget(del_btn)
        actions.addStretch()
        layout.addLayout(actions)
        
        # Table
        self.users_table = self._styled_table()
        self.users_table.setColumnCount(3)
        self.users_table.setHorizontalHeaderLabels(["ID", "Username", "Created At"])
        self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.users_table)
        
    def _setup_trans_tab(self):
        layout = QVBoxLayout(self.trans_tab)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(10)
        
        # Actions bar
        actions = QHBoxLayout()
        actions.setSpacing(8)
        
        del_btn = QPushButton("🗑️ Delete Translation")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['danger']};
                border: 1px solid {COLORS['danger']};
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{
                background: rgba(239, 68, 68, 0.1);
            }}
        """)
        del_btn.clicked.connect(self._delete_translation)
        actions.addWidget(del_btn)
        actions.addStretch()
        layout.addLayout(actions)
        
        # Table
        self.trans_table = self._styled_table()
        self.trans_table.setColumnCount(5)
        self.trans_table.setHorizontalHeaderLabels(["Sign", "Confidence", "Type", "Username", "Time"])
        self.trans_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        layout.addWidget(self.trans_table)
        
    def refresh_all(self):
        """Reload all data."""
        if not self.db: return
        
        try:
            self._load_users()
            self._load_translations()
            self._update_stats()
        except Exception as e:
            print(f"Admin load error: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load data: {e}")
    
    def _update_stats(self):
        """Update stat cards with current counts."""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as cnt FROM users")
                user_count = cursor.fetchone()['cnt']
                self.stat_users.set_value(user_count)
                
                cursor.execute("SELECT COUNT(*) as cnt FROM translations")
                trans_count = cursor.fetchone()['cnt']
                self.stat_translations.set_value(trans_count)
                
                cursor.execute("""
                    SELECT COUNT(*) as cnt FROM translations 
                    WHERE created_at > datetime('now', '-1 day')
                """)
                recent_count = cursor.fetchone()['cnt']
                self.stat_recent.set_value(recent_count)
        except Exception:
            pass
    
    def _load_users(self):
        """Load users into table."""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, email, created_at FROM users ORDER BY created_at DESC")
            rows = cursor.fetchall()
            
            self.users_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.users_table.setItem(i, 0, QTableWidgetItem(str(row['id'])))
                self.users_table.setItem(i, 1, QTableWidgetItem(str(row['email'])))
                self.users_table.setItem(i, 2, QTableWidgetItem(str(row['created_at'])))
    
    def _load_translations(self):
        """Load translations into table."""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.id, t.sign_label, t.confidence, t.gesture_type, u.email, t.created_at 
                FROM translations t
                JOIN users u ON t.user_id = u.id
                ORDER BY t.created_at DESC LIMIT 100
            """)
            t_rows = cursor.fetchall()
            self.trans_table.setRowCount(len(t_rows))
            for i, row in enumerate(t_rows):
                # Store ID in user role for deletion
                item = QTableWidgetItem(str(row['sign_label']))
                item.setData(Qt.UserRole, row['id'])
                self.trans_table.setItem(i, 0, item)
                
                self.trans_table.setItem(i, 1, QTableWidgetItem(f"{row['confidence']*100:.1f}%"))
                self.trans_table.setItem(i, 2, QTableWidgetItem(str(row['gesture_type'])))
                self.trans_table.setItem(i, 3, QTableWidgetItem(str(row['email'])))
                self.trans_table.setItem(i, 4, QTableWidgetItem(str(row['created_at'])))
            
    def _delete_user(self):
        rows = self.users_table.selectionModel().selectedRows()
        if not rows: return
        
        username = self.users_table.item(rows[0].row(), 1).text()
        if username == "admin":
            QMessageBox.warning(self, "Error", "Cannot delete admin user!")
            return
            
        if QMessageBox.question(self, "Confirm", f"Delete user {username}?") == QMessageBox.Yes:
            user_id = self.users_table.item(rows[0].row(), 0).text()
            try:
                with self.db._get_connection() as conn:
                    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
                self.refresh_all()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _delete_translation(self):
        rows = self.trans_table.selectionModel().selectedRows()
        if not rows: return
        
        if QMessageBox.question(self, "Confirm", "Delete selected translation?") == QMessageBox.Yes:
            tid = self.trans_table.item(rows[0].row(), 0).data(Qt.UserRole)
            try:
                with self.db._get_connection() as conn:
                    conn.execute("DELETE FROM translations WHERE id=?", (tid,))
                self.refresh_all()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))
