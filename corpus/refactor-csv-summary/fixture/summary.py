import csv,json,sys
def main(path):
 rows=list(csv.DictReader(open(path,newline="",encoding="utf-8"))); out={}
 for r in rows: out[r["sku"]]=round(out.get(r["sku"],0)+int(r["quantity"])*float(r["unit_price"]),2)
 print(json.dumps(out,sort_keys=True))
if __name__=="__main__": main(sys.argv[1])
