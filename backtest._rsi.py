import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 讀取加密貨幣數據
data = pd.read_csv('history\\crypto\\BTCUSDT-1d-data.csv', index_col='Timestamp', parse_dates=True)
try: 
    data = data.loc['2024-05-24':]
except:
    pass

# 計算 RSI 指標
def compute_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    data['RSI'] = rsi

compute_rsi(data)

# 定義買賣策略（例如：RSI < 30 買入，RSI > 70 賣出）
initial_balance = 1000  # 初始資金
balance = initial_balance
position = 0
buy_price = 0
entry_balance = 0
performance = []  # 用來儲存每筆交易績效
buy_signals = []  # 記錄入場時間
sell_signals = []  # 記錄出場時間
daily_balances = [initial_balance]  # 用來儲存每天的balance
trade_details = []  # 用來儲存每筆交易的詳細資料

for i in range(len(data) - 1):
    if data['RSI'].iloc[i] < 30 and position == 0:  # 買入條件
        entry_balance = balance
        position = balance / data['Close'].iloc[i]
        buy_price = data['Close'].iloc[i]
        balance = 0
        buy_signals.append(data.index[i])  # 記錄入場時間
        buy_time = data.index[i]
        
    elif data['RSI'].iloc[i] > 70 and position > 0:  # 賣出條件
        balance = position * data['Close'].iloc[i]
        sell_signals.append(data.index[i])  # 記錄出場時間
        sell_price = data['Close'].iloc[i]
        sell_time = data.index[i]
        
        # 記錄每筆交易的詳細資料
        holding_days = (sell_time - buy_time).days
        trade_return = (sell_price - buy_price) / buy_price
        trade_details.append({
            'Buy Time': buy_time,
            'Sell Time': sell_time,
            'Buy Price': buy_price,
            'Sell Price': sell_price,
            'Holding Days': holding_days,
            'Return (%)': trade_return * 100
        })
        
        performance.append(trade_return)  # 記錄每筆交易績效
        position = 0
    
    # 計算每日的balance（即未交易日也記錄）
    daily_balances.append(balance if position == 0 else position * data['Close'].iloc[i])

# 最終結算
if position > 0:  # 若尚未賣出，按最後一天價格賣出
    balance = position * data['Close'].iloc[-1]
final_return = (balance - initial_balance) / initial_balance

# 計算回測指標
daily_balance_returns = [0]  # 計算balance變動率，初始化為0
for i in range(1, len(daily_balances)):
    daily_balance_returns.append((daily_balances[i] - daily_balances[i-1]) / daily_balances[i-1])

daily_balance_returns = np.array(daily_balance_returns)  # 將list轉為array，便於後續計算

# 將daily_balance_returns轉為pandas Series來使用cummax()
cumulative_balance = pd.Series(daily_balances, index=data.index)

# 計算最大回撤（Max Drawdown）
drawdown = cumulative_balance.cummax() - cumulative_balance  # 當前回撤 = 峰值 - 當前值
max_drawdown = drawdown.max()  # 最大回撤 = 回撤的最大值

# 夏普比率
sharpe_ratio = daily_balance_returns.mean() / daily_balance_returns.std() * np.sqrt(365)

# 結果輸出
print("初始資金:", initial_balance)
print("最終資金:", balance)
print("總收益率:", final_return)
print("最大回撤:", max_drawdown)
print("夏普比率:", sharpe_ratio)
print("每筆交易的平均收益:", np.mean(performance) if performance else '無交易')

# 印出每筆交易的詳細資料
if trade_details:
    print("\n每筆交易的詳細資料:")
    for trade in trade_details:
        print(f"買入時間: {trade['Buy Time']}, 賣出時間: {trade['Sell Time']}, "
              f"買入價格: {trade['Buy Price']}, 賣出價格: {trade['Sell Price']}, "
              f"持有天數: {trade['Holding Days']}, 報酬率: {trade['Return (%)']:.2f}%")

# 繪製資金變化曲線和回撤曲線
plt.figure(figsize=(12, 6))

# 資金變化圖（縱軸為balance）
plt.subplot(2, 1, 1)
plt.plot(cumulative_balance, label='Balance (Cumulative)')

# 讓買賣信號的點的y值對應於cumulative_balance
plt.scatter(buy_signals, cumulative_balance.loc[buy_signals], marker='^', color='g', label='Buy Signal', zorder=5)  # 標註買入點
plt.scatter(sell_signals, cumulative_balance.loc[sell_signals], marker='v', color='r', label='Sell Signal', zorder=5)  # 標註賣出點

plt.legend()
plt.title('Cumulative Balance')

# 設定Cumulative Balance的縱軸範圍，避免過度拉伸
plt.ylim([min(cumulative_balance) - 0.05 * min(cumulative_balance), max(cumulative_balance) + 0.05 * max(cumulative_balance)])

plt.tight_layout()
plt.show()
