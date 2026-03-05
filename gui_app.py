"""
PPW – Personal Password Manager
Modern dark-themed desktop GUI built with PyQt6.
"""
import sys

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout, QStackedWidget,
    QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QCheckBox,
    QFrame, QScrollArea, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPalette, QPainter, QBrush, QCursor

from controllers.auth_controller import AuthController
from controllers.account_controller import AccountController
from controllers.security_controller import SecurityController
from db.database import db_manager
from utils import extension_api

# ── Clipboard helper (no hard dep on pyperclip) ───────────────────────────────
try:
    import pyperclip
    def copy_to_clipboard(text: str):
        pyperclip.copy(text)
except ImportError:
    def copy_to_clipboard(text: str):
        cb = QApplication.clipboard()
        cb.setText(text)

# ── Palette / Design Tokens ───────────────────────────────────────────────────
BG           = "#0f1117"
SURFACE      = "#1a1d27"
SURFACE2     = "#22263a"
BORDER       = "#2e3250"
ACCENT       = "#6c63ff"
ACCENT_HOVER = "#7b73ff"
ACCENT_PRESS = "#5a52e0"
TEXT         = "#e2e8f0"
TEXT_MUTED   = "#718096"
SUCCESS      = "#48bb78"
WARNING      = "#ed8936"
DANGER       = "#fc8181"
CARD_BG      = "#1e2130"

FONT_FAMILY  = "Segoe UI"

# ── Shared stylesheet ─────────────────────────────────────────────────────────
APP_STYLE = f"""
QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: "{FONT_FAMILY}", Arial, sans-serif;
    font-size: 13px;
}}
QLabel {{
    background: transparent;
}}
QLineEdit, QTextEdit, QComboBox {{
    background-color: {SURFACE2};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    color: {TEXT};
    selection-background-color: {ACCENT};
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
    border: 1px solid {ACCENT};
}}
QComboBox::drop-down {{ border: none; padding-right: 8px; }}
QComboBox QAbstractItemView {{
    background: {SURFACE2};
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT};
    outline: none;
}}
QPushButton {{
    background-color: {ACCENT};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 9px 20px;
    font-weight: 600;
    font-size: 13px;
}}
QPushButton:hover  {{ background-color: {ACCENT_HOVER}; }}
QPushButton:pressed {{ background-color: {ACCENT_PRESS}; }}
QPushButton:disabled {{ background-color: {SURFACE2}; color: {TEXT_MUTED}; }}
QPushButton[flat="true"] {{
    background: transparent;
    color: {TEXT_MUTED};
    padding: 6px 10px;
}}
QPushButton[flat="true"]:hover {{ color: {TEXT}; background: {SURFACE2}; }}
QPushButton[danger="true"] {{
    background-color: transparent;
    color: {DANGER};
    border: 1px solid {DANGER};
}}
QPushButton[danger="true"]:hover {{ background-color: {DANGER}; color: white; }}
QScrollBar:vertical {{
    background: {SURFACE};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 1px solid {BORDER};
    border-radius: 4px;
    background: {SURFACE2};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}
QFrame[card="true"] {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 12px;
}}
"""

# ── Strength bar colours ──────────────────────────────────────────────────────
def strength_color(score: int) -> str:
    if score >= 80: return SUCCESS
    if score >= 50: return WARNING
    return DANGER

def strength_label(score: int) -> str:
    if score >= 80: return "Strong"
    if score >= 50: return "Medium"
    return "Weak"

# ═════════════════════════════════════════════════════════════════════════════
#  Reusable widgets
# ═════════════════════════════════════════════════════════════════════════════

class IconButton(QPushButton):
    """Small square icon-only button."""
    def __init__(self, icon_text: str, tooltip: str = "", danger: bool = False, parent=None):
        super().__init__(icon_text, parent)
        self.setFixedSize(34, 34)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip(tooltip)
        if danger:
            self.setProperty("danger", "true")
            self.style().unpolish(self)
            self.style().polish(self)

class Divider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setStyleSheet(f"color: {BORDER}; background: {BORDER}; border: none; max-height: 1px;")

