import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk


class Database:

    def __init__(self, db_name="library.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # 1. Books Table
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                book_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                total_copies INTEGER NOT NULL,
                available_copies INTEGER NOT NULL
            )
        """
        )
        # 2. Members Table (with Phone Number)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS members (
                member_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL
            )
        """
        )
        # 3. Borrow/Transactions Table
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                trans_id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                member_id INTEGER,
                issue_date TEXT DEFAULT (DATE('now')),
                return_date TEXT,
                status TEXT CHECK(status IN ('ISSUED', 'RETURNED')),
                FOREIGN KEY (book_id) REFERENCES books(book_id),
                FOREIGN KEY (member_id) REFERENCES members(member_id)
            )
        """
        )
        self.conn.commit()


class LibraryApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Library Management System")
        self.geometry("1020x680")
        self.configure(bg="#f4f6f9")

        self.db = Database()

        # Styles
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure(
            "TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[12, 6]
        )
        self.style.configure(
            "Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#e0e0e0"
        )
        self.style.configure("Treeview", font=("Segoe UI", 9), rowheight=25)

        # Tab Control
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tabs
        self.tab_books = ttk.Frame(self.notebook)
        self.tab_members = ttk.Frame(self.notebook)
        self.tab_borrow = ttk.Frame(self.notebook)
        self.tab_history = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_books, text="Book Inventory")
        self.notebook.add(self.tab_members, text="Members List")
        self.notebook.add(self.tab_borrow, text="Borrow / Issue Book")
        self.notebook.add(self.tab_history, text="Transaction Logs")

        # Setup Tab Contents
        self.setup_books_tab()
        self.setup_members_tab()
        self.setup_borrow_tab()
        self.setup_history_tab()

    # --- 1. BOOK MANAGEMENT TAB ---
    def setup_books_tab(self):
        form_frame = tk.LabelFrame(
            self.tab_books,
            text=" Manage Books ",
            font=("Segoe UI", 11, "bold"),
            bg="#ffffff",
            fg="#333333",
            padx=15,
            pady=15,
        )
        form_frame.place(x=10, y=10, width=320, height=600)

        tk.Label(
            form_frame, text="Book Title:", bg="#ffffff", font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", pady=(5, 0))
        self.ent_book_title = ttk.Entry(form_frame, width=35)
        self.ent_book_title.pack(fill="x", pady=2)

        tk.Label(
            form_frame, text="Author:", bg="#ffffff", font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", pady=(10, 0))
        self.ent_book_author = ttk.Entry(form_frame, width=35)
        self.ent_book_author.pack(fill="x", pady=2)

        tk.Label(
            form_frame,
            text="Total Copies:",
            bg="#ffffff",
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(10, 0))
        self.ent_book_copies = ttk.Entry(form_frame, width=35)
        self.ent_book_copies.pack(fill="x", pady=2)

        btn_add = tk.Button(
            form_frame,
            text="Add Book",
            bg="#28a745",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            command=self.add_book,
        )
        btn_add.pack(fill="x", pady=(20, 5))

        btn_delete_book = tk.Button(
            form_frame,
            text="Delete Selected Book",
            bg="#dc3545",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            command=self.delete_book,
        )
        btn_delete_book.pack(fill="x", pady=5)

        table_frame = tk.Frame(self.tab_books)
        table_frame.place(x=340, y=10, width=650, height=600)

        cols = ("ID", "Title", "Author", "Total", "Available")
        self.tree_books = ttk.Treeview(
            table_frame, columns=cols, show="headings", selectmode="browse"
        )
        for col, width in zip(cols, [40, 250, 180, 80, 80]):
            self.tree_books.heading(col, text=col)
            self.tree_books.column(col, width=width, anchor="center" if width <= 80 else "w")

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree_books.yview
        )
        self.tree_books.configure(yscroll=scrollbar.set)

        self.tree_books.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.load_books()

    def add_book(self):
        title = self.ent_book_title.get().strip()
        author = self.ent_book_author.get().strip()
        copies = self.ent_book_copies.get().strip()

        if not title or not author or not copies.isdigit():
            messagebox.showerror(
                "Error", "Please fill all fields correctly. Copies must be a number."
            )
            return

        copies_num = int(copies)
        self.db.cursor.execute(
            "INSERT INTO books (title, author, total_copies, available_copies) VALUES (?, ?, ?, ?)",
            (title, author, copies_num, copies_num),
        )
        self.db.conn.commit()

        self.ent_book_title.delete(0, tk.END)
        self.ent_book_author.delete(0, tk.END)
        self.ent_book_copies.delete(0, tk.END)

        messagebox.showinfo("Success", "Book added successfully!")
        self.load_books()
        self.refresh_borrow_combos()

    def delete_book(self):
        selected_item = self.tree_books.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a book to delete.")
            return

        book_id = self.tree_books.item(selected_item)["values"][0]

        confirm = messagebox.askyesno(
            "Confirm Delete", f"Are you sure you want to delete Book ID {book_id}?"
        )
        if confirm:
            self.db.cursor.execute(
                "DELETE FROM books WHERE book_id = ?", (book_id,)
            )
            self.db.conn.commit()
            messagebox.showinfo("Success", "Book deleted successfully!")
            self.load_books()
            self.refresh_borrow_combos()

    def load_books(self):
        for row in self.tree_books.get_children():
            self.tree_books.delete(row)
        self.db.cursor.execute(
            "SELECT book_id, title, author, total_copies, available_copies FROM books"
        )
        for row in self.db.cursor.fetchall():
            self.tree_books.insert("", tk.END, values=row)

    # --- 2. MEMBERS MANAGEMENT TAB ---
    def setup_members_tab(self):
        form_frame = tk.LabelFrame(
            self.tab_members,
            text=" Register New Member ",
            font=("Segoe UI", 11, "bold"),
            bg="#ffffff",
            fg="#333333",
            padx=15,
            pady=15,
        )
        form_frame.place(x=10, y=10, width=320, height=600)

        tk.Label(
            form_frame,
            text="Full Name:",
            bg="#ffffff",
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(5, 0))
        self.ent_member_name = ttk.Entry(form_frame, width=35)
        self.ent_member_name.pack(fill="x", pady=2)

        tk.Label(
            form_frame,
            text="Email Address:",
            bg="#ffffff",
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(10, 0))
        self.ent_member_email = ttk.Entry(form_frame, width=35)
        self.ent_member_email.pack(fill="x", pady=2)

        tk.Label(
            form_frame,
            text="Phone Number:",
            bg="#ffffff",
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(10, 0))
        self.ent_member_phone = ttk.Entry(form_frame, width=35)
        self.ent_member_phone.pack(fill="x", pady=2)

        btn_add_member = tk.Button(
            form_frame,
            text="Register Member",
            bg="#007bff",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            command=self.add_member,
        )
        btn_add_member.pack(fill="x", pady=(20, 5))

        btn_delete_member = tk.Button(
            form_frame,
            text="Delete Selected Member",
            bg="#dc3545",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            command=self.delete_member,
        )
        btn_delete_member.pack(fill="x", pady=5)

        table_frame = tk.Frame(self.tab_members)
        table_frame.place(x=340, y=10, width=650, height=600)

        cols = ("ID", "Name", "Email", "Phone")
        self.tree_members = ttk.Treeview(
            table_frame, columns=cols, show="headings", selectmode="browse"
        )
        for col, width in zip(cols, [50, 200, 230, 150]):
            self.tree_members.heading(col, text=col)
            self.tree_members.column(col, width=width)

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree_members.yview
        )
        self.tree_members.configure(yscroll=scrollbar.set)

        self.tree_members.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.load_members()

    def add_member(self):
        name = self.ent_member_name.get().strip()
        email = self.ent_member_email.get().strip()
        phone = self.ent_member_phone.get().strip()

        if not name or not email or not phone:
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        try:
            self.db.cursor.execute(
                "INSERT INTO members (name, email, phone) VALUES (?, ?, ?)",
                (name, email, phone),
            )
            self.db.conn.commit()
            self.ent_member_name.delete(0, tk.END)
            self.ent_member_email.delete(0, tk.END)
            self.ent_member_phone.delete(0, tk.END)
            messagebox.showinfo("Success", "Member registered successfully!")
            self.load_members()
            self.refresh_borrow_combos()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Member with this email already exists.")

    def delete_member(self):
        selected_item = self.tree_members.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a member to delete.")
            return

        member_id = self.tree_members.item(selected_item)["values"][0]

        confirm = messagebox.askyesno(
            "Confirm Delete", f"Are you sure you want to delete Member ID {member_id}?"
        )
        if confirm:
            self.db.cursor.execute(
                "DELETE FROM members WHERE member_id = ?", (member_id,)
            )
            self.db.conn.commit()
            messagebox.showinfo("Success", "Member deleted successfully!")
            self.load_members()
            self.refresh_borrow_combos()

    def load_members(self):
        for row in self.tree_members.get_children():
            self.tree_members.delete(row)
        self.db.cursor.execute("SELECT member_id, name, email, phone FROM members")
        for row in self.db.cursor.fetchall():
            self.tree_members.insert("", tk.END, values=row)

    # --- 3. BORROW / ISSUE TAB ---
    def setup_borrow_tab(self):
        # Left Side: Issue Book Form
        borrow_frame = tk.LabelFrame(
            self.tab_borrow,
            text=" Issue / Borrow Book ",
            font=("Segoe UI", 11, "bold"),
            bg="#ffffff",
            padx=15,
            pady=15,
        )
        borrow_frame.place(x=10, y=10, width=470, height=600)

        tk.Label(
            borrow_frame,
            text="Select Member (Name - Email):",
            bg="#ffffff",
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(10, 0))
        self.cmb_member = ttk.Combobox(borrow_frame, state="readonly", width=45)
        self.cmb_member.pack(fill="x", pady=5)

        tk.Label(
            borrow_frame,
            text="Select Book (Title - Available Copies):",
            bg="#ffffff",
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(10, 0))
        self.cmb_book = ttk.Combobox(borrow_frame, state="readonly", width=45)
        self.cmb_book.pack(fill="x", pady=5)

        btn_issue = tk.Button(
            borrow_frame,
            text="Issue Book to Member",
            bg="#17a2b8",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            command=self.issue_book,
        )
        btn_issue.pack(fill="x", pady=(25, 5))

        # Right Side: Return Book Form
        return_frame = tk.LabelFrame(
            self.tab_borrow,
            text=" Return Issued Book ",
            font=("Segoe UI", 11, "bold"),
            bg="#ffffff",
            padx=15,
            pady=15,
        )
        return_frame.place(x=500, y=10, width=480, height=600)

        tk.Label(
            return_frame,
            text="Transaction ID (Borrow Log ID):",
            bg="#ffffff",
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(10, 0))
        self.ent_return_trans_id = ttk.Entry(return_frame, width=35)
        self.ent_return_trans_id.pack(fill="x", pady=5)

        btn_return = tk.Button(
            return_frame,
            text="Return Book to Library",
            bg="#ffc107",
            fg="black",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            command=self.return_book,
        )
        btn_return.pack(fill="x", pady=(25, 5))

        self.refresh_borrow_combos()

    def refresh_borrow_combos(self):
        # Load Members into Dropdown
        self.db.cursor.execute("SELECT member_id, name, email, phone FROM members")
        members = self.db.cursor.fetchall()
        self.member_map = {}
        member_list = []
        for m in members:
            display_str = f"ID:{m[0]} | {m[1]} ({m[2]})"
            member_list.append(display_str)
            self.member_map[display_str] = m[0]
        self.cmb_member["values"] = member_list

        # Load Books into Dropdown
        self.db.cursor.execute(
            "SELECT book_id, title, available_copies FROM books WHERE available_copies > 0"
        )
        books = self.db.cursor.fetchall()
        self.book_map = {}
        book_list = []
        for b in books:
            display_str = f"ID:{b[0]} | {b[1]} (Available: {b[2]})"
            book_list.append(display_str)
            self.book_map[display_str] = b[0]
        self.cmb_book["values"] = book_list

    def issue_book(self):
        selected_member = self.cmb_member.get()
        selected_book = self.cmb_book.get()

        if not selected_member or not selected_book:
            messagebox.showerror(
                "Error", "Please select both Member and Book from the dropdown lists."
            )
            return

        member_id = self.member_map[selected_member]
        book_id = self.book_map[selected_book]

        # Deduct book count and add transaction log
        self.db.cursor.execute(
            "UPDATE books SET available_copies = available_copies - 1 WHERE book_id = ?",
            (book_id,),
        )
        self.db.cursor.execute(
            "INSERT INTO transactions (book_id, member_id, status) VALUES (?, ?, 'ISSUED')",
            (book_id, member_id),
        )
        self.db.conn.commit()

        self.cmb_member.set("")
        self.cmb_book.set("")

        messagebox.showinfo("Success", "Book issued successfully!")
        self.load_books()
        self.load_history()
        self.refresh_borrow_combos()

    def return_book(self):
        trans_id = self.ent_return_trans_id.get().strip()

        if not trans_id.isdigit():
            messagebox.showerror("Error", "Please enter a valid Transaction ID.")
            return

        self.db.cursor.execute(
            "SELECT book_id, status FROM transactions WHERE trans_id = ?", (trans_id,)
        )
        trans = self.db.cursor.fetchone()

        if not trans:
            messagebox.showerror("Error", "Transaction ID not found.")
            return
        if trans[1] == "RETURNED":
            messagebox.showinfo("Notice", "This book has already been returned.")
            return

        book_id = trans[0]
        self.db.cursor.execute(
            "UPDATE books SET available_copies = available_copies + 1 WHERE book_id = ?",
            (book_id,),
        )
        self.db.cursor.execute(
            "UPDATE transactions SET status = 'RETURNED', return_date = DATE('now') WHERE trans_id = ?",
            (trans_id,),
        )
        self.db.conn.commit()

        self.ent_return_trans_id.delete(0, tk.END)

        messagebox.showinfo("Success", "Book returned successfully!")
        self.load_books()
        self.load_history()
        self.refresh_borrow_combos()

    # --- 4. TRANSACTIONS TAB ---
    def setup_history_tab(self):
        btn_frame = tk.Frame(self.tab_history)
        btn_frame.pack(fill="x", padx=10, pady=5)

        btn_delete_trans = tk.Button(
            btn_frame,
            text="Delete Selected Transaction Log",
            bg="#dc3545",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            command=self.delete_transaction,
        )
        btn_delete_trans.pack(side="left", pady=5)

        table_frame = tk.Frame(self.tab_history)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = (
            "Trans ID",
            "Book Title",
            "Member Name",
            "Phone",
            "Email",
            "Issue Date",
            "Return Date",
            "Status",
        )
        self.tree_history = ttk.Treeview(
            table_frame, columns=cols, show="headings", selectmode="browse"
        )
        for col, width in zip(
            cols, [60, 200, 140, 110, 180, 90, 90, 80]
        ):
            self.tree_history.heading(col, text=col)
            self.tree_history.column(col, width=width, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree_history.yview
        )
        self.tree_history.configure(yscroll=scrollbar.set)

        self.tree_history.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.load_history()

    def delete_transaction(self):
        selected_item = self.tree_history.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a transaction to delete.")
            return

        trans_id = self.tree_history.item(selected_item)["values"][0]

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete Transaction ID {trans_id}?",
        )
        if confirm:
            self.db.cursor.execute(
                "DELETE FROM transactions WHERE trans_id = ?", (trans_id,)
            )
            self.db.conn.commit()
            messagebox.showinfo("Success", "Transaction record deleted successfully!")
            self.load_history()

    def load_history(self):
        for row in self.tree_history.get_children():
            self.tree_history.delete(row)

        query = """
            SELECT t.trans_id, b.title, m.name, m.phone, m.email, t.issue_date, COALESCE(t.return_date, '-'), t.status
            FROM transactions t
            JOIN books b ON t.book_id = b.book_id
            JOIN members m ON t.member_id = m.member_id
            ORDER BY t.trans_id DESC
        """
        self.db.cursor.execute(query)
        for row in self.db.cursor.fetchall():
            self.tree_history.insert("", tk.END, values=row)


if __name__ == "__main__":
    app = LibraryApp()
    app.mainloop()