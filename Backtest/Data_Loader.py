import sqlite3
import pandas as pd
from chinese_calendar import is_workday
import baostock as bs
from datetime import time

def get_data_from_bs(stock_code, start_date, end_date, frequency, adjustflag):
    # 登陆系统
    lg = bs.login()
    # 显示登陆系统的返回信息
    print('login respond error_code:' + lg.error_code)
    print('login respond  error_msg:' + lg.error_msg)

    rs = bs.query_history_k_data_plus(stock_code,
                                      "date,time,code,open,high,low,close,volume,amount,adjustflag",
                                      start_date=start_date, end_date=end_date,
                                      frequency=frequency, adjustflag=adjustflag)
    print('query_history_k_data_plus respond error_code:' + rs.error_code)
    print('query_history_k_data_plus respond  error_msg:' + rs.error_msg)

    data_list = []
    while (rs.error_code == '0') & rs.next():
        # 获取一条记录,将记录合并在一起
        data_list.append(rs.get_row_data())
    result = pd.DataFrame(data_list, columns=rs.fields)
    result['time'] = result.time.apply(lambda x:x[:12])
    result.time = pd.to_datetime(result.time)
    result = result.astype({'open':"float32",'high':"float32",'low':"float32",'close':"float32",'volume':"float32"})
    result['time'] = pd.to_datetime(result['time'])

    if len(data_list) > 0:
        print('Get data successfully!')
    else:
        print('No data!')
    # 登出系统
    bs.logout()
    return result

def bs_to_sql(data,db_path,frequency):
    conn = sqlite3.connect(db_path)
    data.to_sql(frequency, conn, if_exists="append")
    print("Done")

def get_data_from_sql(stock_code, start_time, end_time,frequency):
    con = sqlite3.connect('data.db')
    cur = con.cursor()
    sql = f"SELECT * FROM '{frequency}' where code = '{stock_code}' and time >= '{start_time}' and time <= '{end_time}'"
    cur.execute(sql)
    dataset = cur.fetchall()
    if len(dataset) == 0:
        print("No data!")
        raise Exception
    df = pd.DataFrame(dataset,columns = ['index','date','time','code','open','high','low','close','volume','amount','adjustflag'])
    df.drop('index',inplace=True)
    df.time = pd.to_datetime(df.time)
    return df 

import datetime
import pandas as pd
import sqlite3
import datetime
from typing import List


