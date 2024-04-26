import pandas as pd
import os,sys
from Order_Execution import OrderExecutionHandler
from Strategy_BackTest import *
from Logger.logger import *
from BackTest import BackTest

# test
UI_path = 'UI/'
logger = Logger(UI_path)
print(UI_path)

# could be changed
trading_symbols = ['sz.000001']

start_time = '2020-01-02 10:30:00'
end_time = '2020-04-02 10:30:00'

use_frequency = '5'
dh = DataAgent(symbols = trading_symbols)


dh.get_all_data(use_frequency, start_time, end_time)

start_time_backtest = datetime.datetime(2020, 1, 6, 10, 30)
end_time_backtest = datetime.datetime(2020, 4, 2, 15, 00)

account = Account(balance_init = 100000, start_time = start_time_backtest, logger = logger,
                  end_time = end_time_backtest, stop_loss_rate = -0.0001, stop_profit_rate = 0.2)

riskmanager = RiskManager(account = account)

strategy = strategy_DualMA('DualMA', dh, start_time = start_time,
                            end_time = end_time, trading_symbols = trading_symbols,
                            account = account, riskmanager = riskmanager, long_term = 10, short_term = 5, quantity = 10)

# strategy = strategy_DualThrust('DualThrust',dh, start_time = start_time_backtest,
#                                 end_time = end_time_backtest, trading_symbols = trading_symbols,
#                                 account = account, n1 = 20, n2 = 10, k1 = 0.2, k2 = 0.2, quantity = 10)

# strategy = strategy_R_Breaker('R_Breaker',dh, start_time = start_time_backtest,
#                               end_time = end_time_backtest, trading_symbols = trading_symbols,
#                               account = account, n1 = 20, n2 = 10, quantity = 10)

order_execution_handler = OrderExecutionHandler(dh, account,logger = logger, delay_min = 0)
BackTest(strategy, order_execution_handler, 20).run_strategy()
netvalue = strategy.account.get_netvalue_time_series()
trading_info = strategy.account.get_all_trading_info()
eval = account.get_evaluation(strategy.strategy_name, 252 * 4 * 12)
