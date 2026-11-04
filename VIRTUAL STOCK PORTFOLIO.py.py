import tkinter as tk
from tkinter import messagebox, ttk
import mysql.connector
import yfinance as yf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import webbrowser
import requests
from bs4 import BeautifulSoup
from tkinter import font as tkfont


def format_market_cap(value):
    try:
        value = float(value)
    except:
        return str(value)

    if value >= 1_000_000_000_000:
        return f"{value/1_000_000_000_000:.2f} Trillion"
    elif value >= 1_000_000_000:
        return f"{value/1_000_000_000:.2f} Billion"
    elif value >= 1_000_000:
        return f"{value/1_000_000:.2f} Million"
    elif value >= 1_000:
        return f"{value/1_000:.2f} Thousand"
    else:
        return str(int(value))

# ===================== MySQL CONNECTION =====================
def Connect():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_password",
        database="STOCK_APP"
    )

# ===================== TABLES =====================
def ensure_tables():
    conn = Connect()
    cur = conn.cursor()

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE,
            password VARCHAR(50)
        )
    """)

    # Products table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products(
            id INT AUTO_INCREMENT PRIMARY KEY,
            brand_name VARCHAR(100) UNIQUE,
            ticker VARCHAR(20)
        )
    """)

    # Investments table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS investments(
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            product_id INT NOT NULL,
            capital DECIMAL(15,2) DEFAULT 0,
            quantity INT NOT NULL,
            buy_price DECIMAL(10,2) NOT NULL,
            buy_value DECIMAL(15,2) DEFAULT 0,
            sell_quantity INT DEFAULT 0,
            sell_price DECIMAL(10,2) DEFAULT 0,
            sell_value DECIMAL(15,2) DEFAULT 0,
            realized_pl DECIMAL(15,2) DEFAULT 0,
            total_tax DECIMAL(15,2) DEFAULT 0,
            net_pl DECIMAL(15,2) DEFAULT 0,
            returns DECIMAL(10,2) DEFAULT 0,
            buy_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)
    conn.commit()
    conn.close()

# ===================== AUTH =====================
def store(username, password):
    if not username or not password:
        messagebox.showwarning("Missing Info", "Please enter both fields.")
        return
    try:
        conn = Connect()
        cur = conn.cursor()
        cur.execute("INSERT INTO users(username, password) VALUES(%s,%s)", (username, password))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Account created successfully!")
    except mysql.connector.IntegrityError:
        messagebox.showwarning("User Exists", "That username is already taken.")
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"{err}")

def do_login(username, password, login_win):
    if not username or not password:
        messagebox.showwarning("Missing Info", "Please enter both fields.")
        return
    try:
        conn = Connect()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username=%s AND password=%s", (username, password))
        row = cur.fetchone()
        conn.close()
        if row:
            user_id = row[0]
            messagebox.showinfo("Success", f"Welcome {username}!")
            login_win.destroy()
            main_window(username, user_id)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"{err}")

# ===================== PRODUCTS =====================
def get_product_id(brand_name):
    conn = Connect()
    cur = conn.cursor()
    cur.execute("SELECT id, ticker FROM products WHERE brand_name LIKE %s", (f"%{brand_name}%",))
    row = cur.fetchone()
    conn.close()
    if row:
        return row[0], row[1]
    return None, None

# ===================== FETCH STOCK =====================
def fetch_stock_summary(ticker, brand_name):
    price = mcap = high52 = low52 = prev_close = 0.0
    try:
        t = yf.Ticker(ticker)
        fi = getattr(t, "fast_info", None)
        if fi:
            price = getattr(fi, "last_price", price) or price
            high52 = getattr(fi, "year_high", high52) or high52
            low52 = getattr(fi, "year_low", low52) or low52
        info = getattr(t, "info", {})
        price = info.get("currentPrice", price)
        mcap = info.get("marketCap", mcap)
        high52 = info.get("fiftyTwoWeekHigh", high52)
        low52 = info.get("fiftyTwoWeekLow", low52)
        prev_close = info.get("previousClose", prev_close)
    except Exception:
        pass
    
    # Format the market cap using the format_market_cap function
    formatted_mcap = format_market_cap(mcap) if mcap else "N/A"
    
    return {
        "brand": brand_name,
        "ticker": ticker,
        "price": price if price is not None else 0.0,
        "prev_close": prev_close,
        "market_cap": formatted_mcap,  # Use the formatted market cap
        "high52": high52,
        "low52": low52
    }

