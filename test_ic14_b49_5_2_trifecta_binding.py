import start as m

def table(first, active, base=10):
    others=[x for x in active if x!=first]
    h='<tr><th class="n%d" colspan="8">%d Rider</th></tr>'%(first,first)
    h+='<tr><th rowspan="2"></th>'+''.join('<th class="n%d">%d</th>'%(x,x) for x in others)+'<th rowspan="2"></th></tr>'
    h+='<tr>'+''.join('<td class="rider n%d">R%d</td>'%(x,x) for x in others)+'</tr>'
    for second in others:
        cells=[]
        for third in others:
            if third==second: cells.append('<td class="empty"></td>')
            else: cells.append('<td>%.1f</td>'%(base+first+second/10+third/100))
        h+='<tr><th class="n%d">%d</th>'%(second,second)+''.join(cells)+'<th class="n%d">%d</th></tr>'%(second,second)
    return '<table class="odds_table bt5">'+h+'</table>'

active=[1,2,3,4]
raw=''.join(table(x,active) for x in active)
tables=m._b494_tables(raw)
q,meta=m._b495_bind_trifecta_bt5(tables,active)
assert len(q)==24,(len(q),meta)
assert meta['axis_count']==4
assert not meta['conflicts'] and not meta['rejected_rows'],meta
assert q[0]['selection']==[1,2,3]
assert all(len(x['selection'])==3 and len(set(x['selection']))==3 for x in q)
# preserve 9999.9 exactly
raw2=raw.replace('11.2','9999.9',1)
q2,meta2=m._b495_bind_trifecta_bt5(m._b494_tables(raw2),active)
assert any(x['odds']==9999.9 for x in q2)
# dynamic 5-car count = 60, no hardcoded 7
active5=[1,2,3,4,5]
q5,meta5=m._b495_bind_trifecta_bt5(m._b494_tables(''.join(table(x,active5) for x in active5)),active5)
assert len(q5)==60,(len(q5),meta5)
print('B49.5.2 trifecta binding tests PASS: 24/24, 9999.9 preserved, dynamic 60/60')
