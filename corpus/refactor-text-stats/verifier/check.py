from support import *
cases=['Red red blue!\n BLUE\tred','','Hello, hello! ΣIGMA sigma\n','  One\tTWO\n','ß SS ﬁ FI','a a a a!']
for i,text in enumerate(cases):
    tokens=[word.casefold() for word in text.split()]
    expected={'total':len(tokens),'counts':{word:tokens.count(word) for word in sorted(set(tokens))}}
    equal(call('text_stats.py','tokenize',[text]),tokens)
    equal(call('text_stats.py','count_words',[tokens]),expected)
    filename=f'case-{i}.txt';(W/filename).write_text(text)
    equal(sorted_json(cli_using('text_stats.py',[filename],['tokenize','count_words'])),expected)

print('PASS: version 2.0 contract verified')
