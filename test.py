import sqlite3
import math


class StdevFunc:
    """
    For use as an aggregate function in SQLite
    """
    def __init__(self):
        self.M = 0.0    #Mean
        self.V = 0.0    #Used to Calculate Variance
        self.S = 0.0    #Standard Deviation
        self.k = 1      #Population or Small

    def step(self, value):
        try:
            value = float(value)

            tM = self.M
            self.M += (value - tM) / self.k
            self.V += (value - tM) * (value - self.M)
            self.k += 1
        except Exception as EXStep:
            pass
            return None

    def finalize(self):
        try:
            if ((self.k - 1) < 3):
                return None

            #Now with our range Calculated, and Multiplied finish the Variance Calculation
            self.V = (self.V / (self.k-2))

            #Standard Deviation is the Square Root of Variance
            self.S = math.sqrt(self.V)

            return self.S
        except Exception as EXFinal:
            pass
            return None


import math
with sqlite3.connect('recipe2-final.db') as con:
    con.create_aggregate("stdev", 1, StdevFunc)

    cur = con.cursor()

    for x in ["Carbohydratebydifference(g)", "Totallipid(fat)(g)", "Energy(kcal)", "Protein(g)"]:
        print(x)

        cur.execute("select avg({}) from recipes2".format("\"" + x + "\""))
        print("avg: %f" % cur.fetchone()[0])
        cur.execute("select stdev({}) from recipes2".format("\"" + x + "\""))
        print("stdev: %f" % math.sqrt(cur.fetchone()[0]))
        print("\n")
    pass
