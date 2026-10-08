"""Reconcile the 2023-24 odds table against independent training results.

Does not use odds as training inputs. Writes raw quarantine only to chosen local output.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from oddities.normalize import load_reference, reconcile, json_safe


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('database',type=Path)
    parser.add_argument('reference',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    if args.output.exists():
        parser.error('Use a new output directory')
    games,manifest,ignored=load_reference(args.reference,2024)
    with sqlite3.connect(args.database.resolve().as_uri()+'?mode=ro',uri=True) as con:
        con.row_factory=sqlite3.Row
        rows=[dict(r) for r in con.execute('SELECT * FROM "2023-24" ORDER BY rowid')]
    _,quarantine,report=reconcile(rows,games)
    report.update(source_table='2023-24', source_sha256=sha256(args.database.read_bytes()).hexdigest(),
                  reference_response_count=len(manifest), reference_ignored=ignored,
                  reference_manifest_sha256=sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest(),
                  training_note='Baseline uses all completed reference results, not the partial odds table.')
    args.output.mkdir(parents=True)
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    (args.output/'quarantine.jsonl').write_text(''.join(json.dumps(json_safe(r))+'\n' for r in quarantine))
    (args.output/'reference-manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='missing_reference_ids'},indent=2))


if __name__=='__main__':main()