# ===================== VIRTUAL INVEST =====================
def virtual_invest_window(user_id, product_id, brand_name, ticker, current_price):
    win = tk.Toplevel()
    win.title("Virtual Invest")
    win.geometry("1200x800")

    # --- Product Info Labels ---
    tk.Label(win, text=f"Brand: {brand_name}", font=("Poiret One", 14)).pack(pady=2)
    tk.Label(win, text=f"Ticker: {ticker}", font=("Poiret One", 14)).pack(pady=2)
    tk.Label(win, text=f"Current Price: {current_price}", font=("Poiret One", 14)).pack(pady=2)

    status_label = tk.Label(win, text="", font=("Poiret One", 12))
    status_label.pack(pady=5)

    # --- Main Input Frame ---
    main_frame = tk.Frame(win)
    main_frame.pack(pady=5)

    # --- Capital Section (LEFT CORNER) ---
    capital_frame = tk.Frame(main_frame)
    capital_frame.pack(side="left", padx=10)

    tk.Label(capital_frame, text="Capital:", font=("Poiret One", 12)).pack(anchor="w")
    capital_entry = tk.Entry(capital_frame, font=("Poiret One", 12), width=12)
    capital_entry.pack(pady=2)
    
    # Set Capital button
    def set_capital():
        capital = capital_entry.get().strip()
        if not capital:
            status_label.config(text="Please enter capital amount", fg="red")
            return
            
        try:
            capital_val = float(capital)
            conn = Connect()
            if conn is None:
                status_label.config(text="Database connection error", fg="red")
                return
                
            cur = conn.cursor()
            try:
                # Check if user already has capital record
                cur.execute("SELECT COUNT(*) FROM user_capital WHERE user_id=%s", (user_id,))
                if cur.fetchone()[0] > 0:
                    # Update existing capital
                    cur.execute("UPDATE user_capital SET initial_capital=%s WHERE user_id=%s", 
                               (capital_val, user_id))
                else:
                    # Insert new capital record
                    cur.execute("INSERT INTO user_capital (user_id, initial_capital) VALUES (%s, %s)", 
                               (user_id, capital_val))
                
                conn.commit()
                status_label.config(text="Capital set successfully!", fg="green")
                load_investments()  # Refresh to update balance
                
            except Exception as e:
                conn.rollback()
                status_label.config(text=f"Error setting capital: {str(e)}", fg="red")
            finally:
                cur.close()
                conn.close()
                
        except ValueError:
            status_label.config(text="Please enter a valid number", fg="red")
    
    tk.Button(capital_frame, text="Set Capital", font=("Poiret One", 10), 
              bg="blue", fg="white", command=set_capital).pack(pady=2)

    # Capital Balance label
    capital_balance_label = tk.Label(capital_frame, text="Available Balance: 0.00", font=("Poiret One", 12), fg="orange")
    capital_balance_label.pack(pady=2)

    # --- Trading Inputs Section (HORIZONTAL BESIDE CAPITAL) ---
    trading_frame = tk.Frame(main_frame)
    trading_frame.pack(side="left", padx=20)

    # Buy Section
    buy_frame = tk.Frame(trading_frame)
    buy_frame.pack(side="left", padx=10)

    tk.Label(buy_frame, text="BUY", font=("Poiret One", 12, "bold")).pack()
    
    tk.Label(buy_frame, text="Qty:", font=("Poiret One", 12)).pack(anchor="w")
    quantity_entry = tk.Entry(buy_frame, font=("Poiret One", 12), width=10)
    quantity_entry.pack(pady=2)

    tk.Label(buy_frame, text="Price:", font=("Poiret One", 12)).pack(anchor="w")
    buy_price_entry = tk.Entry(buy_frame, font=("Poiret One", 12), width=10)
    buy_price_entry.pack(pady=2)
    buy_price_entry.insert(0, str(current_price))

    # Sell Section
    sell_frame = tk.Frame(trading_frame)
    sell_frame.pack(side="left", padx=10)

    tk.Label(sell_frame, text="SELL", font=("Poiret One", 12, "bold")).pack()
    
    tk.Label(sell_frame, text="Qty:", font=("Poiret One", 12)).pack(anchor="w")
    sell_quantity_entry = tk.Entry(sell_frame, font=("Poiret One", 12), width=10)
    sell_quantity_entry.pack(pady=2)

    tk.Label(sell_frame, text="Price:", font=("Poiret One", 12)).pack(anchor="w")
    sell_price_entry = tk.Entry(sell_frame, font=("Poiret One", 12), width=10)
    sell_price_entry.pack(pady=2)

    # --- Investment Table ---
    columns = ("ID", "Product", "Capital", "Buy Qty", "Avg Price", "Buy Value",
               "Sell Qty", "Sell Price", "Sell Value", "Realized P/L",
               "Total Tax", "Net P/L", "Returns", "Buy Date", "Balance")

    tree_frame = tk.Frame(win)
    tree_frame.pack(pady=10, fill="both", expand=True)
    
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)
    
    # Define column widths
    column_widths = {
        "ID": 40, "Product": 100, "Capital": 80, "Buy Qty": 70, "Avg Price": 80,
        "Buy Value": 90, "Sell Qty": 70, "Sell Price": 80, "Sell Value": 90,
        "Realized P/L": 90, "Total Tax": 80, "Net P/L": 80, "Returns": 70,
        "Buy Date": 100, "Balance": 90
    }
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=column_widths[col], anchor="center")
    
    # Scrollbar
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    # Grid layout
    tree.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    
    # Configure grid weights
    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(0, weight=1)

    # --- Ensure user_capital table exists ---
    def create_user_capital_table():
        conn = Connect()
        if conn is None:
            return False
        cur = conn.cursor()
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_capital (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    initial_capital DECIMAL(15,2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_user (user_id)
                )
            """)
            conn.commit()
            return True
        except Exception as e:
            print(f"Error creating table: {e}")
            return False
        finally:
            cur.close()
            conn.close()

    create_user_capital_table()

    # --- Load initial capital into entry field ---
    def load_initial_capital():
        conn = Connect()
        if conn is None:
            return
            
        cur = conn.cursor()
        try:
            cur.execute("SELECT initial_capital FROM user_capital WHERE user_id=%s", (user_id,))
            row = cur.fetchone()
            if row:
                capital_entry.delete(0, tk.END)
                capital_entry.insert(0, str(row[0]))
                print(f"Loaded initial capital: {row[0]}")
            else:
                print("No capital found in user_capital table")
        except Exception as e:
            print(f"Error loading initial capital: {e}")
        finally:
            cur.close()
            conn.close()

    # --- Update balance and Net P/L ---
    def update_balance():
        conn = Connect()
        if conn is None:
            return 0, 0
            
        cur = conn.cursor()
        initial_capital = 0
        try:
            # Try to get capital from user_capital table
            cur.execute("SELECT initial_capital FROM user_capital WHERE user_id=%s", (user_id,))
            row = cur.fetchone()
            if row:
                initial_capital = float(row[0])
        except Exception as e:
            print(f"Error getting initial capital: {e}")
            initial_capital = 0

        # Calculate total invested
        total_invested = 0
        try:
            cur.execute("SELECT SUM(buy_value) FROM investments WHERE user_id=%s", (user_id,))
            row_sum = cur.fetchone()
            if row_sum and row_sum[0]:
                total_invested = float(row_sum[0])
        except Exception as e:
            print(f"Error calculating total invested: {e}")

        # Calculate available balance
        available_balance = max(initial_capital - total_invested, 0)
        capital_balance_label.config(text=f"Available Balance: {available_balance:.2f}")

        # Calculate total net P/L
        total_net_pl = 0
        try:
            cur.execute("SELECT SUM(net_pl) FROM investments WHERE user_id=%s", (user_id,))
            row_net = cur.fetchone()
            if row_net and row_net[0]:
                total_net_pl = float(row_net[0])
        except Exception as e:
            print(f"Error calculating net P/L: {e}")

        # Update Net P/L label with color
        if total_net_pl > 0:
            net_pl_label.config(text=f"Net P/L: +{total_net_pl:.2f}", fg="green")
        elif total_net_pl < 0:
            net_pl_label.config(text=f"Net P/L: {total_net_pl:.2f}", fg="red")
        else:
            net_pl_label.config(text=f"Net P/L: {total_net_pl:.2f}", fg="blue")

        cur.close()
        conn.close()
        return initial_capital, available_balance

    # --- Load investments into table ---
    def load_investments():
        conn = Connect()
        if conn is None:
            return
            
        cur = conn.cursor()
        rows = []
        try:
            cur.execute("""
                SELECT i.id, p.brand_name, i.capital, i.quantity, i.buy_price, i.buy_value,
                       i.sell_quantity, i.sell_price, i.sell_value, i.realized_pl,
                       i.total_tax, i.net_pl, i.returns, i.buy_date
                FROM investments i
                JOIN products p ON i.product_id = p.id
                WHERE i.user_id = %s 
                ORDER BY i.id ASC
            """, (user_id,))
            rows = cur.fetchall()
        except Exception as e:
            print(f"Error loading investments: {e}")
        finally:
            cur.close()
            conn.close()

        # Clear existing items
        tree.delete(*tree.get_children())
        initial_capital, _ = update_balance()
        running_balance = 0
        
        for r in rows:
            running_balance += float(r[5])  # buy_value
            balance_after = max(initial_capital - running_balance, 0)
            
            # Format values
            net_pl = float(r[11]) if r[11] else 0
            returns = float(r[12]) if r[12] else 0
            
            formatted_values = (
                r[0],  # ID
                r[1],  # Product
                f"{float(r[2]):.2f}",  # Capital
                r[3],  # Buy Qty
                f"{float(r[4]):.2f}",  # Avg Price
                f"{float(r[5]):.2f}",  # Buy Value
                r[6],  # Sell Qty
                f"{float(r[7]):.2f}" if r[7] else "0.00",  # Sell Price
                f"{float(r[8]):.2f}" if r[8] else "0.00",  # Sell Value
                f"+{float(r[9]):.2f}" if r[9] and float(r[9]) > 0 else f"{float(r[9]):.2f}" if r[9] else "0.00",  # Realized P/L
                f"{float(r[10]):.2f}" if r[10] else "0.00",  # Total Tax
                f"+{net_pl:.2f}" if net_pl > 0 else f"{net_pl:.2f}",  # Net P/L
                f"+{returns:.2f}%" if returns > 0 else f"{returns:.2f}%",  # Returns
                r[13].strftime("%Y-%m-%d") if r[13] else "",  # Buy Date
                f"{balance_after:.2f}"  # Balance
            )
            
            item_id = tree.insert("", "end", values=formatted_values)
            
            # Color code based on profit/loss
            if net_pl > 0:
                tree.item(item_id, tags=("profit",))
            elif net_pl < 0:
                tree.item(item_id, tags=("loss",))
        
        # Configure tags
        tree.tag_configure("profit", foreground="green")
        tree.tag_configure("loss", foreground="red")

    # --- Add investment ---
    def add_investment():
        capital = capital_entry.get().strip()
        qty = quantity_entry.get().strip()
        buy_price = buy_price_entry.get().strip()
        sell_qty = sell_quantity_entry.get().strip() or "0"
        sell_price = sell_price_entry.get().strip() or "0"
        
        if not capital or not qty or not buy_price:
            status_label.config(text="Capital, Buy Qty and Buy Price required", fg="red")
            return
            
        try:
            capital_val = float(capital)
            qty_val = int(qty)
            buy_price_val = float(buy_price)
            sell_qty_val = int(sell_qty)
            sell_price_val = float(sell_price)

            buy_value = qty_val * buy_price_val
            sell_value = sell_qty_val * sell_price_val
            realized_pl = sell_value - (sell_qty_val * buy_price_val)
            total_tax = realized_pl * 0.0034825 if realized_pl > 0 else 0
            net_pl = realized_pl - total_tax
            returns = (net_pl / buy_value * 100) if buy_value > 0 else 0
        except ValueError:
            status_label.config(text="Please enter valid numbers", fg="red")
            return

        conn = Connect()
        if conn is None:
            status_label.config(text="Database connection error", fg="red")
            return
            
        cur = conn.cursor()
        try:
            # Check if this is the first investment
            cur.execute("SELECT COUNT(*) FROM investments WHERE user_id=%s", (user_id,))
            count = cur.fetchone()[0]
            
            # Insert investment
            cur.execute("""
                INSERT INTO investments 
                (user_id, product_id, capital, quantity, buy_price, buy_value, 
                 sell_quantity, sell_price, sell_value, realized_pl, 
                 total_tax, net_pl, returns, buy_date) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (user_id, product_id, capital_val, qty_val, buy_price_val, buy_value, 
                  sell_qty_val, sell_price_val, sell_value, realized_pl, 
                  total_tax, net_pl, returns))
            
            # If first investment, save to user_capital
            if count == 0:
                try:
                    cur.execute("INSERT INTO user_capital (user_id, initial_capital) VALUES (%s, %s)", 
                               (user_id, capital_val))
                    print(f"Saved initial capital: {capital_val}")
                except Exception as e:
                    print(f"Error saving initial capital: {e}")
                    # Try update if insert fails (user already exists)
                    try:
                        cur.execute("UPDATE user_capital SET initial_capital=%s WHERE user_id=%s", 
                                   (capital_val, user_id))
                        print(f"Updated initial capital: {capital_val}")
                    except Exception as e2:
                        print(f"Error updating capital: {e2}")
            
            conn.commit()
            status_label.config(text="Investment added successfully!", fg="green")
            
        except Exception as e:
            conn.rollback()
            status_label.config(text=f"Database error: {str(e)}", fg="red")
        finally:
            cur.close()
            conn.close()

        # Clear input fields
        quantity_entry.delete(0, tk.END)
        sell_quantity_entry.delete(0, tk.END)
        sell_price_entry.delete(0, tk.END)
        
        # Refresh data
        load_investments()

    # --- Delete selected investment ---
    def delete_selected():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an investment to delete")
            return
            
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected investment?")
        if not confirm:
            return
            
        conn = Connect()
        if conn is None:
            messagebox.showerror("Error", "Database connection failed")
            return
            
        cur = conn.cursor()
        try:
            for item in selected:
                inv_id = tree.item(item, "values")[0]
                cur.execute("DELETE FROM investments WHERE id=%s AND user_id=%s", (inv_id, user_id))
            conn.commit()
            messagebox.showinfo("Success", "Investment(s) deleted successfully")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to delete investment: {str(e)}")
        finally:
            cur.close()
            conn.close()
            
        load_investments()

    # --- Delete all investments ---
    def delete_all():
        confirm = messagebox.askyesno("Confirm Delete All", "Are you sure you want to delete ALL investments?")
        if not confirm:
            return
            
        conn = Connect()
        if conn is None:
            messagebox.showerror("Error", "Database connection failed")
            return
            
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM investments WHERE user_id=%s", (user_id,))
            cur.execute("DELETE FROM user_capital WHERE user_id=%s", (user_id,))
            conn.commit()
            messagebox.showinfo("Success", "All investments deleted successfully")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to delete investments: {str(e)}")
        finally:
            cur.close()
            conn.close()
            
        load_investments()

    # --- Buttons Frame ---
    btn_frame = tk.Frame(win)
    btn_frame.pack(fill="x", pady=10)
    
    # Delete All button on left
    tk.Button(btn_frame, text="Delete All", font=("Poiret One", 14), 
              bg="red", fg="white", command=delete_all).pack(side="left", padx=10)
    
    # Net P/L label (LEFT of Add Investment button)
    net_pl_label = tk.Label(btn_frame, text="Net P/L: 0.00", font=("Poiret One", 14), fg="blue")
    net_pl_label.pack(side="left", padx=(0, 20))
    
    # Add Investment button on right
    tk.Button(btn_frame, text="Add Investment", font=("Poiret One", 14), 
              bg="#228B22", fg="white", command=add_investment).pack(side="right", padx=10)

    # --- Right-click menu ---
    menu = tk.Menu(win, tearoff=0, bg="red", fg="white", font=("Cutive Mono", 10))
    menu.add_command(label="Delete", command=delete_selected)
    
    def show_menu(event):
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            menu.post(event.x_root, event.y_root)
    
    tree.bind("<Button-3>", show_menu)

    # Initial load
    load_initial_capital()  # Load capital into entry field
    load_investments()      # Load investments and update balance
