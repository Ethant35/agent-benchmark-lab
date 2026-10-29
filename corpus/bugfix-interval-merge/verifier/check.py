from support import *
import random
rng=random.Random(8123)
cases=[[],[[1,3],[3,5]],[[8,9],[1,2],[2,4]],[[-4,-1],[-2,0]],[[2,2],[2,2]],[[0,10],[2,3],[9,12]]]
for _ in range(20):
    cases.append([sorted([rng.randint(-30,30),rng.randint(-30,30)]) for _ in range(rng.randrange(1,14))])
for intervals in cases:
    # Independent connected-component oracle, rather than the candidate's sorted sweep.
    groups=[[x] for x in intervals]
    changed=True
    while changed:
        changed=False
        for i in range(len(groups)):
            for j in range(i+1,len(groups)):
                if any(a<=d and c<=b for a,b in groups[i] for c,d in groups[j]):
                    groups[i]+=groups.pop(j);changed=True;break
            if changed: break
    expected=sorted([[min(x[0] for x in g),max(x[1] for x in g)] for g in groups])
    equal(call('app.py','merge_intervals',[intervals]),expected)
    assert run(['python','app.py'],json.dumps(intervals)).stdout.strip()==json.dumps(expected,separators=(',',':'))

print('PASS: version 2.0 contract verified')
