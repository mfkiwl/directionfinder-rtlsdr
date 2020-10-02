from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import tkinter as tk
from tkinter import ttk

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("C:/Users/MAGRANA/Desktop/Arnau/GPS/directionfinder/finder_v2/points.txt", delim_whitespace=True)

mymap = plt.imread("C:/Users/MAGRANA/Desktop/Arnau/GPS/directionfinder/finder_v2/map.png")


BBox = (df.longitude.min(),   df.longitude.max(),      
         df.latitude.min(), df.latitude.max())


class Page(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
    def show(self):
        self.lift()

class Page1(Page):
    def __init__(self, *args, **kwargs):
        Page.__init__(self, *args, **kwargs)
        label = tk.Label(self, text="This is page 1")
        label.pack(side="top", fill="both", expand=True)

       
        fig, ax = plt.subplots(figsize = (7,8))
        ax.scatter(df.longitude, df.latitude, zorder=1, alpha= 0.2, c='b', s=10)
        #ax.set_title('Plotting Spatial Data on Riyadh Map')
        ax.set_xlim(BBox[0],BBox[1])
        ax.set_ylim(BBox[2],BBox[3])

        ax.imshow(mymap, zorder=0, extent = BBox, aspect= 'auto')

        bar1 = FigureCanvasTkAgg(fig, root)
        bar1.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH)

class Page2(Page):
   def __init__(self, *args, **kwargs):
       Page.__init__(self, *args, **kwargs)
       label = tk.Label(self, text="This is page 2")
       label.pack(side="top", fill="both", expand=True)

class Page3(Page):
   def __init__(self, *args, **kwargs):
       Page.__init__(self, *args, **kwargs)
       label = tk.Label(self, text="This is page 3")
       label.pack(side="top", fill="both", expand=True)


class Page4(Page):
   def __init__(self, *args, **kwargs):
       Page.__init__(self, *args, **kwargs)
       label = tk.Label(self, text="This is page 4")
       label.pack(side="top", fill="both", expand=True)


class Page5(Page):
   def __init__(self, *args, **kwargs):
       Page.__init__(self, *args, **kwargs)
       label = tk.Label(self, text="This is page 5")
       label.pack(side="top", fill="both", expand=True)

class Page6(Page):
   def __init__(self, *args, **kwargs):
       Page.__init__(self, *args, **kwargs)
       label = tk.Label(self, text="This is page 6")
       label.pack(side="top", fill="both", expand=True)


class MainView(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        p1 = Page1(self)
        p2 = Page2(self)
        p3 = Page3(self)
        p4 = Page4(self)
        p5 = Page5(self)
        p6 = Page6(self)

        buttonframe = tk.Frame(self)
        container = tk.Frame(self)
        buttonframe.pack(side="top", fill="x", expand=False)
        container.pack(side="top", fill="both", expand=True)

        p1.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
        p2.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
        p3.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
        p4.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
        p5.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
        p6.place(in_=container, x=0, y=0, relwidth=1, relheight=1)

        b1 = tk.Button(buttonframe, text="Page 1", command=p1.lift)
        b2 = tk.Button(buttonframe, text="Page 2", command=p2.lift)
        b3 = tk.Button(buttonframe, text="Page 3", command=p3.lift)
        b4 = tk.Button(buttonframe, text="Page 4", command=p4.lift)
        b5 = tk.Button(buttonframe, text="Page 5", command=p5.lift)
        b6 = tk.Button(buttonframe, text="Page 6", command=p6.lift)

        b1.pack(side="left")
        b2.pack(side="left")
        b3.pack(side="left")
        b4.pack(side="left")
        b5.pack(side="left")
        b6.pack(side="left")

        p1.show()

if __name__ == "__main__":
    root = tk.Tk()
    main = MainView(root)
    main.pack(side="top", fill="both", expand=True)
    root.wm_geometry("400x400")
    root.mainloop()