class Badge(QLabel):
    def __init__(self, text: str, color: str = ACCENT, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QLabel {{
                background: {color}22;
                color: {color};
                border: 1px solid {color}55;
                border-radius: 10px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 600;
            }}
        """)

class StrengthBar(QWidget):
    def __init__(self, score: int = 0, parent=None):
        super().__init__(parent)
        self.setFixedHeight(6)
        self._score = score

    def set_score(self, score: int):
        self._score = score
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        # background track
        painter.setBrush(QBrush(QColor(BORDER)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, w, h, 3, 3)
        # filled portion
        fill_w = int(w * self._score / 100)
        if fill_w > 0:
            painter.setBrush(QBrush(QColor(strength_color(self._score))))
            painter.drawRoundedRect(0, 0, fill_w, h, 3, 3)
        painter.end()


# ═════════════════════════════════════════════════════════════════════════════
#  Account Card  (used in the vault list)
# ═════════════════════════════════════════════════════════════════════════════

CATEGORY_ICONS = {
    "Email": "📧", "Social Media": "💬", "Banking": "🏦",
    "Shopping": "🛒", "Entertainment": "🎬", "Work": "💼",
    "Education": "📚", "Other": "🔑",
}

class AccountCard(QFrame):
    view_clicked   = pyqtSignal(dict)
    copy_clicked   = pyqtSignal(dict)
    delete_clicked = pyqtSignal(dict)

    def __init__(self, account: dict, parent=None):
        super().__init__(parent)
        self.account = account
        self.setProperty("card", "true")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._build()

    def _build(self):
        acc = self.account
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 12, 12)
        layout.setSpacing(12)

        # Icon circle
        icon_label = QLabel(CATEGORY_ICONS.get(acc.get("category", "Other"), "🔑"))
        icon_label.setFixedSize(42, 42)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"""
            background: {ACCENT}22;
            border-radius: 21px;
            font-size: 18px;
        """)
        layout.addWidget(icon_label)

        # Text block
        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        title_row = QHBoxLayout()
        title_lbl = QLabel(acc.get("title", "—"))
        title_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {TEXT};")
        title_row.addWidget(title_lbl)

        score = acc.get("strength_score", 0)
        badge = Badge(strength_label(score), strength_color(score))
        title_row.addWidget(badge)
        title_row.addStretch()
        text_col.addLayout(title_row)

        sub = acc.get("username") or acc.get("email") or acc.get("url") or acc.get("category", "")
        sub_lbl = QLabel(sub)
        sub_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        text_col.addWidget(sub_lbl)

        bar = StrengthBar(score)
        bar.setFixedWidth(140)
        text_col.addWidget(bar)

        layout.addLayout(text_col)
        layout.addStretch()

        # Action buttons
        btn_view   = IconButton("👁",  "View / Copy password")
        btn_copy   = IconButton("📋", "Copy password")
        btn_delete = IconButton("🗑",  "Delete", danger=True)

        btn_view.clicked.connect(lambda: self.view_clicked.emit(self.account))
        btn_copy.clicked.connect(lambda: self.copy_clicked.emit(self.account))
        btn_delete.clicked.connect(lambda: self.delete_clicked.emit(self.account))

        for btn in (btn_view, btn_copy, btn_delete):
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {SURFACE2};
                    color: {TEXT_MUTED};
                    border: 1px solid {BORDER};
                    border-radius: 8px;
                    font-size: 14px;
                }}
                QPushButton:hover {{ background: {BORDER}; color: {TEXT}; }}
            """)
        btn_delete.setStyleSheet(f"""
            QPushButton {{
                background: {SURFACE2};
                color: {DANGER};
                border: 1px solid {BORDER};
                border-radius: 8px;
                font-size: 14px;
            }}
            QPushButton:hover {{ background: {DANGER}22; border-color: {DANGER}; }}
        """)

        layout.addWidget(btn_view)
        layout.addWidget(btn_copy)
        layout.addWidget(btn_delete)


# ═════════════════════════════════════════════════════════════════════════════
#  Auth Screen (Login + Register)
# ═════════════════════════════════════════════════════════════════════════════

