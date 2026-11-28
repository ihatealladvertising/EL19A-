import tempfile, unittest
from pathlib import Path
import a2l_address_order_audit as audit

class AuditTests(unittest.TestCase):
    def test_parser_types_and_source_lines(self):
        src=("/begin CHARACTERISTIC A\n  \"d\"\n  VALUE 0x8000 REC_UBYTE_C 0 C 0 255\n/end CHARACTERISTIC\n"
             "/begin CHARACTERISTIC B\n  \"d\"\n  CURVE 0x8002 REC_UBYTE_C 0 C 0 255\n/end CHARACTERISTIC\n"
             "/begin CHARACTERISTIC C\n  \"d\"\n  VALUE 0x8001 REC_UWORD_C 0 C 0 65535\n/end CHARACTERISTIC\n")
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"x.a2l";p.write_bytes(src.encode("ascii"));rows,k=audit.parse_a2l(p)
        self.assertEqual(k,{"VALUE":2,"CURVE":1})
        self.assertEqual([(r["name"],r["line"]) for r in rows],[("A",1),("B",5),("C",9)])
    def test_unique_address_representative_and_alias_group(self):
        rows=[{"name":"z","addr":0x8000,"line":20},{"name":"a","addr":0x8000,"line":10},{"name":"b","addr":0x8001,"line":30}]
        primary,groups=audit.unique_address_rows(rows)
        self.assertEqual([r["name"] for r in primary],["a","b"]);self.assertEqual(len(groups[0x8000]),2)
    def test_adjacency_runs(self):
        z=audit.stats(["a","b","c","a","z"])
        self.assertEqual((z["ordered"],z["fraction"],z["runs"],z["max_run"]),(3,.75,2,3))
    def test_seeded_null_is_reproducible(self):
        rows=[{"name":n,"addr":0x8000+i} for i,n in enumerate("abcdefghijklmnop")]
        self.assertEqual(audit.nulls(rows,123,100),audit.nulls(rows,123,100))
    def test_expected_hash_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/"a";b=Path(td)/"b";a.write_text("");b.write_text("")
            with self.assertRaisesRegex(ValueError,"V6 source SHA-256 mismatch"):
                audit.write_outputs(a,b,Path(td)/"x.tsv",Path(td)/"x.json",expected_v6="0"*64,repetitions=1)

if __name__=="__main__": unittest.main()
