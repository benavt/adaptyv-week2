from pathlib import Path
import csv,datetime,hashlib,json,sys

ROOT=Path.cwd();BASE=ROOT/'campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs'
PARENT=BASE/'2026-10-09_boltz2-pose-conservation_007'
REPAIR=BASE/'2026-10-09_whole-tm-adapter-repair_001'
RANK=PARENT/'04_analysis/2026-10-09_local-pose-ranking_001'
mode=sys.argv[1]
assert mode in ['pilot','all']
SOURCE=REPAIR/('04_analysis/2026-10-09_canonical-whole-tm-'+mode+'_001')
OUT=REPAIR/('04_analysis/2026-10-09_corrected-report-'+mode+'_001')
OUT.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
completion=json.loads((SOURCE/'completion.json').read_text())
assert completion['status']=='validated' and sha(SOURCE/'metrics.jsonl')==completion['metrics_sha256']
rows={}
for line,raw in enumerate((SOURCE/'metrics.jsonl').open(),1):
    r=json.loads(raw);cid=r['candidate_id'];assert cid not in rows
    r['source']={'path':str(SOURCE/'metrics.jsonl'),'sha256':completion['metrics_sha256'],'line':line}
    assert all(v['all_atom_site_values_except_chain_names_preserved'] for v in r['canonical_adapter_records'].values())
    rows[cid]=r
assert len(rows)==(20 if mode=='pilot' else 13937)
(OUT/'whole-complex-scores.json').write_text(json.dumps(rows,indent=2)+'\n')
selected=json.loads((RANK/'selected.json').read_text())
keys=['whole_complex_tm_human_normalized','whole_complex_tm_mouse_normalized','whole_complex_usalign_rmsd_angstrom','usalign_stdout']
for r in selected:
    correction=rows[r['candidate_id']];assert r['sequence_sha256']==correction['sequence_sha256']
    for sp in ['human','mouse']:assert r[sp]['native_structure']['sha256']==correction['canonical_adapter_records'][sp]['source_sha256']
    r['legacy_whole_complex_diagnostic']={k:r['pose'][k] for k in keys}
    r['legacy_whole_complex_diagnostic']['status']='superseded_due_to_chainmap_single_protomer_alignment'
    for k in keys+['whole_complex_usalign_aligned_length','canonical_adapter_records']:r['pose'][k]=correction[k]
    r['pose']['whole_complex_source']=correction['source']
    r['pose']['whole_complex_method']=correction['method']
    r['ipsae_times_whole_complex_tm']=r['mean_ipsae']*correction['whole_complex_tm_human_normalized']
(OUT/'selected-report.json').write_text(json.dumps(selected,indent=2)+'\n')
if mode=='all':
    seen=set();changes=0
    with (RANK/'ranked.csv').open() as inp,(OUT/'ranked.csv').open('x',newline='') as out:
        reader=csv.DictReader(inp);writer=csv.DictWriter(out,fieldnames=reader.fieldnames);writer.writeheader()
        for r in reader:
            cid=r['candidate_id'];assert cid not in seen;seen.add(cid)
            c=rows[cid];assert c['sequence_sha256']==r['sequence_sha256']
            changes+=abs(float(r['whole_complex_tm_human_normalized'])-c['whole_complex_tm_human_normalized'])>1e-5
            r['whole_complex_tm_human_normalized']=c['whole_complex_tm_human_normalized'];writer.writerow(r)
    assert seen==set(rows)
    (OUT/'coverage-validation.json').write_text(json.dumps({'status':'passed','pairs':len(seen),'changed_whole_complex_diagnostic_count':changes,'primary_ranking_and_metrics_unchanged':True},indent=2)+'\n')
evidence={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':mode,'source_completion':completion,'primary_selection':str(RANK/'frozen-selection-evidence.json'),'corrected_whole_scores_sha256':sha(OUT/'whole-complex-scores.json'),'selected_report_sha256':sha(OUT/'selected-report.json'),'primary_ranking_unchanged':True}
(OUT/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n');print(OUT)
