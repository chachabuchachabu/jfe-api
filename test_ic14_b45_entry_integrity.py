import unittest
import start

class B45IntegrityTests(unittest.TestCase):
    def good(self):
        return {"entries":[
          {"car_no":1,"rider_name":"甲","age":30,"term":100,"grade":"A1","race_score":88.1},
          {"car_no":5,"rider_name":"乙","age":31,"term":101,"grade":"A2","race_score":82.0}],
          "expected_car_numbers":[1,5],"retrieved_car_numbers":[1,5]}
    def test_good(self): self.assertEqual(start.validate_entry_integrity(self.good())["state"],"AVAILABLE")
    def test_no_contiguous_assumption(self): self.assertEqual(start.validate_entry_integrity(self.good())["active_car_numbers"],[1,5])
    def test_duplicate_car(self):
        x=self.good(); x["entries"][1]["car_no"]=1; x["retrieved_car_numbers"]=[1,1]
        self.assertIn("DUPLICATE_CAR_NUMBER",start.validate_entry_integrity(x)["errors"])
    def test_duplicate_name(self):
        x=self.good(); x["entries"][1]["rider_name"]="甲"
        self.assertIn("DUPLICATE_RIDER_NAME",start.validate_entry_integrity(x)["errors"])
    def test_bad_grade(self):
        x=self.good(); x["entries"][0]["grade"]="逃"
        self.assertEqual(start.validate_entry_integrity(x)["state"],"ERROR")
    def test_bad_score(self):
        x=self.good(); x["entries"][0]["race_score"]=None
        self.assertEqual(start.validate_entry_integrity(x)["state"],"ERROR")
    def test_set_mismatch(self):
        x=self.good(); x["expected_car_numbers"]=[1,2]
        self.assertIn("SOURCE_RETRIEVED_CAR_SET_MISMATCH",start.validate_entry_integrity(x)["errors"])
    def test_withdrawal_not_inferred(self):
        g=start.validate_entry_integrity(self.good()); self.assertEqual(g["withdrawal_state"],"UNKNOWN"); self.assertEqual(g["withdrawals"],[])
    def test_empty(self): self.assertEqual(start.validate_entry_integrity({"entries":[]})["state"],"ERROR")

if __name__=='__main__': unittest.main()
