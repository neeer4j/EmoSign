"""
Admin Page — Premium dashboard for managing users and translations.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QMessageBox, QScrollArea,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from ui.styles import COLORS


class AdminPage(QWidget):
    """Admin dashboard widget — premium design."""

    def __init__(self, db_service=None, parent=None):
        super().__init__(parent)
        self.db = db_service
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent; border: none;
            }}
            QScrollBar:vertical {{
                background: transparent; width: 6px; margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['border']}; border-radius: 3px; min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        main = QVBoxLayout(body)
        main.setContentsMargins(32, 28, 32, 28)
        main.setSpacing(20)

        # ── HEADER ────────────────────────────────────────────────
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['primary']}15, stop:1 {COLORS['accent']}10);
                border: none;
                border-radius: 16px;
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(28, 22, 28, 22)
        header_layout.setSpacing(16)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        title = QLabel("🛡️ Admin Dashboard")
        title.setStyleSheet(f"""
            font-size: 24px; font-weight: 800;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        subtitle = QLabel("Monitor and manage users, translations, and system health")
        subtitle.setStyleSheet(f"""
            font-size: 13px; color: {COLORS['text_muted']};
            background: transparent;
        """)
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_layout.addLayout(title_col, 1)

        refresh_btn = QPushButton("🔄  Refresh")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 24px;
                font-size: 13px; font-weight: 700;
            }}
            QPushButton:hover {{
                background: {COLORS['primary_hover']};
            }}
        """)
        refresh_btn.clicked.connect(self.refresh_all)
        header_layout.addWidget(refresh_btn, alignment=Qt.AlignVCenter)
        main.addWidget(header)

        # ── STAT CARDS ────────────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)

        stats_meta = [
            ("👥", "Total Users", "0", COLORS['primary']),
            ("📜", "Translations", "0", COLORS['success']),
            ("🕐", "Recent (24h)", "0", COLORS['warning']),
            ("📊", "Avg Confidence", "—", COLORS['accent']),
        ]

        self._stat_labels = []

        for icon, label, value, color in stats_meta:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: {COLORS['bg_card']};
                    border: none;
                    border-radius: 14px;
                }}
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(18, 16, 18, 16)
            card_layout.setSpacing(8)

            top = QHBoxLayout()
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet("font-size: 20px; background: transparent;")
            title_lbl = QLabel(label.upper())
            title_lbl.setStyleSheet(f"""
                font-size: 10px; font-weight: 700;
                color: {COLORS['text_muted']};
                letter-spacing: 1px; background: transparent;
            """)
            top.addWidget(icon_lbl)
            top.addWidget(title_lbl)
            top.addStretch()
            card_layout.addLayout(top)

            val_lbl = QLabel(value)
            val_lbl.setStyleSheet(f"""
                font-size: 28px; font-weight: 800;
                color: {color};
                background: transparent;
            """)
            card_layout.addWidget(val_lbl)
            self._stat_labels.append(val_lbl)

            stats_row.addWidget(card, 1)

        main.addLayout(stats_row)

        # ── INSIGHTS ───────────────────────────────────────────────
        insights = QFrame()
        insights.setObjectName("adminInsightsRow")
        insights.setStyleSheet(f"""
            QFrame#adminInsightsRow {{
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
            QFrame#adminInsightItem {{
                background: transparent;
                border: none;
            }}
            QLabel#adminInsightTitle {{
                color: {COLORS['text_muted']};
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1px;
                background: transparent;
                border: none;
                padding: 0;
                margin: 0;
            }}
            QLabel#adminInsightValue {{
                color: {COLORS['text_primary']};
                font-size: 14px;
                font-weight: 700;
                background: transparent;
                border: none;
                padding: 0;
                margin: 0;
            }}
        """)
        insights_layout = QHBoxLayout(insights)
        insights_layout.setContentsMargins(16, 14, 16, 14)
        insights_layout.setSpacing(18)

        self._insight_values = {}
        insight_meta = [
            ("new_users_7d", "NEW USERS (7D)", "0"),
            ("top_sign", "TOP SIGN", "—"),
            ("top_user", "TOP USER", "—"),
            ("last_activity", "LAST TRANSLATION", "—"),
        ]

        for key, label, value in insight_meta:
            item = QFrame()
            item.setObjectName("adminInsightItem")
            col = QVBoxLayout(item)
            col.setSpacing(4)
            title_lbl = QLabel(label)
            title_lbl.setObjectName("adminInsightTitle")
            val_lbl = QLabel(value)
            val_lbl.setObjectName("adminInsightValue")
            col.addWidget(title_lbl)
            col.addWidget(val_lbl)
            insights_layout.addWidget(item, 1)
            self._insight_values[key] = val_lbl

        main.addWidget(insights)

        # ── TABS ──────────────────────────────────────────────────
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

        self.tabs.addTab(self.users_tab, "👥  Users")
        self.tabs.addTab(self.trans_tab, "📜  Translations")

        main.addWidget(self.tabs, 1)

        scroll.setWidget(body)
        outer.addWidget(scroll)

    # ── Table factory ─────────────────────────────────────────────

    def _styled_table(self):
        table = QTableWidget()
        table.setStyleSheet(f"""
            QTableWidget {{
                background: {COLORS['bg_card']};
                border: none;
                color: {COLORS['text_primary']};
                font-size: 13px;
                outline: none;
                gridline-color: transparent;
                selection-background-color: {COLORS['primary']}1f;
                selection-color: {COLORS['text_primary']};
            }}
            QTableWidget:focus {{
                outline: none;
                border: none;
            }}
            QTableWidget::item {{
                padding: 10px 14px;
                border: none;
                border-bottom: 1px solid {COLORS['border']};
            }}
            QTableWidget::item:hover {{
                background: {COLORS['bg_hover']};
            }}
            QTableWidget::item:selected {{
                background: {COLORS['primary']}20;
                color: {COLORS['text_primary']};
                border: none;
                border-bottom: 1px solid {COLORS['border']};
                outline: none;
            }}
            QHeaderView::section {{
                background: {COLORS['bg_input']};
                color: {COLORS['text_muted']};
                font-size: 10px; font-weight: 700;
                letter-spacing: 1px;
                text-transform: uppercase;
                padding: 12px 14px;
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
        table.setFocusPolicy(Qt.NoFocus)
        return table

    # ── Users tab ─────────────────────────────────────────────────

    def _setup_users_tab(self):
        layout = QVBoxLayout(self.users_tab)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(10)

        actions = QHBoxLayout()
        actions.setSpacing(8)

        del_btn = QPushButton("🗑️  Delete User")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['danger']};
                border: 1px solid {COLORS['danger']}60;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{
                background: {COLORS['danger']}15;
                border-color: {COLORS['danger']};
            }}
        """)
        del_btn.clicked.connect(self._delete_user)
        actions.addWidget(del_btn)
        actions.addStretch()

        info = QLabel("Select a row to manage")
        info.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent;")
        actions.addWidget(info)

        layout.addLayout(actions)

        self.users_table = self._styled_table()
        self.users_table.setColumnCount(3)
        self.users_table.setHorizontalHeaderLabels(["ID", "USERNAME", "CREATED AT"])
        hh = self.users_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        layout.addWidget(self.users_table)

    # ── Translations tab ──────────────────────────────────────────

    def _setup_trans_tab(self):
        layout = QVBoxLayout(self.trans_tab)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(10)

        actions = QHBoxLayout()
        actions.setSpacing(8)

        del_btn = QPushButton("🗑️  Delete Translation")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['danger']};
                border: 1px solid {COLORS['danger']}60;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{
                background: {COLORS['danger']}15;
                border-color: {COLORS['danger']};
            }}
        """)
        del_btn.clicked.connect(self._delete_translation)
        actions.addWidget(del_btn)
        actions.addStretch()

        info = QLabel("Showing latest 100 translations")
        info.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent;")
        actions.addWidget(info)

        layout.addLayout(actions)

        self.trans_table = self._styled_table()
        self.trans_table.setColumnCount(5)
        self.trans_table.setHorizontalHeaderLabels(["SIGN", "CONFIDENCE", "TYPE", "USERNAME", "TIME"])
        hh = self.trans_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        layout.addWidget(self.trans_table)

    # ── Data ──────────────────────────────────────────────────────

    def refresh_all(self):
        if not self.db:
            return
        try:
            self._load_users()
            self._load_translations()
            self._update_stats()
        except Exception as e:
            print(f"Admin load error: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load data: {e}")

    def _update_stats(self):
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) as cnt FROM users")
                self._stat_labels[0].setText(str(cursor.fetchone()['cnt']))

                cursor.execute("SELECT COUNT(*) as cnt FROM translations")
                self._stat_labels[1].setText(str(cursor.fetchone()['cnt']))

                cursor.execute("""
                    SELECT COUNT(*) as cnt FROM translations
                    WHERE created_at > datetime('now', '-1 day')
                """)
                self._stat_labels[2].setText(str(cursor.fetchone()['cnt']))

                cursor.execute("SELECT AVG(confidence) as avg_c FROM translations")
                row = cursor.fetchone()
                avg = row['avg_c'] if row['avg_c'] else 0
                self._stat_labels[3].setText(f"{avg*100:.1f}%")

                cursor.execute("""
                    SELECT COUNT(*) AS cnt
                    FROM users
                    WHERE created_at > datetime('now', '-7 day')
                """)
                new_users = cursor.fetchone()['cnt']
                self._insight_values['new_users_7d'].setText(str(new_users))

                cursor.execute("""
                    SELECT sign_label, COUNT(*) AS cnt
                    FROM translations
                    GROUP BY sign_label
                    ORDER BY cnt DESC
                    LIMIT 1
                """)
                top_sign_row = cursor.fetchone()
                if top_sign_row:
                    self._insight_values['top_sign'].setText(
                        f"{top_sign_row['sign_label']} ({top_sign_row['cnt']})"
                    )
                else:
                    self._insight_values['top_sign'].setText("—")

                cursor.execute("""
                    SELECT u.email, COUNT(*) AS cnt
                    FROM translations t
                    JOIN users u ON u.id = t.user_id
                    GROUP BY t.user_id
                    ORDER BY cnt DESC
                    LIMIT 1
                """)
                top_user_row = cursor.fetchone()
                if top_user_row:
                    self._insight_values['top_user'].setText(
                        f"{top_user_row['email']} ({top_user_row['cnt']})"
                    )
                else:
                    self._insight_values['top_user'].setText("—")

                cursor.execute("SELECT MAX(created_at) AS latest FROM translations")
                latest_row = cursor.fetchone()
                latest = latest_row['latest'] if latest_row else None
                self._insight_values['last_activity'].setText(str(latest) if latest else "—")
        except Exception:
            pass

    def _load_users(self):
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, email, created_at FROM users ORDER BY created_at DESC")
            rows = cursor.fetchall()

            self.users_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                id_item = QTableWidgetItem(str(row['id'])[:8] + "…")
                id_item.setData(Qt.UserRole, str(row['id']))
                id_item.setForeground(QColor(COLORS['text_muted']))
                self.users_table.setItem(i, 0, id_item)
                self.users_table.setItem(i, 1, QTableWidgetItem(str(row['email'])))
                self.users_table.setItem(i, 2, QTableWidgetItem(str(row['created_at'])))

    def _load_translations(self):
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.id, t.sign_label, t.confidence, t.gesture_type, u.email, t.created_at
                FROM translations t
                JOIN users u ON t.user_id = u.id
                ORDER BY t.created_at DESC LIMIT 100
            """)
            rows = cursor.fetchall()
            self.trans_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                item = QTableWidgetItem(str(row['sign_label']))
                item.setData(Qt.UserRole, row['id'])
                self.trans_table.setItem(i, 0, item)

                conf = row['confidence'] * 100
                conf_item = QTableWidgetItem(f"{conf:.1f}%")
                self.trans_table.setItem(i, 1, conf_item)

                self.trans_table.setItem(i, 2, QTableWidgetItem(str(row['gesture_type'])))
                self.trans_table.setItem(i, 3, QTableWidgetItem(str(row['email'])))
                self.trans_table.setItem(i, 4, QTableWidgetItem(str(row['created_at'])))

    # ── Actions ───────────────────────────────────────────────────

    def _delete_user(self):
        rows = self.users_table.selectionModel().selectedRows()
        if not rows:
            return

        username = self.users_table.item(rows[0].row(), 1).text()
        if username == "admin":
            QMessageBox.warning(self, "Error", "Cannot delete admin user!")
            return

        if QMessageBox.question(self, "Confirm", f"Delete user '{username}'?") == QMessageBox.Yes:
            user_id = self.users_table.item(rows[0].row(), 0).data(Qt.UserRole)
            try:
                with self.db._get_connection() as conn:
                    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
                self.refresh_all()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _delete_translation(self):
        rows = self.trans_table.selectionModel().selectedRows()
        if not rows:
            return

        if QMessageBox.question(self, "Confirm", "Delete selected translation?") == QMessageBox.Yes:
            tid = self.trans_table.item(rows[0].row(), 0).data(Qt.UserRole)
            try:
                with self.db._get_connection() as conn:
                    conn.execute("DELETE FROM translations WHERE id=?", (tid,))
                self.refresh_all()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))
