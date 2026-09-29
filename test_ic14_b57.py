import start

def test_b57_probe_fail_closed_on_unresolved_target(monkeypatch):
    monkeypatch.setattr(start,'resolve_target_b56',lambda *a,**k:{'state':'PARTIAL','selected_target':None})
    x=start._b57_line_dom_probe('2026-09-30','佐世保',5)
    assert x['state']=='PARTIAL'
    assert x['line_evidence_state']=='UNKNOWN'
    assert x['blockers']==['TARGET_NOT_RESOLVED']
    assert x['fabricated_data'] is False

def test_b57_probe_identity_and_evidence_only(monkeypatch):
    monkeypatch.setattr(start,'resolve_target_b56',lambda *a,**k:{'state':'AVAILABLE','selected_target':{'venue_name':'佐世保','source_racedetail_url':'https://example/r5'}})
    raw='''<html><head><title>佐世保競輪 レース詳細 | 5R Ａ級特予選 | 2026年09月30日</title></head><body><div class="racecard_header">5R</div><section class="sample-narabi"><h3>並び予想</h3><span>1 2 / 3 4</span></section></body></html>'''
    monkeypatch.setattr(start,'fetch',lambda url:(raw,12.3,'TEST'))
    x=start._b57_line_dom_probe('2026-09-30','佐世保',5)
    assert x['state']=='AVAILABLE'
    assert x['body_identity']['verified'] is True
    assert x['keyword_hit_count']>=1
    assert x['line_evidence_state']=='PROBE_ONLY_NOT_BOUND'
    assert x['fabricated_data'] is False
