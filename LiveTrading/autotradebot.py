import time
from datetime import datetime
from Logger.logger import Logger
import binance
from binance import ThreadedWebsocketManager

"""

1.可以更改symbol中的标的，这代表交易的标的，
2.strategy是使用的交易策略
    函数会持续运行，可以为函数设置运行的时间
    只能模拟下市价单，忽略策略交易下单对交易的影响
    策略开始执行后，position,balance等属性将同步更新
    
"""


class BinanceTradingBotBase:

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = binance.Client(self.api_key, self.api_secret)
        self.symbol_info = dict()
        self.initialize_symbol_info()
        print('/*----- Initial Success -----*/')

    def initialize_symbol_info(self):
        """
        初始化交易信息
        """
        info = self.client.get_exchange_info()
        for s in info['symbols']:
            if s['status'] != 'TRADING':
                continue
            symbol = s['symbol']
            self.symbol_info[symbol] = dict()
            self.symbol_info[symbol]['baseAsset'] = s['baseAsset']
            self.symbol_info[symbol]['quoteAsset'] = s['quoteAsset']
            self.symbol_info[symbol]['orderTypes'] = s['orderTypes']
            self.symbol_info[symbol]['isSpotTradingAllowed'] = s['isSpotTradingAllowed']
            self.symbol_info[symbol]['isMarginTradingAllowed'] = s['isMarginTradingAllowed']
            self.symbol_info[symbol]['minPrice'] = s['filters'][0]['minPrice']
            self.symbol_info[symbol]['tickSize'] = s['filters'][0]['tickSize']
            self.symbol_info[symbol]['minQty'] = s['filters'][1]['minQty']
            self.symbol_info[symbol]['stepSize'] = s['filters'][1]['stepSize']
            try:
                self.symbol_info[symbol]['minNotional'] = s['filters'][2]['minNotional']
            except KeyError:
                self.symbol_info[symbol]['minNotional'] = 0.0001

    def get_trade_price(self, symbol):
        """
         获取最新的成交价
        """
        symbol = symbol.upper()
        trade_price = float(self.client.get_recent_trades(symbol=symbol)[-1]['price'])
        print(f'latest trade price is {trade_price}!')
        return trade_price

    def detect_order_errors(self, qty, symbol, prc):
        if symbol not in self.symbol_info:
            print('{symbol} is not in the trading list')
            return False
        if qty < 0:
            print("quantity cannot be negative.")
            return False
        if qty < float(self.symbol_info[symbol]['minQty']):
            print("Holding position is below the minimum selling unit.")
            return False
        if prc is None:
            print('trade price is not available')
            return False
        if qty * prc < float(self.symbol_info[symbol]['minNotional']):
            print('trade amount is below the minimum requirement')
            return False
        return True

    def get_request_diff(self):
        # 判断请求时间，后续在策略运行中，可执行
        start_time = int(time.time() * 1000)
        server_time = self.client.get_server_time()['serverTime']
        end_time = int(time.time() * 1000)

        request_time_cost = end_time - start_time
        arrival_time_cost = server_time - start_time

        print('request time cost is ', request_time_cost, 'ms')
        return arrival_time_cost


