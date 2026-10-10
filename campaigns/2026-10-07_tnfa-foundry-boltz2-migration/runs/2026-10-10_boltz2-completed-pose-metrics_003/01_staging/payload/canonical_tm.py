from pathlib import Path
import hashlib,json,re,subprocess,tempfile
from Bio.PDB.MMCIF2Dict import MMCIF2Dict
from Bio.PDB import MMCIFIO

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def canonical_copy(source,destination,native_to_canonical):
    d=MMCIF2Dict(str(source));keys=[k for k in d if k.startswith('_atom_site.')]
    auth=d['_atom_site.auth_asym_id'];label=d['_atom_site.label_asym_id'];n=len(auth)
    assert set(auth)==set('ABCD') and auth==label and set(native_to_canonical)==set('ABCD')
    assert all(len(d[k])==n for k in keys)
    original={d['_atom_site.id'][i]:tuple(d[k][i] for k in keys if k not in ['_atom_site.auth_asym_id','_atom_site.label_asym_id']) for i in range(n)}
    order=sorted(range(n),key=lambda i:'ABCD'.index(native_to_canonical[auth[i]]))
    for k in keys:
        values=d[k]
        d[k]=[native_to_canonical[values[i]] if k in ['_atom_site.auth_asym_id','_atom_site.label_asym_id'] else values[i] for i in order]
    for k,v in list(d.items()):
        if k not in keys and isinstance(v,list) and ('asym_id' in k or k=='_struct_asym.id'):
            d[k]=[native_to_canonical.get(x,x) for x in v]
    assert {d['_atom_site.id'][i]:tuple(d[k][i] for k in keys if k not in ['_atom_site.auth_asym_id','_atom_site.label_asym_id']) for i in range(n)}==original
    writer=MMCIFIO();writer.set_dict(d);writer.save(str(destination))
    reread=MMCIF2Dict(str(destination))
    assert all(reread[k]==d[k] for k in keys)
    return {'source_sha256':sha(source),'adapter_sha256':sha(destination),'atom_count':n,'native_to_canonical':native_to_canonical,'all_atom_site_values_except_chain_names_preserved':True}

def calculate(row,human_path,mouse_path,executable):
    mapping=row['pose']['chosen_copy_mapping']['human_to_mouse_copy']
    inverse={m:h for h,m in mapping.items()};inverse['D']='D'
    with tempfile.TemporaryDirectory(prefix='tnfa_canonical_tm_') as tmp:
        h=Path(tmp)/'human.cif';m=Path(tmp)/'mouse.cif';cm=Path(tmp)/'chainmap.tsv'
        records={'human':canonical_copy(human_path,h,dict(zip('ABCD','ABCD'))),'mouse':canonical_copy(mouse_path,m,inverse)}
        cm.write_text(''.join(c+'\t'+c+'\n' for c in 'ABCD'))
        argv=[str(executable),str(m),str(h),'-mol','prot','-mm','1','-ter','1','-chainmap',str(cm)]
        p=subprocess.run(argv,capture_output=True,text=True,check=True,timeout=120)
        scores=[float(x) for x in re.findall(r'TM-score=\s*([0-9.]+)',p.stdout)]
        assert len(scores)>=2
        match=re.search(r'Aligned length=\s*(\d+), RMSD=\s*([0-9.]+)',p.stdout);assert match
        return {'candidate_id':row['candidate_id'],'whole_complex_tm_human_normalized':scores[1],'whole_complex_tm_mouse_normalized':scores[0],'whole_complex_usalign_rmsd_angstrom':float(match.group(2)),'whole_complex_usalign_aligned_length':int(match.group(1)),'canonical_adapter_records':records,'usalign_stdout':p.stdout,'method':'Canonical chain ordering and identity chain map under fixed target-copy assignment; no coordinate changes'}
