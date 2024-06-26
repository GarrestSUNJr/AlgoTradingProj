import datetime
from Data_Loader import DataAgent
from Account import Account
import pandas as pd

'''
OrderExecutionHandler would receive the order from Strategy_BackTest and would execute the orders through class Account to 
buy or sell, here we assume the order would all be executed using the T+delay_min close price when order being sent at T
and if there is a warning signal, it could close all the current positions.

'''


class OrderExecutionHandler:
    def __init__(self, dh: DataAgent, account: Account, logger,delay_min: int):
        self.delay_min = delay_min
        self.dh = dh
        self.account = account
        self.logger = logger
        self.orders_fill = {}  # keys are time and values are orders
        

    def execute(self, order, time: datetime.datetime, warning_signal = None):
        for symbol in order.keys():
            if order[symbol]['action'] == 'Long':
                buy_price, buy_time = self.dh.get_market_price_trade(time, symbol, self.delay_min)
                self.account.buy(buy_time, symbol, buy_price, order[symbol]['quantity'])
                self.logger.flush_trades(symbol,'Buy',order[symbol]['quantity'],buy_price,time)

            elif order[symbol]['action'] == 'Short':
                sell_price, sell_time = self.dh.get_market_price_trade(time, symbol, self.delay_min)
                self.account.sell(sell_time, symbol, sell_price, order[symbol]['quantity'])
                self.logger.flush_trades(symbol,'Sell',order[symbol]['quantity'],sell_price,time)

        execution_time = pd.to_datetime(time) + datetime.timedelta(
            minutes = self.delay_min)  # trade done at this time, not the signal generation time
        if warning_signal == 1:
            self.account.stop_profit_time.append(execution_time)
            return execution_time,
        elif warning_signal == -1:
            self.account.stop_loss_time.append(execution_time)
        self.orders_fill[execution_time] = order

        return execution_time
