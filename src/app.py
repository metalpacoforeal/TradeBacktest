import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import MonthLocator
import numpy as np
import yfinance as yf

def get_bars(ticker_symbol, periods='max', alias=''):
    ticker = yf.Ticker(ticker_symbol)
    data_bars = ticker.history(period=periods)
    data_bars['Month'] = data_bars.index.month
    data_bars['Day'] = data_bars.index.day
    data_bars['Returns'] = data_bars['Close'].pct_change()
    if alias:
        data_bars['Symbol'] = alias
    else:
        data_bars['Symbol'] = ticker_symbol
    return data_bars[['Symbol', 'Month', 'Day', 'Close', 'Returns']]

# Load transaction data
trades = pd.read_csv('../data/AMD_transactions.csv', parse_dates=['TransactionDate'])
trades = trades.sort_values('TransactionDate', ignore_index=True)
trades = trades.rename(columns={'TransactionDate': 'Date'})
price_bars = pd.read_csv('../data/AMD_JAN_17_20_C10.csv', parse_dates=['Period'], index_col=0)
price_bars.index.name = 'Date'

# Get price data for underlying stock and broad market benchmark
stock_list = ['AMD', 'SPY']
tickers = yf.Tickers(stock_list)
compare_bars = tickers.history(period='5y')
compare_bars.index = compare_bars.index.tz_localize(None)
price_bars = pd.merge(price_bars, compare_bars['Close'], how='left', left_index=True, right_index=True)



# Merge price data and transactions
data = pd.merge(price_bars, trades, how='left', left_index=True, right_on='Date').set_index('Date')

# Generate holdings
positions = pd.DataFrame(index=price_bars.index).fillna(0.0)
positions['Start'] = 0.0
positions['AMD'] = (positions['Start'] + data['Quantity']).cumsum().fillna(method='ffill')
del positions['Start']
pos_diff = positions.diff()

# Create portfolio
initial_capital = 0
portfolio = positions.multiply(data['Close'], axis=0).multiply(100)
portfolio['Holdings'] = (positions.multiply(data['Close'], axis=0) * 100).sum(axis=1)
portfolio['Cash'] = initial_capital - (pos_diff.multiply(data['Close'], axis=0) * 100).sum(axis=1).cumsum()
portfolio['Total'] = portfolio['Cash'] + portfolio['Holdings']
portfolio['Returns'] = portfolio['Total'].pct_change()
portfolio['Cum Returns'] = portfolio['Returns'].add(1).cumprod().subtract(1)

# Simulate buy and hold portfolio in underlying stock and benchmark
compare_portfolio = pd.DataFrame(index=price_bars.index).fillna(0.0)
for s in stock_list:
    quantity = portfolio['Holdings'][0] / price_bars[s][0]
    compare_portfolio[s] = quantity * price_bars[s]

# Plot Returns
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(portfolio.index, portfolio['Total'], label='Option ({0:.2%})'.format(portfolio['Cum Returns'][-1:].values[0]))
for s in stock_list:
    cum_rets = compare_portfolio[s].pct_change().add(1).cumprod().subtract(1)
    ax.plot(compare_portfolio.index, compare_portfolio[s], label='{0} ({1:.2%})'.format(s, cum_rets[-1:].values[0]))
ax.xaxis.set_major_locator(MonthLocator())
ax.yaxis.set_major_formatter('${x:1,.2f}')
ax.set_ylabel('Portfolio Value')
ax.legend()
plt.show()