# ===================== FEATURE 1 =====================
def feature_1_window(user_id):
    win = tk.Toplevel()
    win.title("Feature_1 - Get Stock")
    win.geometry("1200x800")

    frame_top = tk.Frame(win)
    frame_top.pack(pady=10)

    tk.Label(frame_top, text="Enter Product/Brand Name:", font=("Poiret One", 14)).pack(side=tk.LEFT, padx=5)
    entry = tk.Entry(frame_top, font=("Poiret One", 14))
    entry.pack(side=tk.LEFT, padx=5)

    output_box = tk.Text(win, width=80, height=10, font=("Consolas", 11))
    output_box.pack(pady=10)
    output_box.configure(state="disabled")

    def search_stock():
        brand_name_val = entry.get().strip()
        if not brand_name_val:
            messagebox.showwarning("Input Error", "Please enter a brand name")
            return
        product_id, ticker_val = get_product_id(brand_name_val)
        if product_id is None:
            messagebox.showwarning("Not Found", f"No product named '{brand_name_val}' in DB")
            return
        stock_data = fetch_stock_summary(ticker_val, brand_name_val)
        price_safe = stock_data['price'] if stock_data['price'] is not None else 0.0

        output_box.configure(state="normal")
        output_box.delete(1.0, tk.END)
        summary_text = (
            f"Brand: {stock_data['brand']}\nTicker: {stock_data['ticker']}\n"
            f"Current Price: {price_safe}\nPrevious Close: {stock_data['prev_close']}\n"
            f"Market Cap: {stock_data['market_cap']}\n52W High: {stock_data['high52']}\n52W Low: {stock_data['low52']}\n"
        )
        output_box.insert(tk.END, summary_text)
        output_box.configure(state="disabled")

        if hasattr(win, 'virtual_btn') and win.virtual_btn.winfo_exists():
            win.virtual_btn.destroy()
        win.virtual_btn = tk.Button(win, text="Virtual Invest", font=("Poiret One", 14), bg="#FF8C00", fg="white",
                                    width=18,
                                    command=lambda: virtual_invest_window(user_id, product_id, brand_name_val, ticker_val, price_safe))
        win.virtual_btn.pack(pady=5)

    tk.Button(frame_top, text="Search Stock", font=("Poiret One", 14), bg="#228B22", fg="white",
              width=15, command=search_stock).pack(side=tk.LEFT, padx=5)