class DataAgent:
    def __init__(self, symbols: List):
        # data dict
        self.kline_history_backtest = {}  # the keys is datetime and every datetime is a dict which keys are symbols and the value are also dicts containing data
        self.latest_data = {}
        self.symbols = symbols
        self.datetimelist = []
        self.datetimeiter = iter([])
        self.db = sqlite3.connect('data.db')

    def get_all_data(self, use_frequency: str, start_time: str, end_time: str):

        # get trading datetimelist:could be change according to other time interval data
        # if use_frequency == "1":
        #     self.datetimelist = [datetime.datetime.strptime(str(x), '%Y-%m-%d %H:%M:%S') for x in
        #                          pd.date_range(start = start_time, end = end_time, freq = 'T').tolist()]
        # elif use_frequency == "5":
        #     self.datetimelist = [datetime.datetime.strptime(str(x), '%Y-%m-%d %H:%M:%S') for x in
        #                          pd.date_range(start = start_time, end = end_time, freq = '5T').tolist()]
        # elif use_frequency == "60":
        #     self.datetimelist = [datetime.datetime.strptime(str(x), '%Y-%m-%d %H:%M:%S') for x in
        #                          pd.date_range(start = start_time, end = end_time, freq = '60T').tolist()]

        if use_frequency == "1":
            self.datetimelist = [x.strftime('%Y-%m-%d %H:%M:%S') for x in pd.bdate_range(start = start_time, end = pd.to_datetime(end_time) + datetime.timedelta(days=1), freq = 'T').tolist() if is_workday(x) and (time(11,30) >= time(x.hour,x.minute) >= time(9,31) or time(15,0) >= time(x.hour,x.minute) >= time(13,1))]
        elif use_frequency == "5":
            self.datetimelist = [x.strftime('%Y-%m-%d %H:%M:%S') for x in pd.bdate_range(start = start_time, end = pd.to_datetime(end_time) + datetime.timedelta(days=1), freq = '5T').tolist() if is_workday(x) and (time(11,30) >= time(x.hour,x.minute) >= time(9,35) or time(15,0) >= time(x.hour,x.minute) >= time(13,5))]
        elif use_frequency == "60":
            self.datetimelist = [x.strftime('%Y-%m-%d %H:%M:%S') for x in pd.bdate_range(start = start_time, end = pd.to_datetime(end_time) + datetime.timedelta(days=1), freq = '60T').tolist() if is_workday(x) and (time(11,30) >= time(x.hour,x.minute) >= time(10,30) or time(15,0) >= time(x.hour,x.minute) >= time(14,0))]
        '''
        get the history kline data of symbol from start_time to end_time with use_frequency :now only could choose from "1m" or "5m"

        :params symbol: code
        :params use_frequency: choose from '1m' or '5m'
        :params start_time : starting time to backtesting eg: '2018-01-14 08:00:00'
        :params end_time : ending time to backtesting eg: '2018-01-14 08:00:00'
        '''

        cursor = self.db.cursor()

        # fetch the data in symbols one by one
        for symbol in self.symbols:
            sql = f"SELECT * FROM '{use_frequency}' where code = '{symbol}' and time >= '{start_time}' and time <= '{end_time}'"
            cursor.execute(sql)
            data_set = cursor.fetchall()

            if len(data_set) == 0:
                print("No data!")
                raise Exception
            
            # ['index','date','time','code','open','high','low','close','volume','amount','adjustflag'])
          

            # similar to the live data but filter something not used every date, keys of self.kline_history_backtest is datetime
            for i in range(len(data_set)):
                if data_set[i][2] not in self.kline_history_backtest.keys():  # time
                    self.kline_history_backtest[data_set[i][2]] = {}

                self.kline_history_backtest[data_set[i][2]][symbol] = []
                self.kline_history_backtest[data_set[i][2]][symbol] = {"e": "kline", "E": data_set[i][2], "s": symbol,
                                                                       "k": {"o": data_set[i][4], "h": data_set[i][5],
                                                                             "l": data_set[i][6], "c": data_set[i][7],
                                                                             "v": data_set[i][8]}}
        cursor.close()
        self.db.close()

    def get_market_price_trade(self, time: datetime.date, symbol, delay_min: int = 1):
        '''

        if at time T generate the buy or sell signal, then buy or sell at T+n at its close price
        return the trading price and trading time

        :params delay_min: consider the delay, trading at T+n minute

        return the trade price and the trade time
        '''

        try:
            time_delay = (pd.to_datetime(time) + datetime.timedelta(minutes = delay_min)).strftime('%Y-%m-%d %H:%M:%S')
            price = self.kline_history_backtest[time_delay][symbol]["k"]["c"]
            return price, pd.to_datetime(time) + datetime.timedelta(minutes = delay_min)
        except:
            print("No price data.")
            raise ValueError

    def get_market_price_now(self, time: datetime.datetime, symbol):
        '''
        get the latest close price

        '''
        price = self.kline_history_backtest[time][symbol]["k"]["c"]
        return price

    def generate_backtest_datetime_iter(self, start_time: datetime.datetime, end_time: datetime.datetime):
        try:
            self.datetimeiter = iter(
                self.datetimelist[self.datetimelist.index(start_time):self.datetimelist.index(end_time) + 1])
        except ValueError:
            print("Historical data couldn't cover this time span!")

    def _get_new_datetime(self):
        return next(self.datetimeiter)

    def get_latest_use_data(self, use_symbol_list, n = 1):
        use_symbol_data = {}
        if use_symbol_list is not None:
            for symbol in use_symbol_list:
                try:  # in case for symbol is not valid
                    use_symbol_data[symbol] = []
                    try:  # in case couldn't get n historical data
                        use_symbol_data[symbol] = self.latest_data[symbol][-n:]
                    except:
                        continue
                except KeyError:
                    print("{symbol} is not a valid symbol.").format(symbol = symbol)

            return use_symbol_data

    def update_data(self):
        '''
        return the update symbol list and the time
        '''
        try:
            datatime = self._get_new_datetime()
            print(datatime)
            if datatime in self.kline_history_backtest.keys():
                update_symbol_list = list(self.kline_history_backtest[datatime].keys())
                for symbol in update_symbol_list:
                    if symbol not in self.latest_data.keys():
                        self.latest_data[symbol] = []
                        self.latest_data[symbol].append(self.kline_history_backtest[datatime][symbol])
                    else:
                        self.latest_data[symbol].append(self.kline_history_backtest[datatime][symbol])
                return update_symbol_list, datatime  # so the strategy will generate action of this symbols
            else:  # if at this time no  data to update due to some errors
                return None, datatime  # that means no update this time

        except StopIteration:  # no data
            print("Backtesting done!")
            return None, None  # so if date_time is None ,means backtest done


if __name__ == "__main__":
    stock_code = "sz.000001"
    start_date = "2020-01-01"
    end_date = "2020-12-31"
    freq = '5'
    adjustflag = '1'
    result = get_data_from_bs(stock_code, start_date = start_date, end_date = end_date, frequency = freq, adjustflag= adjustflag)
    db_path = 'DataAdapter/data.db'
    bs_to_sql(result,db_path,frequency=freq)

    
