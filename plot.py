import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

plt.ioff()
matplotlib.use('agg')

class DiagarmPlot:
    STOCK_SYMBOLS = ["MSFT", "AAPL", "NVDA", "NFLX", "INTC", "AMD", "IBM", "QCOM", "TSM", "TSLA"]
    STOCK_COMPANY = ["微软", "苹果", "英伟达", "Netflix", "英特尔", "超微半导体", "IBM", "高通", "台积电", "特斯拉"]
    tail_cut = -2000

    def __init__(self) -> None:
        self.fig, self.ax = plt.subplots()
        self.ax.set_title('Daily Close Price')
        self.fig.set_size_inches(16, 8)
        self.tick_spacing = 200
        self.ax.xaxis.set_major_locator(ticker.MultipleLocator(self.tick_spacing))
        self.linewidth = 0.5
        
    def plot_one_stock_daily(self, symbol):
        df = pd.read_pickle(symbol)
        # 尾部截断，确保所有数据都是同样数量。
        df = df[DiagarmPlot.tail_cut:]
        yclose = df['Close'].values
        xdate = df.index.values
        self.ax.plot(xdate, yclose, linewidth=self.linewidth, label=f'{symbol}')
        self.ax.legend()

    def plot_all(self, current_stocks):
        for stock in current_stocks:
            self.plot_one_stock_daily(stock)

        self.fig.savefig("./fig.png")


if __name__ == "__main__":
    diagramPlot = DiagarmPlot()
    diagramPlot.plot_one_stock_daily('MSFT')
    diagramPlot.plot_one_stock_daily('AAPL')
