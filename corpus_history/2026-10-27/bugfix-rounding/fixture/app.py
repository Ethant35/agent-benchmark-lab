from decimal import Decimal
import sys
def format_price(x): return f"{float(x):.2f}"
if __name__=="__main__": print(format_price(sys.argv[1]))
