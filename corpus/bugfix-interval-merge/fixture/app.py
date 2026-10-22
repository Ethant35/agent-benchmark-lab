import json,sys
def merge_intervals(items):
 out=[]
 for a,b in items:
  if out and a<out[-1][1]: out[-1][1]=max(out[-1][1],b)
  else: out.append([a,b])
 return out
if __name__=="__main__": print(json.dumps(merge_intervals(json.load(sys.stdin)),separators=(",",":")))