class MyTradingBot(BinanceTradingBotBase):
    def __init__(self, api_key: str, api_secret: str, symbol: str, ui_path):
        """
        Initializes the class with API key, API secret, symbol, and strategy function.

        api_key: API key for accessing the API.
        api_secret: API secret for accessing the API.
        symbol: The symbol to be used.
        balance:float
        """
        super().__init__(api_key, api_secret)
        self.symbol = symbol
        self.balance = 1000000  # default is usdt,初始10000 USDT
        self.history_klines = []  # List to store historical K line data
        self.position = 0.5  # Initial position
        self.net_value = self.balance  # Initial net value
        self.last_his = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Timestamp of the last historical data
        self.latest_kline = None  # Latest K line data
        self.ui_path = ui_path
        self.logger = Logger(self.ui_path)
        self.logger.UI_path = ui_path
        print(f'ui_path is {self.logger.UI_path}')
        self.bm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)

    def update_net_value(self):
        """
        Update the net value based on the latest K line data and the current position.
        """
        new_kline = self.history_klines[-1]
        price = new_kline['c']  # Extract the closing price from the K line data
        self.net_value = self.balance + float(price) * self.position
        self.net_value = self.net_value / 10000
        min_now = str(datetime.now())[:16]
        if min_now != self.last_his:
            self.logger.flush_net_value(self.net_value)
            self.last_his = min_now

    def update_klines(self, msg):
        """
        Callback function to update K line data and net value when new data is received.

        msg: The message received from the data stream.
        """
        print('Update kline data')
        self.latest_kline = msg['k']  # Extract the K line data from the message 
        print(f"latest close price: {self.latest_kline['c']}")
        self.history_klines.append(self.latest_kline)
        if len(self.history_klines) > 20:
            self.history_klines = self.history_klines[-20:]  # Keep only the last 20 K lines

    def strategy(self, long_term: int = 10, short_term: int = 5, quantity: int = 1):
        """
        Dual moving average crossover strategy.
        If the short-term moving average is greater than the long-term moving average, then go long.
        If the short-term moving average is less than the long-term moving average, then go short.
        If a signal occurs, then buy or sell the specified quantity of the symbol.

        long_term: The period for the long-term moving average.
        short_term: The period for the short-term moving average.
        quantity: The quantity to buy or sell when a signal occurs.
        """

        # Calculate the current short-term and long-term moving averages
        short_term_mean_now = sum([float(kline["c"]) for kline in self.history_klines[-short_term:]]) / short_term
        long_term_mean_now = sum([float(kline["c"]) for kline in self.history_klines[-long_term:]]) / long_term

        # Calculate the previous short-term and long-term moving averages
        short_term_mean_last_minute = sum(
            [float(kline["c"]) for kline in self.history_klines[-short_term - 1:-1]]) / short_term
        long_term_mean_last_minute = sum(
            [float(kline["c"]) for kline in self.history_klines[-long_term - 1:-1]]) / long_term

        # Get the latest close price and the trade price
        current_price = float(self.history_klines[-1]["c"])
        trade_price = self.get_trade_price(self.symbol)
        detect_qty = abs(self.position) + quantity
        # 判断是不是满足交易要求
        if not self.detect_order_errors(detect_qty, self.symbol, trade_price):
            time.sleep(0.1)
            # 不满足就不执行策略
            return

        if (short_term_mean_now > long_term_mean_now) and (long_term_mean_last_minute < short_term_mean_last_minute):
            print(f"No trading signals appeared!")
            self.logger.flush_trades(self.symbol, 0, 0, 0)

        if (short_term_mean_now < long_term_mean_now) and (long_term_mean_last_minute > short_term_mean_last_minute):
            print(f"No trading signals appeared!")
            self.logger.flush_trades(self.symbol, 0, 0, 0)

        # if the short-term MA is above the long-term MA and was below in the previous minute
        if (short_term_mean_now > long_term_mean_now) and (long_term_mean_last_minute > short_term_mean_last_minute):

            if self.position < 0:
                required_balance = (-self.position + quantity + 1) * current_price  # Needed balance to go long
                if self.balance > required_balance:
                    # Buy enough to go long
                    print('A golden cross signal appeared, '
                          'currently position is short,  turn to long position!')
                    self.balance -= trade_price * (-self.position + quantity)  # Update balance
                    self.position = quantity  # Update position
                    self.logger.flush_trades(self.symbol, 'Buy', (-self.position + quantity), trade_price)
                else:
                    print("A golden cross signal appeared, but the account balance is insufficient.")
            # If currently neutral, check if we have enough balance to go long
            elif self.position == 0:
                required_balance = (quantity + 1) * current_price  # Needed balance to go long
                if self.balance > required_balance:
                    # Buy to go long
                    print('A golden cross signal appeared, '
                          'currently position is empty,  turn to long position!')
                    self.balance -= trade_price * quantity  # Update balance
                    self.position = quantity  # Update position
                    self.logger.flush_trades(self.symbol, 'Buy', quantity, trade_price)
                else:
                    print("A golden cross signal appeared, but the account balance is insufficient.")

        # If the short-term MA is below the long-term MA and was above in the previous minute
        elif (short_term_mean_now < long_term_mean_now) and (long_term_mean_last_minute < short_term_mean_last_minute):

            # If currently long, sell to go short
            if self.position > 0:
                # Sell enough to go short
                print('A dead cross signal appeared, '
                      'currently position is long, turn to short position!')
                self.balance += trade_price * (self.position + quantity)  # Update balance
                self.position = -quantity  # Update position
                self.logger.flush_trades(self.symbol, 'Sell', (self.position + quantity), trade_price)

            # If currently neutral, sell to go short
            elif self.position == 0:
                # Sell to go short
                print('A dead cross signal appeared, '
                      'currently position is empty, turn to short position!')
                self.balance += trade_price * quantity  # Update balance
                self.position = -quantity  # Update position
                self.logger.flush_trades(self.symbol, 'Sell', quantity, trade_price)
        return

    def run_strategy(self):
        """
        Run the trading bot with the specified strategy.
        The strategy here is a dual moving average crossover strategy.
        The bot will keep running the strategy until it is stopped.
        """

        while True:
            print('Start running the strategy')
            self.strategy()
            self.update_net_value()
            # 每30s执行一次
            time.sleep(30)