# ===================== MARKET DASHBOARD =====================


class MarketDashboard:
    def __init__(self, user_id):
        self.user_id = user_id
        self.root = tk.Toplevel()
        self.root.title("Live Market Dashboard")
        self.root.geometry("1200x800")
        self.root.configure(bg="#1e1e1e")

        # ✅ Stock and Commodity lists
        self.indian_stocks = [ 
            {"brand": "NIFTY 50", "ticker": "^NSEI"},   # 🔥 Added here
            {"brand": "TCS", "ticker": "TCS.NS"},
            {"brand": "Reliance", "ticker": "RELIANCE.NS"},
            {"brand": "HDFC Bank", "ticker": "HDFCBANK.NS"},
            {"brand": "Infosys", "ticker": "INFY.NS"},
            {"brand": "ICICI Bank", "ticker": "ICICIBANK.NS"},
            {"brand": "Larsen & Toubro", "ticker": "LT.NS"},
            {"brand": "Hindustan Unilever", "ticker": "HINDUNILVR.NS"},
            {"brand": "Kotak Bank", "ticker": "KOTAKBANK.NS"},
            {"brand": "Axis Bank", "ticker": "AXISBANK.NS"},
            {"brand": "Mahindra & Mahindra", "ticker": "M&M.NS"},
        ]
        self.commodities = [
            {"brand": "Gold", "ticker": "GC=F"},
            {"brand": "Silver", "ticker": "SI=F"},
        ]

        # Scrollable canvas
        canvas = tk.Canvas(self.root, bg="#1e1e1e")
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        self.inner_frame = tk.Frame(canvas, bg="#1e1e1e")
        self.inner_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ✅ Bind mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")  # Windows/mac
        def _on_linux_scroll(event):
            if event.num == 4:  # scroll up
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:  # scroll down
                canvas.yview_scroll(1, "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", _on_linux_scroll)
        canvas.bind_all("<Button-5>", _on_linux_scroll)

        # Load the market data initially
        self.fetch_and_display_market()

        # ✅ Auto-refresh every 60 sec
        self.root.after(60000, self.refresh_data)

    # ---------------- STOCK DATA FETCH ----------------
    def fetch_stock_summary(self, ticker, brand):
        price = prev_close = high52 = low52 = 0
        data = None
        try:
            t = yf.Ticker(ticker)
            fi = getattr(t, "fast_info", None)
            if fi:
                price = getattr(fi, "last_price", price) or price
            info = getattr(t, "info", {})
            price = info.get("currentPrice", price)
            prev_close = info.get("previousClose", prev_close)
            high52 = info.get("fiftyTwoWeekHigh", high52)
            low52 = info.get("fiftyTwoWeekLow", low52)
            data = t.history(period="5d", interval="15m")
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
        return {"brand": brand, "ticker": ticker, "price": price or 0.0,
                "prev_close": prev_close or 0.0, "high52": high52, "low52": low52, "data": data}

    # ---------------- SUGGESTIONS ----------------
    def get_suggestion(self, stock):
        last_price = stock["price"]
        prev_close = stock["prev_close"]
        high52 = stock.get("high52")
        low52 = stock.get("low52")
        ticker = stock["ticker"]
        data = stock.get("data")

        change = ((last_price - prev_close) / prev_close * 100) if prev_close else 0
        suggestion = "Stable market"

        if data is not None and len(data['Close']) >= 3:
            last3 = data['Close'][-3:]
            if all(x < y for x, y in zip(last3, last3[1:])):
                trend = "Uptrend"
            elif all(x > y for x, y in zip(last3, last3[1:])):
                trend = "Downtrend"
            else:
                trend = "Sideways"
        else:
            trend = "Stable"

        if trend == "Uptrend" and change > 0.5:
            suggestion = "Potential Buy – Uptrend strong"
        elif trend == "Downtrend" and change < -0.5:
            suggestion = "Consider waiting – Downtrend"
        elif abs(change) < 0.5:
            suggestion = "Hold – Stable market"
        else:
            suggestion = "High volatility – Trade carefully"

        if high52 and last_price >= 0.95 * high52:
            suggestion += " | Near 52W High – Be cautious"
        elif low52 and last_price <= 1.05 * low52:
            suggestion += " | Near 52W Low – Might be undervalued"

        if ticker in ["GC=F", "SI=F"]:
            if change > 0:
                suggestion = "Positive momentum – Consider investing"
            else:
                suggestion = "Market dip – Monitor closely"

        return suggestion

    # ---------------- DISPLAY PANEL ----------------
    def display_stock_panel(self, stock, row, col=0):
        panel = tk.Frame(
            self.inner_frame,
            bg="#2e2e2e",
            padx=5, pady=5,
            width=500,   # fixed width
            height=200   # height for graph
        )
        panel.grid(row=row, column=col, pady=5, padx=20, sticky="nw")
        panel.grid_propagate(False)

        sugg = self.get_suggestion(stock)
        last_price = stock["price"]

        # 🔹 First line: Brand, ticker, and price
        tk.Label(
            panel,
            text=f"{stock['brand']} ({stock['ticker']}) - {last_price:.2f}",
            font=("Poiret One", 14, "bold"),
            fg="white", bg="#2e2e2e", anchor="w"
        ).pack(anchor="w")

        # 🔹 Second line: Suggestion
        tk.Label(
            panel,
            text=sugg,
            font=("Poiret One", 12),
            fg="Orange", bg="#2e2e2e",
            wraplength=480, justify="left", anchor="w"
        ).pack(anchor="w", pady=(0, 5))

        # 🔹 Third line: Graph
        try:
            data = stock.get("data")
            if data is not None and not data.empty:
                fig, ax = plt.subplots(figsize=(4.5, 1.8))
                color = "green" if last_price > stock["prev_close"] else "red"
                ax.plot(data['Close'], color=color, linewidth=1.5)
                ax.set_xticks([])
                ax.set_yticks([])
                fig.patch.set_facecolor('#2e2e2e')
                ax.set_facecolor('#2e2e2e')

                canvas = FigureCanvasTkAgg(fig, master=panel)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True)

                plt.close(fig)
        except Exception as e:
            error_label = tk.Label(panel, text=f"Graph error: {e}", fg="red", bg="#2e2e2e")
            error_label.pack()

    # ---------------- FETCH + DISPLAY ----------------
    def fetch_and_display_market(self):
        for w in self.inner_frame.winfo_children():
            w.destroy()

        # Headers
        tk.Label(self.inner_frame, text="Top Indian Stocks", font=("Poiret One", 16),
                 fg="yellow", bg="#1e1e1e").grid(row=0, column=0, sticky="w", pady=5, padx=10)
        tk.Label(self.inner_frame, text="Commodities", font=("Poiret One", 16),
                 fg="orange", bg="#1e1e1e").grid(row=0, column=1, sticky="w", pady=5, padx=20)

        # Row-wise display
        max_len = max(len(self.indian_stocks), len(self.commodities))
        for i in range(max_len):
            if i < len(self.indian_stocks):
                summary = self.fetch_stock_summary(self.indian_stocks[i]["ticker"], self.indian_stocks[i]["brand"])
                self.display_stock_panel(summary, row=i+1, col=0)
            if i < len(self.commodities):
                summary = self.fetch_stock_summary(self.commodities[i]["ticker"], self.commodities[i]["brand"])
                self.display_stock_panel(summary, row=i+1, col=1)

        self.inner_frame.grid_columnconfigure(0, weight=1)
        self.inner_frame.grid_columnconfigure(1, weight=1)

    # ---------------- REFRESH ----------------
    def refresh_data(self):
        self.fetch_and_display_market()
        self.root.after(60000, self.refresh_data)  # refresh again in 60 sec

