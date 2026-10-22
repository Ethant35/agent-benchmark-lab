import json,sys
def main(t):
 w=[x.casefold() for x in t.split()]; print(json.dumps({"total":len(w),"counts":{x:w.count(x) for x in sorted(set(w))}},sort_keys=True))
if __name__=="__main__": main(open(sys.argv[1],encoding="utf-8").read())
