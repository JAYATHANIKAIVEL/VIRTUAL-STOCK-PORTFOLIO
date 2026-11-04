# Virtual Stock Portfolio (StockInsight Pro)

A desktop app for practicing stock trading with virtual money, built with Python, Tkinter and MySQL. It uses live market data, so you can learn investing without risking real money.

## Features
- **Login and Register:** each user has their own account and portfolio, stored in MySQL
- **Get Stock:** search a company by name and see its live price, previous close, market cap, and 52-week high/low
- **Virtual Invest:** set your starting capital, then record buy and sell trades
  - Tracks buy value, sell value, realized profit/loss, tax estimate, net profit/loss and returns (%)
  - Shows your remaining balance after every trade
  - Profit rows show in green and loss rows in red
  - Delete one trade (right-click) or all trades
- **Market Dashboard:** live charts for Nifty 50, top Indian stocks, Gold and Silver, with simple trend-based suggestions. It refreshes every 60 seconds.
- **Stock News:** top market headlines from Moneycontrol, opened in your browser
- **Investor Education:** built-in guides on financial ratios, strategies, risk management, market psychology and common mistakes

## Tech Used
- Python 3
- Tkinter (GUI)
- MySQL (database)
- yfinance (live market data)
- Matplotlib and NumPy (charts)
- Requests and BeautifulSoup (news scraping)

## How to Run
1. Install Python 3 and MySQL Server.
2. Install the libraries:
   ```
   pip install mysql-connector-python yfinance matplotlib numpy requests beautifulsoup4
   ```
3. Create the database in MySQL:
   ```sql
   CREATE DATABASE STOCK_APP;
   ```
4. Open `VIRTUAL_STOCK_PORTFOLIO.py` and put your own MySQL username and password in the `Connect()` function.
5. Run the app once. It creates the tables automatically:
   ```
   python VIRTUAL_STOCK_PORTFOLIO.py
   ```
6. Add some stocks to search for (the Get Stock page only finds stocks in this table):
   ```sql
   USE STOCK_APP;
   INSERT INTO products (brand_name, ticker) VALUES
   ('TCS', 'TCS.NS'),
   ('Reliance', 'RELIANCE.NS'),
   ('HDFC Bank', 'HDFCBANK.NS'),
   ('Infosys', 'INFY.NS'),
   ('ICICI Bank', 'ICICIBANK.NS');
   ```
7. Run the app again, register an account, and log in.

## Notes
- Needs an internet connection for live prices and news.
- Built for learning only. It is not financial advice.
- This is a student project: passwords are stored as plain text, so don't reuse a real password.

## Author
Thanikai
