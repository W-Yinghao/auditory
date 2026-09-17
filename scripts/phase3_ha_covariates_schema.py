#!/usr/bin/env python3
import csv,json,os
from pathlib import Path
import openpyxl
R=Path(__file__).resolve().parents[1]; M=R/'private/inventory_001/file_path_map.csv'; OUT=R/'results/phase3_ha_covariates_schema.json'
def main():
 assert os.getenv('SLURM_JOB_ID')
 path=next(Path(r[3]) for r in csv.reader(M.open()) if r and r[0]=='file_e254c9a75c971ac7d4e76bf6df2b4030')
 wb=openpyxl.load_workbook(path,read_only=False,data_only=True); ws=wb['Sheet1']; rows=list(ws.iter_rows(values_only=True)); hdr=rows[0]
 OUT.write_text(json.dumps({'job_id':os.environ['SLURM_JOB_ID'],'file_id':'file_e254c9a75c971ac7d4e76bf6df2b4030','sheet':'Sheet1','columns':[{'column':i+1,'header':str(v) if v is not None else None} for i,v in enumerate(hdr)],'merged_ranges':[str(x) for x in ws.merged_cells.ranges]},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
