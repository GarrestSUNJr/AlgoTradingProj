import numpy as np

class TCA:
    def __init__(self, shares_to_trade, decision_price, arrival_price, trade_record):
        """
        初始化TCA类
        :param shares_to_trade: 需要交易的股份总数
        :param decision_price: 交易决策价格
        :param arrival_price: 订单进入市场时的价格
        :param trade_record: 交易记录列表，每个元素包含交易价格和交易股份数
        """
        self.shares_to_trade = shares_to_trade
        self.decision_price = decision_price
        self.arrival_price = arrival_price
        self.trade_record = trade_record
        self.execution_prices = [trade[0] for trade in trade_record]  # 所有交易的执行价格
        self.trade_volumes = [trade[1] for trade in trade_record]  # 每笔交易的交易量

    def calculate_average_execution_price(self):
        """
        计算平均执行价格
        """
        total_traded_volume = sum(self.trade_volumes)
        total_cost = sum(p * q for p, q in zip(self.execution_prices, self.trade_volumes))
        return total_cost / total_traded_volume

    def calculate_implementation_shortfall(self):
        """
        计算实施短缺
        """
        average_execution_price = self.calculate_average_execution_price()
        paper_return = (self.decision_price * self.shares_to_trade) - (self.arrival_price * self.shares_to_trade)
        actual_return = (self.shares_to_trade * self.calculate_average_execution_price()) - (self.shares_to_trade * self.arrival_price)
        is_cost = paper_return - actual_return
        return is_cost

    def calculate_relative_performance_measure(self):
        """
        计算相对性能度量（RPM）
        """
        execution_prices = np.array(self.execution_prices)
        arrival_price = self.arrival_price
        better_than_arrival = execution_prices <= arrival_price
        volume_better_than_arrival = np.sum(self.trade_volumes[better_than_arrival])
        total_volume = sum(self.trade_volumes)
        rpm = (volume_better_than_arrival / total_volume) * 100
        return rpm
