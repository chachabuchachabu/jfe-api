import importlib.util
sp=importlib.util.spec_from_file_location('jfe','start.py'); m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
active=list(range(1,8)); tables=[]
for axis in active:
    rows=[]
    for second in active:
        if second==axis: continue
        thirds=[x for x in active if x not in (axis,second)]
        vals=['9999.9' if (axis+second+x)%5==0 else f'{axis*100+second*10+x}.1' for x in thirds]
        rows.append('<tr><td>%d</td>%s<td>%d</td></tr>'%(second,''.join('<td>%s</td>'%v for v in vals),second))
    html='<table class="odds_table bt5"><tr><th>%d rider</th></tr>%s</table>'%(axis,''.join(rows))
    tables.append({'table_index':axis,'class':'odds_table bt5','html':html,'text':m.txt(html)})
q,d=m._b495_bind_trifecta_bt5(tables,active)
assert len(q)==210,(len(q),d)
assert d['axis_count']==7 and not d['conflicts'] and not d['rejected_rows'],d
assert any(x['odds']==9999.9 for x in q)
# Dynamic count, no fixed seven-rider assumption.
active9=list(range(1,10)); tabs=[]
for axis in active9:
    rows=[]
    for second in active9:
        if second==axis: continue
        thirds=[x for x in active9 if x not in (axis,second)]
        rows.append('<tr><td>%d</td>%s</tr>'%(second,''.join('<td>12.3</td>' for _ in thirds)))
    html='<table class="odds_table bt5"><tr><th>%d rider</th></tr>%s</table>'%(axis,''.join(rows))
    tabs.append({'table_index':axis,'class':'odds_table bt5','html':html,'text':m.txt(html)})
q9,d9=m._b495_bind_trifecta_bt5(tabs,active9)
assert len(q9)==504 and d9['axis_count']==9,(len(q9),d9)
print('B49.5 focused tests PASS: 7-car=210, 9-car=504, 9999.9 preserved')
