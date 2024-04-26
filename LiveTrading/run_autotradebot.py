import time
import autotradebot as auto
import sys
import os
import threading

if __name__ == "__main__":

    #  测试使用
    api_key = 'rF7wq1ri0kMJBxRhQZTiFUx5U8OO50oNi9iOZhzLD6kf9N7dIwG4mowiHz7psGX1'
    api_secret = 'cWtzGZsaoddLMYlw5MghAQDVqm12rkAYiJDxfQwa26WwQRaUnNeXw5dc06KLVzjw'
    symbol = 'BTCUSDT'
    ui_path = str(os.path.abspath(sys.argv[0]))[:-4] + 'Ui/'
    if not os.path.exists(ui_path):
        os.mkdir(ui_path)

    def stop_bot(robot, func_name):
        if robot is not None and robot.bm is not None and func_name is not None:
            robot.bm.stop_socket(func_name)
            robot.bm.close()


    bot = None
    socket_name = None
    try:
        bot = auto.MyTradingBot(api_key, api_secret, symbol, ui_path)
        bot.bm.start()
        socket_name = bot.bm.start_kline_socket(callback=bot.update_klines, symbol=bot.symbol)
        timer = threading.Timer(10 * 60, stop_bot, args=(bot, socket_name))
        timer.start()
        # 获取一些k线数值
        time.sleep(10)
        bot.run_strategy()

    except Exception as e:
        print(f"Error occurred: {e}")
        stop_bot(bot, socket_name)






