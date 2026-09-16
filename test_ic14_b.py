import unittest
from start import parse_stats

def tr(car,name,score='91.25',style='追',rates=('10.0','20.0','30.0')):
 return f'<tr><td>{car}</td><td title="{name}">{name}</td><td>{score}</td><td>{style}</td><td>{rates[0]}%</td><td>{rates[1]}%</td><td>{rates[2]}%</td></tr>'

class T(unittest.TestCase):
 def test_six_complete(self):
  entry=[{'car_no':i,'name':f'選手{i}','reading':'テスト'} for i in range(1,7)]
  raw='<table>'+''.join(tr(i,f'選手{i}') for i in range(1,7))+'</table>'
  rows,ok,m=parse_stats(raw,entry);self.assertTrue(ok);self.assertEqual(len(rows),6);self.assertEqual(m['missing_car_nos'],[])
 def test_missing_five_is_partial_not_not_published(self):
  entry=[{'car_no':i,'name':f'選手{i}','reading':'テスト'} for i in range(1,7)]
  raw='<table>'+''.join(tr(i,f'選手{i}') for i in [1,2,3,4,6])+'</table>'
  rows,ok,m=parse_stats(raw,entry);self.assertFalse(ok);self.assertEqual(m['state'],'PARTIAL');self.assertEqual(m['missing_car_nos'],[5])
 def test_seven_complete(self):
  entry=[{'car_no':i,'name':f'選手{i}','reading':'テスト'} for i in range(1,8)]
  raw='<table>'+''.join(tr(i,f'選手{i}') for i in range(1,8))+'</table>'
  rows,ok,m=parse_stats(raw,entry);self.assertTrue(ok);self.assertEqual(m['expected_car_nos'],list(range(1,8)))
if __name__=='__main__':unittest.main(verbosity=2)
