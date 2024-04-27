# coded by Zhou
# python version:   3.8.10

import json
import os
import random
import queue
import threading
from datetime import datetime
import requests
import pandas as pd



"""
alphavantage 网站爬取
"""


class StockScraper:

    QUERY_API = "https://www.alphavantage.co/query"
    API_KEYS = ["HJ67SMCFG1U8OEBI", "04OZ4JV7DC6672M1", "G3YEHWV5WEIUVXM3"]
    STOCK_PRICE_DATILY_API = QUERY_API + "?function=TIME_SERIES_DAILY_ADJUSTED&outputsize=full"
    BOLLINGER_BANDS_API = QUERY_API + "?function=BBANDS&interval=daily&time_period=5&series_type=close&nbdevup=3&nbdevdn=3"
    MACD_API = QUERY_API + "?function=MACD&interval=daily&series_type=open"
    APIS = [STOCK_PRICE_DATILY_API, BOLLINGER_BANDS_API, MACD_API]
    STOCK_COMPANY = ["微软", "苹果", "英伟达", "Netflix", "英特尔", "超微半导体", "IBM", "高通", "台积电", "特斯拉"]
    STOCK_SYMBOLS = ["MSFT", "AAPL", "NVDA", "NFLX", "INTC", "AMD", "IBM", "QCOM", "TSM", "TSLA"]

    def __init__(self, timeout, retry_times, thread_number, is_test):
        self.output_dir = ""
        self.timeout = timeout
        self.retry_times = retry_times
        self.thread_number = thread_number
        self.threads = []
        self.thread_lock = None
        self.work_queue = queue.Queue()
        self.exit_flag = False
        self.company_dict = dict()
        for i in range(10):
            self.company_dict[StockScraper.STOCK_SYMBOLS[i]] = StockScraper.STOCK_COMPANY[i]
        self.result = dict()
        self.is_test = is_test
    
    def start(self):
        self.prepare()
        for thread in self.threads:
            thread.start()
        while not self.work_queue.empty():
            pass

        self.exit_flag = True
        for thread in self.threads:
            thread.join()

    def prepare(self):
        if self.is_test:
            total = 1
            self.thread_number = 1
        else:
            total = 10
        self.work_queue = queue.Queue(10)


        done = set()
        for root, files, dirs in os.walk("./"):
            done = set(files)

        for i in range(total):
            symbol = StockScraper.STOCK_SYMBOLS[i]
            if symbol in done:
                pass
            else:
                self.work_queue.put(symbol)
    
        self.threads = [threading.Thread(target=self.run, args=(thread_id,)) for thread_id in range(self.thread_number)]
        self.thread_lock = threading.Lock()

    # 线程任务
    def run(self, thread_id):
        print(f"begin thread:\t {thread_id}")
        while not self.exit_flag:
            self.thread_lock.acquire()
            if not self.work_queue.empty():
                symbol = self.work_queue.get()
                self.thread_lock.release()
                daily = self.scrape(StockScraper.STOCK_PRICE_DATILY_API + f"&symbol={symbol}&apikey={StockScraper.get_api_key()}", self.timeout, self.retry_times)
                boll = self.scrape(StockScraper.BOLLINGER_BANDS_API + f"&symbol={symbol}&apikey={StockScraper.get_api_key()}", self.timeout, self.retry_times)
                macd = self.scrape(StockScraper.MACD_API + f"&symbol={symbol}&apikey={StockScraper.get_api_key()}", self.timeout, self.retry_times)
                daily_df, boll_df, macd_df = self.parse(daily, boll, macd)
                self.store(self.company_dict[symbol], symbol, 'daily', daily_df)
                self.store(self.company_dict[symbol], symbol, 'boll', boll_df)
                self.store(self.company_dict[symbol], symbol, 'macd', macd_df)
                boll_cal = self.calculate_boll(daily_df)
                macd_cal = self.calculate_macd(daily_df)
                self.store(self.company_dict[symbol], symbol, 'boll-cal', boll_cal)
                self.store(self.company_dict[symbol], symbol, 'macd-cal', macd_cal)
                result = pd.concat([daily_df, boll_df, macd_df, boll_cal, macd_cal], axis=1)
                result.to_pickle(f"{symbol}")
            else:
                self.thread_lock.release()
        print(f"end thread:   \t {thread_id}")

    # 爬取
    def scrape(self, url, timeout, retry_times):
        while retry_times > 0:
            retry_times -= 1
            try:
                response = requests.get(url, timeout=timeout)
                if response.status_code == 200:
                    print(response.json()["Meta Data"])
                    return response.json()
            except TypeError as e:
                print("TypeError", e)
            except KeyError as e:
                print('queries too frequently!!!!')
            except Exception as e:
                print(e)

        return

    # 解析
    def parse(self, daily, boll, macd):
        daily_df = pd.DataFrame.from_dict(daily["Time Series (Daily)"], orient='index')
        boll_df = pd.DataFrame.from_dict(boll["Technical Analysis: BBANDS"], orient='index')
        macd_df = pd.DataFrame.from_dict(macd["Technical Analysis: MACD"], orient='index')
        daily_df.columns = ['Open', 'High', 'Low', 'Close', 'AdjClose', 'Volume', 'Dividend', 'SplitCoefficient']
        daily_df.index.name = 'Date'
        daily_df.sort_index(inplace=True)
        daily_df = daily_df.astype(float)
        boll_df.columns = ["Real Upper Band", "Real Middle Band", "Real Lower Band"]
        boll_df.index.name = 'Date'
        boll_df.sort_index(inplace=True)
        boll_df = boll_df.astype(float)
        macd_df.columns = ["MACD", "MACD_Signal", "MACD_Hist"]
        macd_df.index.name = 'Date'
        macd_df.sort_index(inplace=True)
        macd_df = macd_df.astype(float)
        return daily_df, boll_df, macd_df
    
    # 保存
    def store(self, company, symbol, indicator, df):
        if indicator == 'daily':
            df.to_excel(f"{company}-{symbol}.xlsx")
        else:
            df.to_excel(f"{company}-{symbol}-{indicator}.xlsx")


    @staticmethod
    def calculate_boll(daily_df):
        # 计算BOLL，UB和LB
        boll = daily_df['Close'].rolling(20).mean()
        std = daily_df['Close'].rolling(20).std()
        upper_band = boll + 2 * std
        low_band = boll - 2 * std
        return pd.DataFrame({'boll cal': boll, 'upper band cal': upper_band, 'low band cal': low_band}, index=daily_df.index)


    @staticmethod
    def calculate_macd(daily_df):
        ema12 = daily_df['Close'].ewm(span=12, adjust=False, min_periods=12).mean()
        ema26 = daily_df['Close'].ewm(span=26, adjust=False, min_periods=26).mean()
        macd = ema12 - ema26
        macd_signal = macd.ewm(span=9, adjust=False, min_periods=9).mean()
        macd_hist = macd - macd_signal
        return pd.DataFrame({'macd cal': macd, "macd signal cal": macd_signal, "macd hist cal": macd_hist}, index=daily_df.index)
    
    @staticmethod
    def get_api_key():
        return random.choice(StockScraper.API_KEYS)
    

def begin_scrape():
    stockScraper = StockScraper(20, 3, 3, False)
    stockScraper.start()

if __name__ =="__main__":
    stockScraper = StockScraper(20, 3, 3, False)
    stockScraper.start()