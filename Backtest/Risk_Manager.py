class RiskManager:
    def __init__(self,account,order_max = 1,execute_max = 100, stop_loss_rate = -0.1,stop_profit_rate = 0.1):
        self.account = account
        self.order_max = order_max
        self.execute_max = execute_max
        self.stop_loss_rate = stop_loss_rate
        self.stop_profit_rate = stop_profit_rate
        self.execute_cnt = 0
        
    
    def check_order(self,quantity):
        if quantity > self.order_max:
            return -1
        elif quantity < -self.order_max:
            return 1
        else:
            return None

    def check_execute(self,date_time):
        if self.execute_cnt < self.execute_max:
            self.execute_cnt += 1
            return None
        else:
            self.execute_cnt = 0
            return 1
    def execute_add(self):
        pass

    def check_pnl(self,time,dh):
        self.account.update_net_value(time, dh)
        if self.account.netValue < self.account.balance_init * (1 + self.stop_loss_rate):
            print("Reach the stop loss line. Stop trading!")
            return -1

        elif self.account.netValue > self.account.balance_init * (1 + self.stop_profit_rate):
            print("Reach the stop profit line. Could consider closing out the positions and leave.")
            return 1

        else:
            return None



     
        
