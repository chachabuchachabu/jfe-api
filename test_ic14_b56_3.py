import ast, pathlib
p=pathlib.Path(__file__).with_name('start.py')
s=p.read_text(encoding='utf-8')
ast.parse(s)
assert '1.0.0-ic1.4-dev-b56.3' in s
for x in ['/v1/target-resolver/venue/','/v1/target-resolver/race/','/v1/targeted-strict-contract/race/']:
    assert x in s
assert 'resolve_target_b56("VENUE"' in s
assert 'resolve_target_b56("RACE"' in s
print('B56.3 static route contract PASS')
