import tkinter as tk
from scrape import begin_scrape
from plot import DiagarmPlot
from PIL import Image, ImageTk
from functools import partial

STOCK_SYMBOLS = ["MSFT", "AAPL", "NVDA", "NFLX", "INTC", "AMD", "IBM", "QCOM", "TSM", "TSLA"]
STOCK_COMPANY = ["微软", "苹果", "英伟达", "Netflix", "英特尔", "超微半导体", "IBM", "高通", "台积电", "特斯拉"]

current_stocks = set()
win = tk.Tk()
win.title("Stock Daily Close Price")
win.geometry('400x625')
new = None

def draw(symbol):
    current_stocks.add(symbol)
    diagramPlot = DiagarmPlot()
    diagramPlot.plot_all(current_stocks)
    generate_window()
    

def undraw(symbol):
    try:
        current_stocks.remove(symbol)
        diagramPlot = DiagarmPlot()
        diagramPlot.plot_all(current_stocks)
        generate_window()
    except:
        pass

def generate_window():
    global new
    if new != None:
        new.destroy()

    new = tk.Toplevel()
    image = Image.open("./fig.png")
    image_tk = ImageTk.PhotoImage(image)
    image = tk.Label(new, image=image_tk)
    image.pack()
    win.mainloop()


tk.Button(win, text="Start To Collect Data", command=begin_scrape).pack()
for symbol in STOCK_SYMBOLS:
    tk.Button(win, text=f"add {symbol}", command=partial(draw, symbol)).pack()
    tk.Button(win, text=f"remove {symbol}", command=partial(undraw, symbol)).pack()

win.mainloop()