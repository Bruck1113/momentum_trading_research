import pandas as pd
import csv


class strategy:
    def __init__(self, data, equities) -> None:
        self.data = data
        self.equities = equities
        self.start_money = 100000

class pair_trading(strategy):
    #Assume data is a pd.DataFrame object
    def __init__(self, data, equities) -> None:
        super().__init__(data, equities)
        self.long_pos = 0
        self.short_pos = 0
        self.result = pd.DataFrame()

    def trading_logic(self, long_price, short_price):
        if(abs((long_price - short_price)< long_price * 0.5)):
            #Close the positions
            self.start_money = self.start_money + long_price * self.long_pos - short_price * self.short_pos
            self.short_pos = 0
            self.long_pos = 0

    def check(self):
        #Initial determination of long and short
        long_eq = ""
        short_eq = ""
        if(self.data[self.equities[0]][0] > self.data[self.equities[1]][0]):
            long_eq = self.equities[0]
            short_eq = self.equities[1]
        else:
            long_eq = self.equities[1]
            short_eq = self.equities[0]

        for index, row in df.iterrows():
            if(self.long_pos == 0 and self.short_pos == 0) and (row[long_eq] - row[short_eq] < row[long_eq] * 0.7):
                self.long_pos = 50000 / row[long_eq]
                self.short_pos = 50000 / row[short_eq]
                # print(self.long_pos)
                # print(self.short_pos)
                self.start_money = self.start_money + self.short_pos * row[short_eq] - self.long_pos * row[long_eq]

            self.trading_logic(row[long_eq], row[short_eq])


        print("The ending money will be: " + str(self.start_money))
        print("The value of the long position will be " + str(self.long_pos * self.data[long_eq].iloc[-1]))
        print("The value of the short position will be " + str(self.short_pos * self.data[short_eq].iloc[-1]))


if __name__ == "__main__":
    df = pd.read_csv("store.csv")
    strat = pair_trading(df, ["BG", "ADNT"])
    strat.check()