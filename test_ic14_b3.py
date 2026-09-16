import unittest
from unittest.mock import patch
import start

ENTRY_HTML = """
<table>
<tr><td>1</td><td>1</td><td title="山田太郎">山田太郎</td><td>ヤマダタロウ</td><td>100.00</td><td>逃</td><td>10.0%</td><td>20.0%</td><td>30.0%</td></tr>
<tr><td>2</td><td>2</td><td title="佐藤次郎">佐藤次郎</td><td>サトウジロウ</td><td>99.00</td><td>追</td><td>11.0%</td><td>21.0%</td><td>31.0%</td></tr>
<tr><td>3</td><td>3</td><td title="鈴木三郎">鈴木三郎</td><td>スズキサブロウ</td><td>98.00</td><td>両</td><td>12.0%</td><td>22.0%</td><td>32.0%</td></tr>
<tr><td>4</td><td>4</td><td title="高橋四郎">高橋四郎</td><td>タカハシシロウ</td><td>97.00</td><td>逃</td><td>13.0%</td><td>23.0%</td><td>33.0%</td></tr>
<tr><td>5</td><td>5</td><td title="吉川誠">吉川誠</td><td>ヨシカワマコト</td><td>96.00</td><td>追</td><td>14.0%</td><td>24.0%</td><td>34.0%</td></tr>
<tr><td>6</td><td>6</td><td title="中村六郎">中村六郎</td><td>ナカムラロクロウ</td><td>95.00</td><td>両</td><td>15.0%</td><td>25.0%</td><td>35.0%</td></tr>
</table>
"""
ODDS_HTML = """
2026年9月16日 岸和田 1R
山田太郎 佐藤次郎 鈴木三郎 高橋四郎 吉川誠 中村六郎
3連単 1-2-3 4.5 2-3-1 8.2
3連複 1-2-3 3.1
2026/9/16 10:00現在
"""

class B3Tests(unittest.TestCase):
    def test_reg_b001_yoshikawa_is_bound(self):
        entry=start.parse_entry(ENTRY_HTML)
        rows,ok,meta=start.parse_stats(ENTRY_HTML,entry)
        self.assertTrue(ok)
        self.assertEqual(meta["missing_car_nos"],[])
        self.assertIn(5,[x["car_no"] for x in rows])

    def test_odds_bet_types_are_separate(self):
        entry=start.parse_entry(ENTRY_HTML)
        x=start.kd_odds_probe(ODDS_HTML,"2026-09-16","岸和田",1,entry)
        self.assertTrue(x["identity_bound"])
        self.assertEqual(x["bet_types"]["trifecta"]["state"],"AVAILABLE")
        self.assertEqual(x["bet_types"]["trio"]["state"],"AVAILABLE")
        self.assertEqual(x["bet_types"]["wide"]["state"],"UNKNOWN")

    def test_no_data_is_not_not_published(self):
        x=start.parse_kd_odds_sections("3連単 オッズ情報なし",[1,2,3,4,5,6])
        self.assertEqual(x["trifecta"]["state"],"UNKNOWN")

    def test_explicit_unpublished_is_not_published(self):
        x=start.parse_kd_odds_sections("3連単 オッズ未発表",[1,2,3,4,5,6])
        self.assertEqual(x["trifecta"]["state"],"NOT_PUBLISHED")

if __name__=="__main__":
    unittest.main(verbosity=2)