# ========== FETCH NEWS FROM MONEYCONTROL ==========
def fetch_moneycontrol_news():
    url = "https://www.moneycontrol.com/news/business/markets/"
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        headlines = []
        for item in soup.select("li.clearfix a"):
            title = item.get_text(strip=True)
            link = item["href"]
            if title and link and "news" in link:
                headlines.append((title, link))
            if len(headlines) >= 10:
                break
        return headlines
    except Exception as e:
        print("Error fetching news:", e)
        return []

# ========== OPEN ARTICLE IN BROWSER ==========
def open_article(url):
    webbrowser.open(url)

# ========== CREATE NEWS WINDOW ==========
def open_news_window():
    news_win = tk.Toplevel()
    news_win.title("Top Stock Market News (Moneycontrol)")
    news_win.geometry("800x600")
    news_win.configure(bg="black")

    # Fonts
    heading_font = tkfont.Font(family="Cutive Mono", size=20, weight="bold")
    readmore_font = tkfont.Font(family="Poiret One", size=12, underline=True)

    # Scrollable frame setup
    container = ttk.Frame(news_win)
    canvas = tk.Canvas(container, width=780, height=580, bg="black", highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="black")

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0,0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    container.pack(fill="both", expand=True)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Enable Mousewheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    news_win.bind_all("<MouseWheel>", _on_mousewheel)  # Windows / Mac
    news_win.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux scroll up
    news_win.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))   # Linux scroll down

    # Heading
    tk.Label(scrollable_frame, text="Stock Market News", 
             font=heading_font, fg="Gold", bg="black").pack(pady=10)

    articles = fetch_moneycontrol_news()

    if not articles:
        tk.Label(scrollable_frame, text="⚠ Could not fetch news. Please try again.", 
                 font=("Cutive Mono", 12), fg="red", bg="black").pack(pady=20)
        return

    for idx, (title, link) in enumerate(articles, start=1):
        # Headline
        tk.Label(scrollable_frame, text=f"{idx}. {title}", 
                 font=("Poiret One", 14), wraplength=750, justify="left", 
                 fg="#EAB875", bg="black").pack(anchor="w", padx=10, pady=(10,0))

        # Read More link
        read_link = tk.Label(scrollable_frame, text="Read More", font=readmore_font, 
                             fg="#D3E3EE", bg="black", cursor="hand2")
        read_link.pack(anchor="w", padx=20, pady=(0,10))
        read_link.bind("<Button-1>", lambda e, url=link: open_article(url))


