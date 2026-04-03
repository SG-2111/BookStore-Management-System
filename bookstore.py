import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
import csv
import hashlib  # For password hashing
import os
from dotenv import load_dotenv
load_dotenv()

# Database Connection

def connect_db():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),  # Replace with your MySQL root password
            database=os.getenv("DB_NAME")
        )
        return connection
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error: {err}")
        return None

# Initialize Database

def init_db():
    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        # Create Books Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(100) UNIQUE,
                author VARCHAR(100),
                genre VARCHAR(100),
                year INT(4),
                price DECIMAL(10, 2),
                stock INT
            )
        """)

  # Create Users Table

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE,
                password_hash VARCHAR(255),
                salt VARCHAR(255)
            )
        """)
        # Add a default admin user if not exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", ("admin",))
        if cursor.fetchone()[0] == 0:
            salt = hashlib.sha256("admin".encode("utf-8")).hexdigest()
            hashed_password = hashlib.sha256((salt + "admin123").encode("utf-8")).hexdigest()
            cursor.execute("INSERT INTO users (username, password_hash, salt) VALUES (%s, %s, %s)", ("admin", hashed_password, salt))
        connection.commit()
        connection.close()

# Login Functionality

def login():
    def verify_credentials():
        username = username_entry.get()
        password = password_entry.get()

        if not username or not password:
            messagebox.showerror("Input Error", "Please enter both username and password!")
            return

        connection = connect_db()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT password_hash, salt FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()
            connection.close()

            if result:
                stored_hash, salt = result
                entered_hash = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
                if entered_hash == stored_hash:
                    messagebox.showinfo("Login Success", f"Welcome, {username}!")
                    login_window.destroy()  
                    main_menu()  
                else:
                    messagebox.showerror("Login Failed", "Invalid username or password!")
            else:
                messagebox.showerror("Login Failed", "Invalid username or password!")

    login_window = tk.Tk()
    login_window.title("Login")

    tk.Label(login_window, text="Username:").grid(row=0, column=0, pady=5)
    username_entry = tk.Entry(login_window)
    username_entry.grid(row=0, column=1, pady=5)

    tk.Label(login_window, text="Password:").grid(row=1, column=0, pady=5)
    password_entry = tk.Entry(login_window, show="*")
    password_entry.grid(row=1, column=1, pady=5)

    tk.Button(login_window, text="Login", command=verify_credentials).grid(row=2, columnspan=2, pady=10)

    login_window.mainloop()

# Main Menu

def main_menu():
    main_window = tk.Tk()
    main_window.title("Bookstore Management System")

    # Add Buttons

    tk.Button(main_window, text="Add Book", command=lambda: add_or_update_book(is_update=False)).grid(row=0, column=0, padx=5, pady=5)
    tk.Button(main_window, text="Search Books", command=search_books).grid(row=0, column=1, padx=5, pady=5)
    tk.Button(main_window, text="Update Book", command=lambda: add_or_update_book(is_update=True)).grid(row=0, column=2, padx=5, pady=5)
    tk.Button(main_window, text="Export Books to CSV", command=export_books_to_csv).grid(row=0, column=3, padx=5, pady=5)

    main_window.mainloop()




# Add or Update Book 

