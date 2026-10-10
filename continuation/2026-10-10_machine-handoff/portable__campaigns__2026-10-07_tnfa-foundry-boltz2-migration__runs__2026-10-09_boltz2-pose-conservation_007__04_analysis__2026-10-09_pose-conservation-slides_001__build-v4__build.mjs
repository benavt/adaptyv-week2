import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { Presentation, PresentationFile, FileBlob } from 'CONFIGURED_ROOT/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
import { resolvePresentationFont, applyPresentationChartFont, finalizePresentation } from 'CONFIGURED_ROOT/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations/container_tools/artifact_tool_utils.mjs';

const ROOT='CONFIGURED_ROOT/Code/projects/adaptyv-week2';
const run=path.join(ROOT,'campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs/2026-10-09_boltz2-pose-conservation_007');
const workspaceDir=path.join(run,'04_analysis/2026-10-09_pose-conservation-slides_001');
const build=path.join(workspaceDir,'build-v4');
const SKILL_DIR='CONFIGURED_ROOT/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations';
const rankDir=path.join(run,'04_analysis/2026-10-09_local-pose-ranking_001');
const selectedPath=path.join(ROOT,'campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs/2026-10-09_whole-tm-adapter-repair_001/04_analysis/2026-10-09_corrected-report-pilot_001/selected-report.json');
const selected=JSON.parse(await fs.readFile(selectedPath,'utf8'));
const scores=Object.values(JSON.parse(await fs.readFile(path.join(rankDir,'scores.json'),'utf8')));
const method=JSON.parse(await fs.readFile(path.join(rankDir,'selection-method.json'),'utf8'));
if(selected.length!==20)throw new Error('Exactly twenty selected designs required');
const renderer=path.join(workspaceDir,'renders_002');
const font=resolvePresentationFont({fontFamily:'Helvetica Neue'});
const p=Presentation.create({slideSize:{width:1600,height:900}});
const cohorts=['original-human','original-mouse','revised-human','revised-mouse'];
const labels={'original-human':'Original hotspots, human-origin binders','original-mouse':'Original hotspots, mouse-origin binders','revised-human':'Revised hotspots, human-origin binders','revised-mouse':'Revised hotspots, mouse-origin binders'};
const fmt=(v,n=3)=>v===null||v===undefined?'N/A':Number(v).toFixed(n);
const sha=b=>createHash('sha256').update(b).digest('hex');
function text(slide,value,x,y,w,h,size=24,bold=false,color='#263540',align='left'){
 const s=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 s.text=value;s.text.style={typeface:font,fontSize:size,bold,color,alignment:align,verticalAlignment:'top',autoFit:'none',wrap:'none',insets:{left:0,right:0,top:0,bottom:0}};return s;
}
function scatter(slide,rows,winners,key,title,x){
 const valid=rows.filter(r=>Number.isFinite(r.pose[key]));
 const color='#6D8FA5';
 const chart=slide.charts.add('scatter',{
  position:{left:x,top:170,width:710,height:470},title,titlePlacement:'aboveChart',
  titleTextStyle:{typeface:font,fontSize:25,bold:true,fill:'#263540'},
  series:[{name:'All complete pairs',xValues:valid.map(r=>r.mean_ipsae),values:valid.map(r=>r.pose[key]),fill:color,line:{fill:'none',width:0},marker:{symbol:'circle',size:3}},
          {name:'Selected top five',xValues:winners.filter(r=>Number.isFinite(r.pose[key])).map(r=>r.mean_ipsae),values:winners.filter(r=>Number.isFinite(r.pose[key])).map(r=>r.pose[key]),fill:'#B16A24',line:{fill:'none',width:0},marker:{symbol:'diamond',size:10}}],
  scatterOptions:{style:'marker'},hasLegend:true,legend:{position:'bottom',textStyle:{typeface:font,fontSize:23,fill:'#4C5961'}},
  xAxis:{title:{text:'Mean human/mouse IPSAE',textStyle:{typeface:font,fontSize:24,fill:'#263540'}},min:0,max:1,majorUnit:.2,numberFormatCode:'0.0',textStyle:{typeface:font,fontSize:23},majorGridlines:{fill:'#E5E9EC',width:1}},
  yAxis:{title:{text:key==='dockq_symmetric'?'Symmetric DockQ':'Binder pose TM',textStyle:{typeface:font,fontSize:24,fill:'#263540'}},min:0,max:1,majorUnit:.2,numberFormatCode:'0.0',textStyle:{typeface:font,fontSize:23},majorGridlines:{fill:'#E5E9EC',width:1}},
  chartFill:'#FFFFFF',plotAreaFill:'#FFFFFF',chartLine:{fill:'none',width:0},plotAreaLine:{fill:'#CDD5DA',width:1}
 });
 applyPresentationChartFont(chart,{fontFamily:font});
 return {count:valid.length,missing:rows.length-valid.length};
}
for(const cohort of cohorts){
 const rows=scores.filter(r=>r.cohort===cohort);const winners=selected.filter(r=>r.cohort===cohort).sort((a,b)=>a.rank-b.rank);
 if(winners.length!==5||rows.length!==method.available_pairs[cohort])throw new Error('Cohort coverage differs');
 const slide=p.slides.add();slide.background.fill='#FFFFFF';
 text(slide,labels[cohort],60,28,1480,54,42,true,'#1B2C37');
 text(slide,`${rows.length.toLocaleString()} complete pairs from ${method.full_cohort_sizes[cohort].toLocaleString()} designs. ${rows.length<method.full_cohort_sizes[cohort]?'Provisional. ':''}Snapshot, 2026-10-09.`,60,89,1480,32,24,false,'#6D5737');
 text(slide,'Selection score = mean IPSAE × binder pose TM after target-only alignment',60,130,1480,30,24,true,'#263540');
 const counts=[scatter(slide,rows,winners,'binder_pose_tm_target_aligned','IPSAE and binding-pose similarity',60),scatter(slide,rows,winners,'dockq_symmetric','IPSAE and interface agreement',830)];
 const values=[['Rank','Design sequence ID','Mean IPSAE','Pose TM','Product','DockQ'],...winners.map(r=>[String(r.rank),r.candidate_id,fmt(r.mean_ipsae),fmt(r.pose.binder_pose_tm_target_aligned),fmt(r.ipsae_times_binder_pose_tm,4),fmt(r.pose.dockq_symmetric)])];
 const table=slide.tables.add({rows:6,columns:6,left:60,top:660,width:1480,height:174,columnWidths:[65,715,175,175,175,175],values});
 table.borders.assign({fill:'none',width:0});
 table.cells.block({row:0,column:0,rowCount:6,columnCount:6}).assign({fill:'#FFFFFF',textStyle:{typeface:font,fontSize:19,color:'#263540'},margins:{left:6,right:6,top:4,bottom:3}});
 table.cells.block({row:0,column:0,rowCount:1,columnCount:6}).assign({fill:'#F0F3F5',textStyle:{typeface:font,fontSize:19,bold:true,color:'#263540'}});
 text(slide,`TM plot includes every complete pair. DockQ N/A: ${counts[1].missing}. Full-precision ranking. Predictions serve as mutual references.`,60,855,1480,26,19,false,'#59666F');
 slide.speakerNotes.textFrame.setText(JSON.stringify({cohort,scope:method.scope,available_pairs:rows.length,full_cohort_size:method.full_cohort_sizes[cohort],selection_method:method,source_scores:path.join(rankDir,'scores.json'),source_scores_sha256:sha(await fs.readFile(path.join(rankDir,'scores.json'))),plot_keys:['mean_ipsae','pose.binder_pose_tm_target_aligned','pose.dockq_symmetric'],chart_sample_counts:counts,selected_candidate_ids:winners.map(r=>r.candidate_id),historical_sources:method.historical_sources,method_sources:['https://github.com/wallnerlab/DockQ','https://github.com/pylelab/USalign'],reference_scope:'Computational human and mouse Boltz2 predictions compared with one another. No experimental binder complex reference.'},null,2));
 for(const row of winners){
  const s=p.slides.add();s.background.fill='#FFFFFF';
  text(s,labels[cohort],60,24,1170,50,40,true,'#1B2C37');
  text(s,row.candidate_id,60,80,1190,32,23,false,'#4C5961');
  text(s,`Product rank ${row.rank} of ${row.available_pair_count.toLocaleString()} complete pairs from ${row.full_cohort_size.toLocaleString()} designs.${row.available_pair_count<row.full_cohort_size?' Provisional.':''}`,60,117,1190,30,23,false,'#6D5737');
  text(s,'Mean IPSAE × pose TM',1230,28,310,28,21,false,'#4C5961','right');
  text(s,fmt(row.ipsae_times_binder_pose_tm,4),1250,62,290,48,40,true,'#1B2C37','right');
  const assets=[];
  for(const [sp,x,color] of [['human',60,'#174A78'],['mouse',840,'#85451F']]){
   const o=row[sp];text(s,sp==='human'?'Human TNF-alpha trimer':'Mouse TNF-alpha trimer',x,158,700,38,29,true,color);
   const imagePath=path.join(renderer,row.candidate_id+'__'+sp+'.png');
   s.images.add({blob:new Uint8Array(await fs.readFile(imagePath)),contentType:'image/png',alt:`${sp} TNF-alpha with binder ${row.candidate_id}`,fit:'contain',position:{left:x,top:196,width:700,height:398}});
   text(s,`IPSAE ${fmt(o.ipsae)} (native D–${o.best_protomer})   Complex ipTM ${fmt(o.complex_iptm)}   pTM ${fmt(o.ptm)}`,x,640,710,26,22);
   text(s,`Binder ipTM ${fmt(o.best_binder_pair_iptm)}   Confidence ${fmt(o.confidence_score)}   Binder pLDDT ${fmt(o.binder_plddt_0_to_100,1)}`,x,672,710,26,21);
   const rr=JSON.parse(await fs.readFile(path.join(renderer,row.candidate_id+'__'+sp+'.json'),'utf8'));
   assets.push({species:sp,native_structure:o.native_structure,score_sources:o.artifact_sources,ipsae_by_protomer:o.ipsae_by_protomer,display_transform:rr.chosen,render_png_sha256:rr.png_sha256,render_record:row.candidate_id+'__'+sp+'.json'});
  }
  text(s,`Mean IPSAE ${fmt(row.mean_ipsae)}    Binder pose TM ${fmt(row.pose.binder_pose_tm_target_aligned)}    Complex TM ${fmt(row.pose.whole_complex_tm_human_normalized)}    DockQ ${fmt(row.pose.dockq_symmetric)}`,60,602,1480,30,24,true,'#263540');
  text(s,`Binder sequence, ${row.sequence.length} aa`,60,711,1480,27,22,true);
  const chunks=row.sequence.match(/.{1,95}/g)||[];chunks.forEach((chunk,i)=>text(s,chunk,60,744+i*26,1480,27,22));
  text(s,'Pose TM uses the identical binder under a target-only fit. Complex TM is Human-normalized USalign. DockQ averages both reference directions.',60,814,1480,26,18,false,'#59666F');
  text(s,'Blue target: human. Copper target: mouse. Gray: binder. Green: hotspots. Red: ARG/LYS. Blue sticks: ASP/GLU. Magenta: HIS.',60,849,1480,26,19,false,'#59666F');
  s.speakerNotes.textFrame.setText(JSON.stringify({candidate_id:row.candidate_id,sequence:row.sequence,sequence_sha256:row.sequence_sha256,scope:method.scope,cohort,rank:row.rank,available_pair_count:row.available_pair_count,full_cohort_size:row.full_cohort_size,mean_ipsae:row.mean_ipsae,product:row.ipsae_times_binder_pose_tm,pose_metrics:row.pose,source_score:row.score_source,candidate_trace:row.candidate_trace,selection_method:method,models:assets,camera:path.join(workspaceDir,'2026-10-09_shared-camera_002.json'),colors:path.join(ROOT,'docs/2026-10-06_TNFA_COLORS.md'),binder_plddt_units:'0 to 100',score_units:'TM, DockQ and IPSAE are dimensionless 0 to 1',hotspot_scope:'Species/revision reference-pocket display annotation, not Boltz restraints.',reference_scope:'Computational prediction agreement.'},null,2));
 }
}
await fs.mkdir(path.join(workspaceDir,'outputs'),{recursive:true});
const candidatePath=path.join(build,'candidate-v5.pptx');
await (await PresentationFile.exportPptx(p)).save(candidatePath);
const finalPath=path.join(workspaceDir,'outputs/2026-10-09_TNFA_Boltz2_top5_IPSAE_pose_TM_available_pairs_v2.pptx');
const owners=[1,7,13,19];
const result=await finalizePresentation({workspaceDir,candidatePath,finalPath,pythonExecutable:'CONFIGURED_ROOT/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',integrityValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','15240000,8572500','--validate-heading-fit',...owners.flatMap(n=>['--require-native-table-slide',String(n)])],explicitTotalSlideCount:24,requiredNativeTableOwnerSlides:owners,requiredNativeChartOwnerSlides:owners,materializeLiteralChartWorkbooks:true,nativeChartTargetApplication:'powerpoint',fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,receiptPath:path.join(build,'validation.json')});
await fs.writeFile(path.join(build,'finalization.json'),JSON.stringify(result,null,2));
const fp=await PresentationFile.importPptx(await FileBlob.load(finalPath));
for(let i=0;i<24;i++){
 const s=fp.slides.getItem(i);const blob=await fp.export({slide:s,format:'png',scale:1});
 await fs.writeFile(path.join(build,`slide-${i+1}.png`),new Uint8Array(await blob.arrayBuffer()));
 await fs.writeFile(path.join(build,`slide-${i+1}.layout.json`),await (await s.export({format:'layout'})).text());
}
await fs.writeFile(path.join(workspaceDir,'manifest-v4.json'),JSON.stringify({final_path:finalPath,final_sha256:sha(await fs.readFile(finalPath)),selected_path:selectedPath,selected_sha256:sha(await fs.readFile(selectedPath)),slide_count:24,design_slides:20,cohort_plot_slides:4,native_scatter_charts:8,font,renderer_dir:renderer,ranking_metric:'mean_ipsae times binder_pose_tm_target_aligned'},null,2));
console.log(finalPath);