# ===================== MAIN WINDOW =====================
# ===================== MAIN WINDOW =====================
def main_window(username, user_id):
    Main_Window = tk.Tk()
    Main_Window.title("StockInsight Pro - Investment Dashboard")
    Main_Window.geometry("1200x800")
    Main_Window.configure(bg="#1e1e2e")

    # Custom fonts
    title_font = ("Cutive Mono", 24, "bold")
    welcome_font = ("Poiret One", 20, "bold")
    heading_font = ("Poiret One", 18, "bold")
    subheading_font = ("Poiret One", 14, "bold")
    normal_font = ("Poiret One", 12)
    small_font = ("Poiret One", 10)

    # Create a main frame with canvas for scrolling
    main_frame = tk.Frame(Main_Window, bg="#1e1e2e")
    main_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(main_frame, bg="#1e1e2e", highlightthickness=0)
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="#1e1e2e")

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Enable mousewheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    Main_Window.bind_all("<MouseWheel>", _on_mousewheel)

    # Header Section with improved welcome theme
    header_frame = tk.Frame(scrollable_frame, bg="#2c2c4c", padx=20, pady=15)
    header_frame.pack(fill="x", pady=(0, 20))
    
    # Welcome message with improved styling
    welcome_text = f"Welcome back, {username}!"
    tk.Label(header_frame, text=welcome_text, font=welcome_font, 
             fg="#EAB875", bg="#2c2c4c").pack(side="left")
    
    # Date display
    from datetime import datetime
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    tk.Label(header_frame, text=current_date, font=normal_font, 
             fg="#aaaaaa", bg="#2c2c4c").pack(side="right", padx=10)
    
    # Main content container with centered alignment
    content_container = tk.Frame(scrollable_frame, bg="#1e1e2e")
    content_container.pack(fill="both", expand=True, padx=80)  # Equal left and right padding

    # Sidebar for navigation (left side)
    sidebar = tk.Frame(content_container, bg="#2c2c4c", width=200)
    sidebar.pack(side="left", fill="y", padx=(0, 20))
    
    tk.Label(sidebar, text="Quick Actions", font=heading_font, 
             fg="#f5f5f5", bg="#2c2c4c").pack(pady=20)
    
    nav_buttons = [
        ("📊 Get Stock", lambda: feature_1_window(user_id)),
        ("📈 Market Dashboard", lambda: MarketDashboard(user_id)),
        ("📰 Stock News", open_news_window),
    ]
    
    for text, command in nav_buttons:
        btn = tk.Button(sidebar, text=text, font=normal_font, bg="#44446c", fg="#f5f5f5",
                 width=18, command=command, relief="flat", anchor="w")
        btn.pack(pady=8, padx=10)
        # Add hover effect
        btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#55558c"))
        btn.bind("<Leave>", lambda e, b=btn: b.configure(bg="#44446c"))

    # Content area (right side)
    content_frame = tk.Frame(content_container, bg="#1e1e2e")
    content_frame.pack(side="right", fill="both", expand=True)

    # Investor Education Section
    education_frame = tk.Frame(content_frame, bg="#2c2c4c", padx=20, pady=20)
    education_frame.pack(fill="x", pady=(0, 20))
    
    tk.Label(education_frame, text="💡 Essential Investor Education", font=heading_font, 
             fg="#EAB875", bg="#2c2c4c").pack(anchor="w", pady=(0, 15))
    
    # Investment tips and knowledge
    tips = [
        "📈 Diversification: Spread investments across different sectors and asset classes to reduce risk",
        "💡 Long-term Focus: Invest for the long term rather than trying to time the market",
        "📊 Portfolio Review: Regularly review and rebalance your portfolio to maintain target allocations",
        "🔍 Fundamental Analysis: Research companies thoroughly before investing - examine financials, management, and competitive position",
        "💰 Dollar-Cost Averaging: Invest consistent amounts regularly regardless of market conditions",
        "📉 Contrarian Opportunities: Market downturns can present opportunities to buy quality stocks at discounted prices",
        "📚 Continuous Learning: Stay informed about financial markets, economic trends, and new investment strategies",
        "🎯 Goal Setting: Establish clear investment goals and develop a strategy to achieve them",
        "⏰ Time Horizon: Match investments to your time horizon - longer horizons can tolerate more risk",
        "💸 Emergency Fund: Maintain 3-6 months of living expenses in liquid assets before investing"
    ]
    
    for tip in tips:
        tip_frame = tk.Frame(education_frame, bg="#2c2c4c")
        tip_frame.pack(fill="x", pady=5)
        tk.Label(tip_frame, text="•", font=normal_font, fg="#EAB875", bg="#2c2c4c", width=2, anchor="w").pack(side="left")
        tk.Label(tip_frame, text=tip, font=normal_font, 
                fg="#f5f5f5", bg="#2c2c4c", justify="left", wraplength=650).pack(side="left", fill="x")

    # Key Financial Ratios Explanation
    ratios_frame = tk.Frame(content_frame, bg="#2c2c4c", padx=20, pady=20)
    ratios_frame.pack(fill="x", pady=(0, 20))
    
    tk.Label(ratios_frame, text="📊 Understanding Key Financial Ratios", font=heading_font, 
             fg="#EAB875", bg="#2c2c4c").pack(anchor="w", pady=(0, 15))
    
    ratios_info = [
        ("P/E Ratio (Price-to-Earnings)", "Measures a company's current share price relative to its earnings per share. Lower P/E may indicate undervaluation, while higher P/E may suggest growth expectations. Compare with industry averages for context."),
        ("P/B Ratio (Price-to-Book)", "Compares a company's market value to its book value. Useful for valuing companies with tangible assets. Values below 1 may suggest undervaluation, but consider industry norms."),
        ("Debt-to-Equity", "Indicates the proportion of equity and debt used to finance a company's assets. Lower ratios generally indicate less financial risk. Compare with industry peers as acceptable levels vary by sector."),
        ("ROE (Return on Equity)", "Measures profitability by revealing how much profit a company generates with shareholders' money. Higher ROE generally indicates efficient use of equity. Consistently high ROE is a positive sign."),
        ("Current Ratio", "Measures a company's ability to pay short-term obligations. Ratios above 1.5 are generally considered healthy, but very high ratios may indicate inefficient use of assets."),
        ("Dividend Yield", "Shows how much a company pays out in dividends each year relative to its stock price. Important for income investors. Very high yields may be unsustainable."),
        ("EPS Growth", "Measures the growth rate of a company's earnings per share. Consistent EPS growth often correlates with stock price appreciation over time."),
        ("Free Cash Flow", "Represents the cash a company generates after accounting for cash outflows to support operations. Positive and growing free cash flow is a sign of financial health.")
    ]
    
    for ratio, explanation in ratios_info:
        ratio_frame = tk.Frame(ratios_frame, bg="#3c3c5c", padx=15, pady=12)
        ratio_frame.pack(fill="x", pady=8)
        
        tk.Label(ratio_frame, text=ratio, font=subheading_font, 
                fg="#EAB875", bg="#3c3c5c").pack(anchor="w")
        tk.Label(ratio_frame, text=explanation, font=small_font, 
                fg="#f5f5f5", bg="#3c3c5c", wraplength=650, justify="left").pack(anchor="w", pady=(5, 0))

    # Investment Strategies Section
    strategies_frame = tk.Frame(content_frame, bg="#2c2c4c", padx=20, pady=20)
    strategies_frame.pack(fill="x", pady=(0, 20))
    
    tk.Label(strategies_frame, text="🚀 Popular Investment Strategies", font=heading_font, 
             fg="#EAB875", bg="#2c2c4c").pack(anchor="w", pady=(0, 15))
    
    strategies = [
        ("Value Investing", "Focuses on finding undervalued stocks with strong fundamentals that trade for less than their intrinsic values. Pioneered by Benjamin Graham and Warren Buffett."),
        ("Growth Investing", "Seeks companies with strong potential for earnings growth, often in emerging industries. These stocks may have higher P/E ratios but offer potential for significant appreciation."),
        ("Dividend Investing", "Builds income through dividend-paying stocks. Focuses on companies with strong cash flows and history of consistent dividend payments and increases."),
        ("Index Investing", "Seeks to match market performance through index funds or ETFs. Offers diversification, low costs, and typically outperforms most active managers over time."),
        ("Momentum Investing", "Follows recent price trends and market momentum. Buys securities that have been performing well and sells those performing poorly."),
        ("Contrarian Investing", "Goes against prevailing market trends. Buys when others are selling and sells when others are buying, based on the belief that markets overreact."),
        ("Dollar-Cost Averaging", "Invests fixed amounts at regular intervals regardless of market conditions. Reduces the impact of volatility and eliminates timing risk."),
        ("Asset Allocation", "Diversifies across different asset classes (stocks, bonds, real estate, commodities) based on risk tolerance and investment horizon.")
    ]
    
    for strategy, description in strategies:
        strategy_frame = tk.Frame(strategies_frame, bg="#3c3c5c", padx=15, pady=12)
        strategy_frame.pack(fill="x", pady=8)
        
        tk.Label(strategy_frame, text=strategy, font=subheading_font, 
                fg="#EAB875", bg="#3c3c5c").pack(anchor="w")
        tk.Label(strategy_frame, text=description, font=small_font, 
                fg="#f5f5f5", bg="#3c3c5c", wraplength=650, justify="left").pack(anchor="w", pady=(5, 0))

    # Risk Management Section
    risk_frame = tk.Frame(content_frame, bg="#2c2c4c", padx=20, pady=20)
    risk_frame.pack(fill="x", pady=(0, 20))
    
    tk.Label(risk_frame, text="🛡 Comprehensive Risk Management", font=heading_font, 
             fg="#EAB875", bg="#2c2c4c").pack(anchor="w", pady=(0, 15))
    
    risk_points = [
        ("Capital Preservation", "Never invest more than you can afford to lose. Your first priority should be protecting your initial investment."),
        ("Stop-Loss Orders", "Use stop-loss orders to automatically sell positions if they decline by a predetermined percentage, limiting potential losses."),
        ("Diversification", "Spread investments across different asset classes, sectors, and geographic regions to reduce exposure to any single risk."),
        ("Risk Assessment", "Honestly evaluate your risk tolerance and investment time horizon. Younger investors can typically tolerate more risk."),
        ("Regular Monitoring", "Continuously review and adjust your portfolio as market conditions, and your personal circumstances, change."),
        ("Emotional Control", "Avoid making impulsive decisions based on fear or greed. Stick to your investment plan during market volatility."),
        ("Liquidity Management", "Maintain adequate cash reserves for emergencies and opportunities so you're not forced to sell investments at inopportune times."),
        ("Hedging Strategies", "Consider using options or inverse ETFs to hedge against market downturns, especially for larger portfolios.")
    ]
    
    for point, description in risk_points:
        point_frame = tk.Frame(risk_frame, bg="#3c3c5c", padx=15, pady=12)
        point_frame.pack(fill="x", pady=8)
        
        tk.Label(point_frame, text=point, font=subheading_font, 
                fg="#EAB875", bg="#3c3c5c").pack(anchor="w")
        tk.Label(point_frame, text=description, font=small_font, 
                fg="#f5f5f5", bg="#3c3c5c", wraplength=650, justify="left").pack(anchor="w", pady=(5, 0))

    # Market Psychology Section
    psychology_frame = tk.Frame(content_frame, bg="#2c2c4c", padx=20, pady=20)
    psychology_frame.pack(fill="x", pady=(0, 20))
    
    tk.Label(psychology_frame, text="🧠 Market Psychology & Behavioral Finance", font=heading_font, 
             fg="#EAB875", bg="#2c2c4c").pack(anchor="w", pady=(0, 15))
    
    psych_points = [
        ("Herd Mentality", "Investors often follow the crowd, buying when prices are high and selling when prices are low. Successful investors think independently."),
        ("Loss Aversion", "People feel the pain of losses more strongly than the pleasure of gains. This can lead to holding losing positions too long and selling winners too early."),
        ("Confirmation Bias", "Seeking information that confirms existing beliefs while ignoring contradictory evidence. Actively seek opposing viewpoints."),
        ("Overconfidence", "Believing you know more than you do or have special insight. The market humbles overconfident investors."),
        ("Anchoring", "Fixing on specific price points, such as what you paid for a stock. Make decisions based on current realities, not historical prices."),
        ("Recency Bias", "Giving more weight to recent events while ignoring long-term trends. Maintain perspective through market cycles.")
    ]
    
    for point, description in psych_points:
        point_frame = tk.Frame(psychology_frame, bg="#3c3c5c", padx=15, pady=12)
        point_frame.pack(fill="x", pady=8)
        
        tk.Label(point_frame, text=point, font=subheading_font, 
                fg="#EAB875", bg="#3c3c5c").pack(anchor="w")
        tk.Label(point_frame, text=description, font=small_font, 
                fg="#f5f5f5", bg="#3c3c5c", wraplength=650, justify="left").pack(anchor="w", pady=(5, 0))

    # Getting Started Guide
    getting_started_frame = tk.Frame(content_frame, bg="#2c2c4c", padx=20, pady=20)
    getting_started_frame.pack(fill="x", pady=(0, 20))
    
    tk.Label(getting_started_frame, text="📋 Getting Started with Investing", font=heading_font, 
             fg="#EAB875", bg="#2c2c4c").pack(anchor="w", pady=(0, 15))
    
    steps = [
        ("1. Set Clear Goals", "Define what you're investing for (retirement, home, education) and your time horizon."),
        ("2. Assess Risk Tolerance", "Be honest about how much risk you can comfortably handle emotionally and financially."),
        ("3. Build Emergency Fund", "Ensure you have 3-6 months of living expenses in liquid savings before investing."),
        ("4. Start with Index Funds", "For beginners, low-cost index funds or ETFs provide instant diversification."),
        ("5. Learn Continuously", "Read books, follow financial news, and consider courses to build your knowledge."),
        ("6. Start Small", "Begin with amounts you're comfortable with and gradually increase as you gain experience."),
        ("7. Automate Investments", "Set up automatic contributions to build discipline and benefit from dollar-cost averaging."),
        ("8. Review Regularly", "Schedule periodic portfolio reviews but avoid constantly checking prices.")
    ]
    
    for step, description in steps:
        step_frame = tk.Frame(getting_started_frame, bg="#3c3c5c", padx=15, pady=12)
        step_frame.pack(fill="x", pady=8)
        
        tk.Label(step_frame, text=step, font=subheading_font, 
                fg="#EAB875", bg="#3c3c5c").pack(anchor="w")
        tk.Label(step_frame, text=description, font=small_font, 
                fg="#f5f5f5", bg="#3c3c5c", wraplength=650, justify="left").pack(anchor="w", pady=(5, 0))

    # Common Mistakes to Avoid
    mistakes_frame = tk.Frame(content_frame, bg="#2c2c4c", padx=20, pady=20)
    mistakes_frame.pack(fill="x", pady=(0, 20))
    
    tk.Label(mistakes_frame, text="⚠ Common Investment Mistakes to Avoid", font=heading_font, 
             fg="#EAB875", bg="#2c2c4c").pack(anchor="w", pady=(0, 15))
    
    mistakes = [
        ("Market Timing", "Trying to predict market movements rarely works consistently. Time in the market beats timing the market."),
        ("Chasing Performance", "Buying investments solely because they've recently performed well often leads to buying at peaks."),
        ("Overtrading", "Excessive buying and selling generates commissions and taxes while often underperforming a buy-and-hold approach."),
        ("Ignoring Costs", "High fees and expenses significantly erode returns over time. Prioritize low-cost investment vehicles."),
        ("Lack of Diversification", "Concentrating too heavily in a single stock, sector, or asset class exposes you to unnecessary risk."),
        ("Letting Emotions Rule", "Making decisions based on fear or greed rather than rational analysis typically leads to poor outcomes."),
        ("Following Hot Tips", "Acting on stock tips without doing your own research is speculating, not investing."),
        ("Neglecting Taxes", "Failing to consider tax implications of investment decisions can significantly reduce net returns.")
    ]
    
    for mistake, description in mistakes:
        mistake_frame = tk.Frame(mistakes_frame, bg="#3c3c5c", padx=15, pady=12)
        mistake_frame.pack(fill="x", pady=8)
        
        tk.Label(mistake_frame, text=mistake, font=subheading_font, 
                fg="#EAB875", bg="#3c3c5c").pack(anchor="w")
        tk.Label(mistake_frame, text=description, font=small_font, 
                fg="#f5f5f5", bg="#3c3c5c", wraplength=650, justify="left").pack(anchor="w", pady=(5, 0))

    # Footer with disclaimer
    disclaimer_frame = tk.Frame(content_frame, bg="#1e1e2e", padx=20, pady=15)
    disclaimer_frame.pack(fill="x", pady=(0, 10))
    
    disclaimer_text = "Disclaimer: The information provided is for educational purposes only and should not be considered as financial advice. Always conduct your own research and consult with a qualified financial advisor before making investment decisions. Past performance is not indicative of future results. Investing involves risk, including possible loss of principal."
    
    tk.Label(disclaimer_frame, text=disclaimer_text, font=("Poiret One", 9), 
             fg="#aaaaaa", bg="#1e1e2e", wraplength=800, justify="center").pack()

    Main_Window.mainloop()
    