def add_or_update_book(is_update=False):
    def save_book():
        title = title_entry.get()
        author = author_entry.get()
        genre = genre_entry.get()
        year = year_entry.get()
        price = price_entry.get()
        stock = stock_entry.get()
        book_id = selected_book.get() if is_update else None

        # Validate Inputs

        if not (title and author and genre and year and price.isdigit() and stock.isdigit()):
            messagebox.showerror("Input Error", "All fields must be valid!")
            return
        if not (year.isdigit() and 1000 <= int(year) <= 9999):
            messagebox.showerror("Year Error", "Year must be a valid 4-digit number between 1000 and 9999!")
            return
        
        connection = connect_db()
        if connection:
            cursor = connection.cursor()
            if is_update and book_id:

                # Update Book

                cursor.execute("""
                    UPDATE books 
                    SET title = %s, author = %s, genre = %s, year = %s, price = %s, stock = %s 
                    WHERE id = %s
                """, (title, author, genre, int(year), float(price), int(stock), int(book_id.split(" - ")[0])))
                messagebox.showinfo("Success", "Book updated successfully!")
            else:

                # Add New Book with Duplicate Check

                cursor.execute("SELECT COUNT(*) FROM books WHERE title = %s", (title,))
                if cursor.fetchone()[0] > 0:
                    messagebox.showerror("Duplicate Error", "A book with this title already exists!")
                else:
                    cursor.execute(
                        "INSERT INTO books (title, author, genre, year, price, stock) VALUES (%s, %s, %s, %s, %s, %s)",
                        (title, author, genre, int(year), float(price), int(stock))
                          )
                    messagebox.showinfo("Success", "Book added successfully!")
            connection.commit()
            connection.close()
            add_update_window.destroy()

    add_update_window = tk.Toplevel()
    add_update_window.title("Update Book" if is_update else "Add Book")
    
    # If updating, prefill fields

    selected_book = None
    if is_update:
        connection = connect_db()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id, title FROM books")
            books = cursor.fetchall()
            connection.close()
            
            tk.Label(add_update_window, text="Select Book:").grid(row=0, column=0, pady=5)
            selected_book = ttk.Combobox(add_update_window, values=[f"{book[0]} - {book[1]}" for book in books])
            selected_book.grid(row=0, column=1, pady=5)

    tk.Label(add_update_window, text="Title:").grid(row=1, column=0, pady=5)
    title_entry = tk.Entry(add_update_window)
    title_entry.grid(row=1, column=1, pady=5)

    tk.Label(add_update_window, text="Author:").grid(row=2, column=0, pady=5)
    author_entry = tk.Entry(add_update_window)
    author_entry.grid(row=2, column=1, pady=5)

    tk.Label(add_update_window, text="Genre:").grid(row=3, column=0, pady=5)
    genre_entry = tk.Entry(add_update_window)
    genre_entry.grid(row=3, column=1, pady=5)

    tk.Label(add_update_window, text="Year:").grid(row=4, column=0, pady=5)
    year_entry = tk.Entry(add_update_window)
    year_entry.grid(row=4, column=1, pady=5)

    tk.Label(add_update_window, text="Price:").grid(row=5, column=0, pady=5)
    price_entry = tk.Entry(add_update_window)
    price_entry.grid(row=5, column=1, pady=5)

    tk.Label(add_update_window, text="Stock:").grid(row=6, column=0, pady=5)
    stock_entry = tk.Entry(add_update_window)
    stock_entry.grid(row=6, column=1, pady=5)

    tk.Button(add_update_window, text="Save", command=save_book).grid(row=7, columnspan=2, pady=10)
    
# Search Books 

def search_books():
    def search():
        search_by = search_by_combobox.get()
        search_value = search_value_entry.get()

        if not (search_by and search_value):
            messagebox.showerror("Input Error", "Please select a search criterion and enter a value!")
            return

        connection = connect_db()
        if connection:
            cursor = connection.cursor()
            query = f"SELECT id, title, author, genre, year, price, stock FROM books WHERE {search_by.lower()} LIKE %s"
            cursor.execute(query, (f"%{search_value}%",))
            results = cursor.fetchall()
            connection.close()

            # Display Results in Treeview

            for item in tree.get_children():
                tree.delete(item)
            for row in results:
                tree.insert("", tk.END, values=row)

    search_window = tk.Toplevel()
    search_window.title("Search Books")
    
    tk.Label(search_window, text="Search By:").grid(row=0, column=0, pady=5)
    search_by_combobox = ttk.Combobox(search_window, values=["Title", "Author", "Genre", "Year"])
    search_by_combobox.grid(row=0, column=1, pady=5)

    tk.Label(search_window, text="Enter Value:").grid(row=1, column=0, pady=5)
    search_value_entry = tk.Entry(search_window)
    search_value_entry.grid(row=1, column=1, pady=5)

    tk.Button(search_window, text="Search", command=search).grid(row=2, columnspan=2, pady=10)

# Display Search Results

    tree = ttk.Treeview(search_window, columns=("ID", "Title", "Author", "Genre", "Year", "Price", "Stock"), show="headings")
    tree.grid(row=3, column=0, columnspan=2, padx=10, pady=10)
    for col in ("ID", "Title", "Author", "Genre", "Year", "Price", "Stock"):
        tree.heading(col, text=col)


# Export Books to CSV

def export_books_to_csv():
    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM books")
        books = cursor.fetchall()
        connection.close()

        # Specify the CSV file name

        csv_file_name = "books_list.csv"
        with open(csv_file_name, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "Title", "Author", "Genre", "Year", "Price", "Stock"])
            writer.writerows(books)

        messagebox.showinfo("Success", f"Book list exported to {csv_file_name} successfully!")

# Initialize Database and Start Login

if __name__ == "__main__":
    init_db()
    login()  