class AuthScreen(QWidget):
    """
    Two-page auth screen:
      - Login  : username + master password
      - Register: username + email (required) + password + confirm password
    Animated toggle between the two.
    """
    authenticated = pyqtSignal(str, str, str)   # user_id, session_token, master_password

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode = "login"
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._card = QFrame()
        self._card.setProperty("card", "true")
        self._card.setFixedWidth(440)
        vl = QVBoxLayout(self._card)
        vl.setContentsMargins(44, 40, 44, 40)
        vl.setSpacing(14)

        # ── Logo ──────────────────────────────────────────────────
        logo = QLabel("🔐")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("font-size: 44px; background: transparent;")
        vl.addWidget(logo)

        self._title = QLabel("Welcome back")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setStyleSheet(
            f"font-size: 22px; font-weight: 700; color: {TEXT}; background: transparent;")
        vl.addWidget(self._title)

        self._subtitle = QLabel("Enter your master password to unlock your vault")
        self._subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitle.setWordWrap(True)
        self._subtitle.setStyleSheet(
            f"color: {TEXT_MUTED}; background: transparent; font-size: 12px; margin-bottom: 4px;")
        vl.addWidget(self._subtitle)

        # ── Fields ────────────────────────────────────────────────
        self._username = QLineEdit()
        self._username.setPlaceholderText("Username")
        self._username.setFixedHeight(42)
        vl.addWidget(self._username)

        # Register-only fields
        self._email = QLineEdit()
        self._email.setPlaceholderText("Email address  (required — used for security alerts)")
        self._email.setFixedHeight(42)
        self._email.setVisible(False)
        vl.addWidget(self._email)

        # Password row
        pw_row = QHBoxLayout()
        self._password = QLineEdit()
        self._password.setPlaceholderText("Master password")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setFixedHeight(42)
        self._password.returnPressed.connect(self._submit)
        pw_row.addWidget(self._password)
        self._eye_btn = QPushButton("👁")
        self._eye_btn.setFixedSize(42, 42)
        self._eye_btn.setStyleSheet(
            f"background:{SURFACE2};border:1px solid {BORDER};border-radius:8px;font-size:14px;")
        self._eye_btn.clicked.connect(self._toggle_eye)
        pw_row.addWidget(self._eye_btn)
        vl.addLayout(pw_row)

        # Confirm password (register only)
        self._confirm_pw = QLineEdit()
        self._confirm_pw.setPlaceholderText("Confirm master password")
        self._confirm_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm_pw.setFixedHeight(42)
        self._confirm_pw.setVisible(False)
        self._confirm_pw.returnPressed.connect(self._submit)
        vl.addWidget(self._confirm_pw)

        # Password hint (register only)
        self._pw_hint = QLabel(
            "Min 12 chars · uppercase · lowercase · digit · symbol")
        self._pw_hint.setStyleSheet(
            f"color:{TEXT_MUTED}; font-size:11px; background:transparent;")
        self._pw_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pw_hint.setVisible(False)
        vl.addWidget(self._pw_hint)

        # Status label
        self._status = QLabel("")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setWordWrap(True)
        self._status.setStyleSheet(
            f"color:{DANGER}; background:transparent; font-size:12px;")
        vl.addWidget(self._status)

        # Primary button
        self._submit_btn = QPushButton("Sign In")
        self._submit_btn.setFixedHeight(44)
        self._submit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._submit_btn.clicked.connect(self._submit)
        vl.addWidget(self._submit_btn)

        # Divider
        div_row = QHBoxLayout()
        for _ in range(2):
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setStyleSheet(f"color:{BORDER};")
            div_row.addWidget(line)
        or_lbl = QLabel(" or ")
        or_lbl.setStyleSheet(f"color:{TEXT_MUTED}; font-size:11px;")
        div_row.insertWidget(1, or_lbl)
        vl.addLayout(div_row)

        # Toggle button
        self._toggle_btn = QPushButton("Create a new account")
        self._toggle_btn.setFixedHeight(40)
        self._toggle_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: {SURFACE2};
                color: {ACCENT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{ background: {BORDER}; }}
        """)
        self._toggle_btn.clicked.connect(self._toggle_mode)
        vl.addWidget(self._toggle_btn)

        outer.addWidget(self._card, alignment=Qt.AlignmentFlag.AlignCenter)

    # ── Helpers ───────────────────────────────────────────────────
    def _toggle_eye(self):
        hidden = self._password.echoMode() == QLineEdit.EchoMode.Password
        mode = QLineEdit.EchoMode.Normal if hidden else QLineEdit.EchoMode.Password
        self._password.setEchoMode(mode)
        self._eye_btn.setText("🙈" if hidden else "👁")

    def _set_status(self, msg: str, ok: bool = False):
        color = SUCCESS if ok else DANGER
        self._status.setStyleSheet(
            f"color:{color}; background:transparent; font-size:12px;")
        self._status.setText(msg)

    def _toggle_mode(self):
        going_to_register = (self._mode == "login")
        self._mode = "register" if going_to_register else "login"

        # Show/hide register-only fields
        for w in (self._email, self._confirm_pw, self._pw_hint):
            w.setVisible(going_to_register)

        if going_to_register:
            self._title.setText("Create your vault")
            self._subtitle.setText(
                "Your data is encrypted on your device — we never see your passwords")
            self._submit_btn.setText("Create Account")
            self._toggle_btn.setText("Already have an account? Sign in")
            self._card.setFixedWidth(440)
        else:
            self._title.setText("Welcome back")
            self._subtitle.setText("Enter your master password to unlock your vault")
            self._submit_btn.setText("Sign In")
            self._toggle_btn.setText("Create a new account")

        self._status.setText("")
        self._password.clear()
        self._confirm_pw.clear()
        self._username.setFocus()

    # ── Submit ────────────────────────────────────────────────────
    def _submit(self):
        username = self._username.text().strip()
        password = self._password.text()
        self._set_status("")

        if not username or not password:
            self._set_status("Please fill in all required fields.")
            return

        self._submit_btn.setEnabled(False)
        self._submit_btn.setText("Please wait…")

        try:
            if self._mode == "register":
                self._do_register(username, password)
            else:
                self._do_login(username, password)
        finally:
            label = "Sign In" if self._mode == "login" else "Create Account"
            self._submit_btn.setText(label)
            self._submit_btn.setEnabled(True)

    def _do_register(self, username: str, password: str):
        email   = self._email.text().strip()
        confirm = self._confirm_pw.text()

        if not email:
            self._set_status("Email is required — we use it for security alerts.")
            return

        if password != confirm:
            self._set_status("Passwords don't match. Please try again.")
            return

        ok, msg, uid = AuthController.register(username, password, email)
        if ok:
            self._set_status(
                "✅  Account created! Check your inbox for a welcome email, then sign in.",
                ok=True)
            # Switch to login after short delay
            QTimer.singleShot(2000, self._toggle_mode)
        else:
            self._set_status(msg)

    def _do_login(self, username: str, password: str):
        ok, msg, session = AuthController.login(username, password)
        if ok:
            self.authenticated.emit(
                session["user_id"], session["session_token"], password)
        else:
            self._set_status(msg)


# ═════════════════════════════════════════════════════════════════════════════
#  Add / Edit Account Dialog
# ═════════════════════════════════════════════════════════════════════════════

class AccountDialog(QDialog):
    def __init__(self, user_id: str, master_password: str, account: dict = None, parent=None):
        super().__init__(parent)
        self._user_id = user_id
        self._master_password = master_password
        self._account = account
        self.setWindowTitle("Edit Account" if account else "New Account")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build()
        if account:
            self._populate()

    def _build(self):
        vl = QVBoxLayout(self)
        vl.setContentsMargins(28, 28, 28, 28)
        vl.setSpacing(14)

        header = QLabel("Edit Account" if self._account else "Add New Account")
        header.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {TEXT};")
        vl.addWidget(header)
        vl.addWidget(Divider())

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        def field(ph):
            w = QLineEdit(); w.setPlaceholderText(ph); w.setFixedHeight(40); return w

        self._title    = field("e.g. Gmail")
        self._username = field("login username")
        self._email_f  = field("account email")
        self._url      = field("https://example.com")

        pw_row = QHBoxLayout()
        self._pw = QLineEdit()
        self._pw.setPlaceholderText("password")
        self._pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw.setFixedHeight(40)
        self._pw.textChanged.connect(self._update_strength)
        pw_row.addWidget(self._pw)

        eye = QPushButton("👁"); eye.setFixedSize(40, 40)
        eye.setStyleSheet(f"background:{SURFACE2};border:1px solid {BORDER};border-radius:8px;")
        eye.clicked.connect(lambda: self._pw.setEchoMode(
            QLineEdit.EchoMode.Normal if self._pw.echoMode() == QLineEdit.EchoMode.Password
            else QLineEdit.EchoMode.Password))
        pw_row.addWidget(eye)

        gen_btn = QPushButton("Generate")
        gen_btn.setFixedHeight(40)
        gen_btn.clicked.connect(self._generate)
        pw_row.addWidget(gen_btn)

        self._strength_bar   = StrengthBar()
        self._strength_label = QLabel("")
        self._strength_label.setStyleSheet(f"color:{TEXT_MUTED}; font-size:11px;")

        self._category = QComboBox()
        self._category.addItems(["Other","Email","Social Media","Banking","Shopping","Entertainment","Work","Education"])
        self._category.setFixedHeight(40)

        self._notes = QTextEdit()
        self._notes.setPlaceholderText("Optional notes…")
        self._notes.setFixedHeight(80)

        self._twofa = QCheckBox("Two-factor authentication enabled on this account")

        form.addRow("Title *",    self._title)
        form.addRow("Username",   self._username)
        form.addRow("Email",      self._email_f)
        form.addRow("Password *", pw_row)
        form.addRow("",           self._strength_bar)
        form.addRow("",           self._strength_label)
        form.addRow("URL",        self._url)
        form.addRow("Category",   self._category)
        form.addRow("Notes",      self._notes)
        form.addRow("",           self._twofa)
        vl.addLayout(form)

        vl.addWidget(Divider())
        btn_row = QHBoxLayout()
        cancel = QPushButton("Cancel"); cancel.setProperty("flat","true"); cancel.clicked.connect(self.reject)
        save   = QPushButton("Save Account"); save.setFixedHeight(42); save.clicked.connect(self._save)
        btn_row.addWidget(cancel); btn_row.addStretch(); btn_row.addWidget(save)
        vl.addLayout(btn_row)

    def _update_strength(self):
        pw = self._pw.text()
        if pw:
            res = AccountController.analyze_password_strength(pw)
            score = res.get("score", 0)
            self._strength_bar.set_score(score)
            self._strength_label.setText(f"{strength_label(score)} — {score}/100")
            self._strength_label.setStyleSheet(f"color:{strength_color(score)}; font-size:11px;")
        else:
            self._strength_bar.set_score(0)
            self._strength_label.setText("")

    def _generate(self):
        res = AccountController.generate_strong_password(length=20)
        if res.get("password"):
            self._pw.setText(res["password"])
            self._pw.setEchoMode(QLineEdit.EchoMode.Normal)

    def _populate(self):
        a = self._account
        self._title.setText(a.get("title",""))
        self._username.setText(a.get("username","") or "")
        self._email_f.setText(a.get("email","") or "")
        self._url.setText(a.get("url","") or "")
        self._category.setCurrentText(a.get("category","Other"))
        self._twofa.setChecked(a.get("two_factor_enabled", False))

    def _save(self):
        title = self._title.text().strip()
        pw    = self._pw.text()
        if not title:
            QMessageBox.warning(self, "Required", "Title is required.")
            return
        if not pw and not self._account:
            QMessageBox.warning(self, "Required", "Password is required.")
            return

        updates = dict(
            title=title,
            username=self._username.text().strip() or None,
            email=self._email_f.text().strip() or None,
            url=self._url.text().strip() or None,
            category=self._category.currentText(),
            notes=self._notes.toPlainText().strip() or None,
            two_factor_enabled=self._twofa.isChecked(),
        )
        if pw:
            updates["password"] = pw

        if self._account:
            ok, msg = AccountController.update_account(
                self._user_id, self._account["account_id"], self._master_password, **updates)
        else:
            ok, msg = AccountController.create_account(
                self._user_id, self._master_password, **updates)

        if ok:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", msg)


# ═════════════════════════════════════════════════════════════════════════════
#  Vault Screen  (main password list)
# ═════════════════════════════════════════════════════════════════════════════

class VaultScreen(QWidget):
    logout_requested = pyqtSignal()

    def __init__(self, user_id: str, session_token: str, master_password: str, parent=None):
        super().__init__(parent)
        self._user_id        = user_id
        self._session_token  = session_token
        self._master_password = master_password
        self._accounts       = []
        self._build()
        self._load_accounts()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._load_accounts)
        self._timer.start(60_000)

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f"background:{SURFACE}; border-right: 1px solid {BORDER};")
        sb_vl = QVBoxLayout(sidebar)
        sb_vl.setContentsMargins(16, 24, 16, 24)
        sb_vl.setSpacing(4)

        logo_row = QHBoxLayout()
        logo_lbl = QLabel("🔐")
        logo_lbl.setStyleSheet("font-size:22px; background:transparent;")
        app_name  = QLabel("PPW")
        app_name.setStyleSheet(f"font-size:18px; font-weight:700; color:{TEXT}; background:transparent;")
        logo_row.addWidget(logo_lbl); logo_row.addWidget(app_name); logo_row.addStretch()
        sb_vl.addLayout(logo_row)
        sb_vl.addSpacing(20)

        # Nav items
        self._nav_btns = {}
        for key, icon, label in [
            ("vault",    "🗄️",  "Vault"),
            ("security", "🛡️",  "Security"),
            ("generator","⚡",  "Generator"),
        ]:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setCheckable(True)
            btn.setFixedHeight(40)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet(f"""
                QPushButton {{
                    text-align: left;
                    background: transparent;
                    border: none;
                    border-radius: 8px;
                    color: {TEXT_MUTED};
                    font-size: 13px;
                    padding-left: 8px;
                }}
                QPushButton:checked {{
                    background: {ACCENT}22;
                    color: {ACCENT};
                    font-weight: 600;
                }}
                QPushButton:hover:!checked {{ background: {SURFACE2}; color: {TEXT}; }}
            """)
            btn.clicked.connect(lambda _, k=key: self._nav(k))
            self._nav_btns[key] = btn
            sb_vl.addWidget(btn)

        sb_vl.addStretch()
        sb_vl.addWidget(Divider())

        logout_btn = QPushButton("  🚪  Sign out")
        logout_btn.setFixedHeight(40)
        logout_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                text-align:left; background:transparent; border:none;
                border-radius:8px; color:{TEXT_MUTED}; font-size:13px; padding-left:8px;
            }}
            QPushButton:hover {{ background:{DANGER}22; color:{DANGER}; }}
        """)
        logout_btn.clicked.connect(self._logout)
        sb_vl.addWidget(logout_btn)

        root.addWidget(sidebar)

        # ── Content area ──────────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_vault_page())    # 0
        self._stack.addWidget(self._build_security_page()) # 1
        self._stack.addWidget(self._build_generator_page())# 2
        root.addWidget(self._stack)

        self._nav("vault")

    def _nav(self, key: str):
        idx = {"vault": 0, "security": 1, "generator": 2}[key]
        self._stack.setCurrentIndex(idx)
        for k, btn in self._nav_btns.items():
            btn.setChecked(k == key)
        if key == "security":
            self._load_security()

    # ── Vault page ────────────────────────────────────────────────
    def _build_vault_page(self):
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(28, 24, 28, 24)
        vl.setSpacing(16)

        # Header row
        header_row = QHBoxLayout()
        title = QLabel("My Vault")
        title.setStyleSheet(f"font-size:22px; font-weight:700; color:{TEXT};")
        header_row.addWidget(title)
        header_row.addStretch()

        add_btn = QPushButton("+ Add Account")
        add_btn.setFixedHeight(38)
        add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_btn.clicked.connect(self._add_account)
        header_row.addWidget(add_btn)
        vl.addLayout(header_row)

        # Search + filter row
        sf_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Search accounts…")
        self._search.setFixedHeight(38)
        self._search.textChanged.connect(self._filter_accounts)
        sf_row.addWidget(self._search)

        self._cat_filter = QComboBox()
        self._cat_filter.setFixedHeight(38)
        self._cat_filter.setFixedWidth(160)
        self._cat_filter.addItems(["All Categories","Email","Social Media","Banking",
                                   "Shopping","Entertainment","Work","Education","Other"])
        self._cat_filter.currentTextChanged.connect(self._filter_accounts)
        sf_row.addWidget(self._cat_filter)
        vl.addLayout(sf_row)

        # Stats chips
        self._stats_row = QHBoxLayout()
        self._stats_row.setSpacing(8)
        vl.addLayout(self._stats_row)

        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._cards_container = QWidget()
        self._cards_layout    = QVBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(8)
        self._cards_layout.addStretch()

        scroll.setWidget(self._cards_container)
        vl.addWidget(scroll)

        return w

    def _load_accounts(self):
        self._accounts = AccountController.get_accounts(self._user_id)
        self._render_cards(self._accounts)
        self._render_stats(self._accounts)

    def _render_stats(self, accounts):
        # clear old chips
        while self._stats_row.count():
            item = self._stats_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        total  = len(accounts)
        strong = sum(1 for a in accounts if a.get("strength_score", 0) >= 80)
        weak   = sum(1 for a in accounts if a.get("strength_score", 0) < 50)

        for text, color in [
            (f"{total} accounts", ACCENT),
            (f"{strong} strong", SUCCESS),
            (f"{weak} weak", DANGER if weak else TEXT_MUTED),
        ]:
            self._stats_row.addWidget(Badge(text, color))
        self._stats_row.addStretch()

    def _render_cards(self, accounts):
        # Remove all existing cards (keep the trailing stretch)
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not accounts:
            empty = QLabel("No accounts found.\nClick  + Add Account  to get started.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color:{TEXT_MUTED}; font-size:14px; padding:40px;")
            self._cards_layout.insertWidget(0, empty)
            return

        for acc in accounts:
            card = AccountCard(acc)
            card.view_clicked.connect(self._view_account)
            card.copy_clicked.connect(self._copy_password)
            card.delete_clicked.connect(self._delete_account)
            self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)

    def _filter_accounts(self):
        q   = self._search.text().strip().lower()
        cat = self._cat_filter.currentText()
        filtered = [
            a for a in self._accounts
            if (not q or q in a.get("title","").lower()
                      or q in (a.get("username") or "").lower()
                      or q in (a.get("url") or "").lower())
            and (cat == "All Categories" or a.get("category") == cat)
        ]
        self._render_cards(filtered)

    def _add_account(self):
        dlg = AccountDialog(self._user_id, self._master_password, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load_accounts()

    def _view_account(self, acc):
        details = AccountController.get_account_details(
            self._user_id, acc["account_id"],
            include_password=True, master_password=self._master_password)
        if not details:
            return
        pw = details.get("password", "—")

        dlg = QDialog(self)
        dlg.setWindowTitle(f"  {acc.get('title','Account')}")
        dlg.setMinimumWidth(420)
        vl = QVBoxLayout(dlg)
        vl.setContentsMargins(28, 28, 28, 28)
        vl.setSpacing(14)

        icon_lbl = QLabel(CATEGORY_ICONS.get(acc.get("category","Other"), "🔑"))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("font-size:36px; background:transparent;")
        vl.addWidget(icon_lbl)

        def row(label, value, copyable=False):
            if not value: return
            rl = QHBoxLayout()
            lbl = QLabel(f"<b>{label}</b>")
            lbl.setFixedWidth(100)
            lbl.setStyleSheet(f"color:{TEXT_MUTED}; font-size:12px;")
            val = QLabel(value)
            val.setWordWrap(True)
            val.setStyleSheet(f"color:{TEXT}; font-size:13px;")
            rl.addWidget(lbl); rl.addWidget(val)
            if copyable:
                cb = IconButton("📋","Copy")
                cb.clicked.connect(lambda _, v=value: copy_to_clipboard(v))
                rl.addWidget(cb)
            vl.addLayout(rl)

        row("Title",    details.get("title"))
        row("Username", details.get("username"), copyable=True)
        row("Email",    details.get("email"),    copyable=True)
        row("URL",      details.get("url"))
        row("Category", details.get("category"))

        # Password row with toggle
        pw_row_layout = QHBoxLayout()
        pw_lbl = QLabel("<b>Password</b>")
        pw_lbl.setFixedWidth(100)
        pw_lbl.setStyleSheet(f"color:{TEXT_MUTED}; font-size:12px;")
        self._pw_val_lbl = QLineEdit(pw)
        self._pw_val_lbl.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw_val_lbl.setReadOnly(True)
        self._pw_val_lbl.setStyleSheet(f"background:{SURFACE2};border:1px solid {BORDER};border-radius:8px;padding:6px 10px;")
        eye2 = IconButton("👁","Show")
        eye2.clicked.connect(lambda: self._pw_val_lbl.setEchoMode(
            QLineEdit.EchoMode.Normal if self._pw_val_lbl.echoMode() == QLineEdit.EchoMode.Password
            else QLineEdit.EchoMode.Password))
        cp2 = IconButton("📋","Copy")
        cp2.clicked.connect(lambda: copy_to_clipboard(pw))
        pw_row_layout.addWidget(pw_lbl); pw_row_layout.addWidget(self._pw_val_lbl)
        pw_row_layout.addWidget(eye2); pw_row_layout.addWidget(cp2)
        vl.addLayout(pw_row_layout)

        score = details.get("strength_score",0)
        bar = StrengthBar(score); bar.setFixedHeight(6)
        vl.addWidget(bar)
        vl.addWidget(QLabel(f"Password strength: {strength_label(score)} ({score}/100)"))

        vl.addWidget(Divider())
        btn_row = QHBoxLayout()
        edit_btn  = QPushButton("Edit"); edit_btn.setFixedHeight(38)
        close_btn = QPushButton("Close"); close_btn.setProperty("flat","true"); close_btn.setFixedHeight(38)
        edit_btn.clicked.connect(lambda: (dlg.accept(), self._edit_account(acc)))
        close_btn.clicked.connect(dlg.reject)
        btn_row.addWidget(edit_btn); btn_row.addStretch(); btn_row.addWidget(close_btn)
        vl.addLayout(btn_row)
        dlg.exec()

    def _edit_account(self, acc):
        dlg = AccountDialog(self._user_id, self._master_password, account=acc, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load_accounts()

    def _copy_password(self, acc):
        pw = AccountController.get_account_details(
            self._user_id, acc["account_id"],
            include_password=True, master_password=self._master_password)
        if pw and pw.get("password"):
            copy_to_clipboard(pw["password"])
            # Brief visual feedback via title bar
            self.window().setWindowTitle("PPW — Copied! ✓")
            QTimer.singleShot(2000, lambda: self.window().setWindowTitle("PPW — Personal Password Manager"))

    def _delete_account(self, acc):
        reply = QMessageBox.question(
            self, "Delete Account",
            f"Delete  <b>{acc.get('title')}</b>?<br>This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            ok, msg = AccountController.delete_account(self._user_id, acc["account_id"])
            if ok:
                self._load_accounts()
            else:
                QMessageBox.critical(self, "Error", msg)

    # ── Security page ─────────────────────────────────────────────
    def _build_security_page(self):
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(28, 24, 28, 24)
        vl.setSpacing(16)

        header = QLabel("Security Overview")
        header.setStyleSheet(f"font-size:22px; font-weight:700; color:{TEXT};")
        vl.addWidget(header)

        # Stats grid
        self._sec_grid = QGridLayout()
        self._sec_grid.setSpacing(12)
        vl.addLayout(self._sec_grid)

        vl.addWidget(Divider())
        weak_header = QLabel("⚠️  Weak passwords  (score < 60)")
        weak_header.setStyleSheet(f"color:{WARNING}; font-weight:600; font-size:13px;")
        vl.addWidget(weak_header)

        self._weak_scroll = QScrollArea()
        self._weak_scroll.setWidgetResizable(True)
        self._weak_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._weak_container = QWidget()
        self._weak_layout    = QVBoxLayout(self._weak_container)
        self._weak_layout.setSpacing(6)
        self._weak_layout.addStretch()
        self._weak_scroll.setWidget(self._weak_container)
        vl.addWidget(self._weak_scroll)

        return w

    def _load_security(self):
        summary = SecurityController.get_security_summary(self._user_id)

        # Clear grid
        while self._sec_grid.count():
            item = self._sec_grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        cards = [
            ("Total Accounts",  str(summary.get("total_accounts", 0)),         ACCENT),
            ("Strong",          str(summary.get("password_strength",{}).get("strong",0)), SUCCESS),
            ("Medium",          str(summary.get("password_strength",{}).get("medium",0)), WARNING),
            ("Weak",            str(summary.get("password_strength",{}).get("weak",0)),   DANGER),
            ("2FA Coverage",    f"{summary.get('2fa_percentage',0)}%",           ACCENT),
            ("Old Passwords",   str(summary.get("old_passwords",0)),             WARNING),
        ]
        for i, (label, value, color) in enumerate(cards):
            frame = QFrame()
            frame.setProperty("card","true")
            fl = QVBoxLayout(frame)
            fl.setContentsMargins(16,14,16,14)
            v_lbl = QLabel(value)
            v_lbl.setStyleSheet(f"font-size:28px; font-weight:700; color:{color};")
            l_lbl = QLabel(label)
            l_lbl.setStyleSheet(f"color:{TEXT_MUTED}; font-size:12px;")
            fl.addWidget(v_lbl); fl.addWidget(l_lbl)
            self._sec_grid.addWidget(frame, i // 3, i % 3)

        # Weak passwords list
        while self._weak_layout.count() > 1:
            item = self._weak_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        weak_accounts = SecurityController.get_weak_passwords(self._user_id)
        for acc in weak_accounts:
            row = QHBoxLayout()
            title_lbl = QLabel(f"🔑  {acc['title']}")
            title_lbl.setStyleSheet(f"color:{TEXT};")
            score_lbl = QLabel(f"{acc['strength_score']}/100")
            score_lbl.setStyleSheet(f"color:{DANGER}; font-weight:600;")
            row.addWidget(title_lbl); row.addStretch(); row.addWidget(score_lbl)

            container = QFrame(); container.setProperty("card","true")
            container.setLayout(row)
            self._weak_layout.insertWidget(self._weak_layout.count()-1, container)

        if not weak_accounts:
            ok_lbl = QLabel("✅  All passwords are above the weak threshold.")
            ok_lbl.setStyleSheet(f"color:{SUCCESS}; padding:20px;")
            ok_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._weak_layout.insertWidget(0, ok_lbl)

    # ── Generator page ────────────────────────────────────────────
    def _build_generator_page(self):
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(28, 24, 28, 24)
        vl.setSpacing(20)

        title = QLabel("Password Generator")
        title.setStyleSheet(f"font-size:22px; font-weight:700; color:{TEXT};")
        vl.addWidget(title)

        card = QFrame(); card.setProperty("card","true")
        cl = QVBoxLayout(card); cl.setContentsMargins(24,24,24,24); cl.setSpacing(16)

        # Output display
        out_row = QHBoxLayout()
        self._gen_output = QLineEdit()
        self._gen_output.setReadOnly(True)
        self._gen_output.setFixedHeight(48)
        self._gen_output.setStyleSheet(f"font-family:monospace; font-size:16px; background:{SURFACE2}; border:1px solid {BORDER}; border-radius:8px; padding:0 14px; color:{TEXT};")
        out_row.addWidget(self._gen_output)
        copy_gen = QPushButton("📋 Copy"); copy_gen.setFixedHeight(48); copy_gen.setFixedWidth(90)
        copy_gen.clicked.connect(lambda: copy_to_clipboard(self._gen_output.text()))
        out_row.addWidget(copy_gen)
        cl.addLayout(out_row)

        self._gen_bar = StrengthBar(); self._gen_bar.setFixedHeight(8)
        self._gen_score_lbl = QLabel("")
        self._gen_score_lbl.setStyleSheet(f"color:{TEXT_MUTED}; font-size:12px;")
        cl.addWidget(self._gen_bar)
        cl.addWidget(self._gen_score_lbl)

        cl.addWidget(Divider())

        # Options
        opts = QFormLayout(); opts.setSpacing(12)

        self._gen_length = QLineEdit("20"); self._gen_length.setFixedHeight(38); self._gen_length.setFixedWidth(80)
        opts.addRow("Length:", self._gen_length)

        self._gen_upper  = QCheckBox("Uppercase  (A–Z)");     self._gen_upper.setChecked(True)
        self._gen_lower  = QCheckBox("Lowercase  (a–z)");     self._gen_lower.setChecked(True)
        self._gen_digits = QCheckBox("Digits  (0–9)");        self._gen_digits.setChecked(True)
        self._gen_syms   = QCheckBox("Symbols  (!@#$…)");     self._gen_syms.setChecked(True)
        for cb in (self._gen_upper, self._gen_lower, self._gen_digits, self._gen_syms):
            opts.addRow("", cb)
        cl.addLayout(opts)

        gen_btn = QPushButton("⚡  Generate Password"); gen_btn.setFixedHeight(44)
        gen_btn.clicked.connect(self._run_generator)
        cl.addWidget(gen_btn)

        vl.addWidget(card)
        vl.addStretch()

        self._run_generator()
        return w

    def _run_generator(self):
        try:
            length = int(self._gen_length.text() or 20)
            length = max(8, min(128, length))
        except ValueError:
            length = 20

        res = AccountController.generate_strong_password(
            length=length,
            use_uppercase=self._gen_upper.isChecked(),
            use_lowercase=self._gen_lower.isChecked(),
            use_digits=self._gen_digits.isChecked(),
            use_symbols=self._gen_syms.isChecked(),
        )
        pw = res.get("password","")
        score = res.get("strength_score", 0)
        self._gen_output.setText(pw)
        self._gen_bar.set_score(score)
        self._gen_score_lbl.setText(f"{strength_label(score)} — {score}/100")
        self._gen_score_lbl.setStyleSheet(f"color:{strength_color(score)}; font-size:12px;")

    def _logout(self):
        AuthController.logout(self._session_token, self._user_id)
        self.logout_requested.emit()


# ═════════════════════════════════════════════════════════════════════════════
#  Setup Wizard  (first-run MongoDB URI configuration)
# ═════════════════════════════════════════════════════════════════════════════

# ═════════════════════════════════════════════════════════════════════════════
#  Main Window  (orchestrates screens)
# ═════════════════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PPW — Personal Password Manager")
        self.setMinimumSize(1100, 680)

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._connect_and_start()

    def _connect_and_start(self):
        """Connect to the database silently, then show the auth screen.
        The MONGO_URI comes from the developer's .env — users never see it."""
        import os
        from pymongo.errors import OperationFailure, ConfigurationError

        uri = os.getenv("MONGO_URI", "")

        if not uri:
            self._show_db_error(
                "MONGO_URI is not configured.",
                "Add your MongoDB Atlas connection string to the .env file.\n"
                "See README.md → Development Setup for instructions."
            )
            return

        # Warn if the URI still has the placeholder password
        if "<db_password>" in uri or "<password>" in uri:
            self._show_db_error(
                "MongoDB password not set.",
                "Your MONGO_URI in .env still contains a placeholder.\n\n"
                "Replace  <db_password>  with your real Atlas database password."
            )
            return

        if not db_manager.is_connected:
            ok = db_manager.connect()
            if not ok:
                # Detect auth vs network error from the log/URI
                if "bad auth" in str(db_manager.client) if db_manager.client else False:
                    title = "Authentication failed."
                    msg = "Wrong username or password in MONGO_URI.\nCheck your .env file."
                else:
                    title = "Cannot connect to the server."
                    msg = ("PPW could not reach MongoDB Atlas.\n"
                           "Check your internet connection, and that the\n"
                           "password in MONGO_URI is correct.")
                self._show_db_error(title, msg)
                return
            db_manager.initialize_collections()
        self._init_auth()

    def _show_db_error(self, title: str = "Cannot connect to the server",
                       message: str = "Check your internet connection and try again."):
        """Show a clean error screen if the database can't be reached."""
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame(); card.setProperty("card", "true"); card.setFixedWidth(440)
        cl = QVBoxLayout(card); cl.setContentsMargins(40, 36, 40, 36); cl.setSpacing(14)

        ico = QLabel("⚠️"); ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico.setStyleSheet("font-size:40px; background:transparent;")
        cl.addWidget(ico)

        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet(f"font-size:18px; font-weight:700; color:{TEXT};")
        cl.addWidget(title_lbl)

        msg_lbl = QLabel(message)
        msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet(f"color:{TEXT_MUTED}; font-size:13px;")
        cl.addWidget(msg_lbl)

        retry = QPushButton("Retry")
        retry.setFixedHeight(42)
        retry.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        retry.clicked.connect(self._on_retry)
        cl.addWidget(retry)

        vl.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
        self._stack.addWidget(w)
        self._stack.setCurrentWidget(w)

    def _on_retry(self):
        # Remove the error screen and try again
        w = self._stack.currentWidget()
        self._stack.removeWidget(w)
        w.deleteLater()
        self._connect_and_start()

    def _init_auth(self):
        auth = AuthScreen()
        auth.authenticated.connect(self._on_auth)
        self._stack.addWidget(auth)
        self._stack.setCurrentWidget(auth)

    def _on_auth(self, user_id: str, session_token: str, master_password: str):
        extension_api.state.unlock(user_id, master_password)
        extension_api.state._on_focus = self._bring_to_front

        vault = VaultScreen(user_id, session_token, master_password)
        vault.logout_requested.connect(self._on_logout)
        self._stack.addWidget(vault)
        self._stack.setCurrentWidget(vault)

    def _on_logout(self):
        extension_api.state.lock()
        vault = self._stack.currentWidget()
        self._stack.removeWidget(vault)
        vault.deleteLater()
        self._init_auth()

    def _bring_to_front(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()


# ═════════════════════════════════════════════════════════════════════════════
#  Entry point
# ═════════════════════════════════════════════════════════════════════════════

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PPW")
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLE)

    # Start local API for the browser extension (localhost:27227)
    extension_api.start()
    app.aboutToQuit.connect(extension_api.stop)

    # Override palette for full dark mode
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor(BG))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Base,            QColor(SURFACE2))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(SURFACE))
    palette.setColor(QPalette.ColorRole.Text,            QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Button,          QColor(SURFACE))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()