# ===================== LOGIN WINDOW =====================
def login_window():
    ensure_tables()
    window = tk.Tk()
    window.title("Login")
    window.geometry("1200x800")
    window.configure(bg="#333333")

    frame = tk.Frame(window, bg="#333333")
    frame.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(frame, text="Login", bg="#D4AF37", fg="#FFFFFF", font=("Cutive Mono", 24)).pack(pady=20)
    tk.Label(frame, text="Username", bg="#333333", fg="#FFFFFF", font=("Poiret One", 16)).pack(pady=5)
    username_entry = tk.Entry(frame, font=("Poiret One", 16))
    username_entry.pack(pady=5)
    tk.Label(frame, text="Password", bg="#333333", fg="#FFFFFF", font=("Poiret One", 16)).pack(pady=5)
    password_entry = tk.Entry(frame, show="*", font=("Poiret One", 16))
    password_entry.pack(pady=5)

    btn_width = 20
    tk.Button(frame, text="Login", bg="#333333", fg="#FFFFFF", font=("Poiret One", 15),
              width=btn_width,
              command=lambda: do_login(username_entry.get(), password_entry.get(), window)).pack(pady=10)
    tk.Button(frame, text="Register", bg="#333333", fg="#FFFFFF", font=("Poiret One", 15),
              width=btn_width,
              command=lambda: store(username_entry.get(), password_entry.get())).pack(pady=10)

    window.mainloop()
if __name__ == "__main__":
    login_window()
