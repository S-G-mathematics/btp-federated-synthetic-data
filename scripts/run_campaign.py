"""One-lane subprocess scheduler with shared lease, timeouts and resume."""
import argparse, fcntl, itertools, json, os, shutil, subprocess, sys, time
from pathlib import Path
import yaml

def main():
 p=argparse.ArgumentParser();p.add_argument('--profile',choices=['smoke','pilot','projected_pilot','full'],default='smoke')
 p.add_argument('--experiments',default='all');p.add_argument('--all-cells',action='store_true')
 p.add_argument('--generators',default='independent');p.add_argument('--partitions',default='age')
 p.add_argument('--clients',default='5');p.add_argument('--seeds',default='101')
 p.add_argument('--official-test',action='store_true');p.add_argument('--selection-file')
 p.add_argument('--out',default='results');a=p.parse_args()
 if a.official_test:raise SystemExit('Legacy multi-method official-test route is disabled; use the dedicated full-freeze confirmation runner.')
 root=Path(__file__).resolve().parents[1];os.chdir(root)
 config=yaml.safe_load(Path('configs/campaign.yaml').read_text());resources=yaml.safe_load(Path('configs/resources.yaml').read_text())
 lane=Path(os.path.expanduser(resources['shared_compute_lease']));lane.parent.mkdir(parents=True,exist_ok=True)
 lock=lane.open('a+')
 try:fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:raise SystemExit('Shared heavy-compute lease is occupied; checkpoint and wait for the other project.')
 # EC2-only heavy work; smoke allowed elsewhere as software verification.
 if a.profile!='smoke':
  dmi_parts=[]
  for name in ('sys_vendor','product_name'):
   try:dmi_parts.append((Path('/sys/devices/virtual/dmi/id')/name).read_text(errors='ignore'))
   except OSError:pass
  dmi=' '.join(dmi_parts)
  if 'amazon' not in dmi.lower() and not dmi.lower().startswith('ec2'):
   raise SystemExit('Heavy profiles must run on verified existing EC2. Do not bypass this check on a laptop.')
 def safe_capacity():
  mem=Path('/proc/meminfo').read_text()
  available=next(int(line.split()[1])*1024 for line in mem.splitlines() if line.startswith('MemAvailable:'))
  if available<resources['minimum_available_ram_gib']*2**30:raise RuntimeError('Insufficient available RAM; other workloads take priority.')
  if shutil.disk_usage('.').free<resources['minimum_free_disk_gib']*2**30:raise RuntimeError('Disk reserve reached.')
 axes=(config['generators'],config['partitions'],config['clients'],config['development_seeds']) if a.all_cells else (
     a.generators.split(','),a.partitions.split(','),[int(x) for x in a.clients.split(',')],[int(x) for x in a.seeds.split(',')])
 start=time.monotonic();limit=resources['smoke_wall_seconds'] if a.profile=='smoke' else resources['campaign_wall_seconds']
 jobs=[];Path('logs').mkdir(exist_ok=True)
 for generator,partition,k,seed in itertools.product(*axes):
  remaining=limit-(time.monotonic()-start)
  if remaining<=1:break
  safe_capacity();timeout=min(resources['cell_timeout_seconds'],int(remaining))
  command=[sys.executable,'-m','btp.run','--profile',a.profile,'--generator',generator,'--partition',partition,
      '--clients',str(k),'--seed',str(seed),'--experiments',a.experiments,'--out',a.out,'--wall-seconds',str(timeout)]
  if a.official_test:
   if not a.selection_file:raise SystemExit('Official test requires --selection-file')
   command+=['--official-test','--selection-file',a.selection_file]
  name=f'{a.profile}_{generator}_{partition}_{k}_{seed}';began=time.time()
  env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1','PYTHONHASHSEED':str(seed)}
  with open(f'logs/{name}.log','a') as log:
   try:
    result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=timeout,env=env)
    status='completed' if result.returncode==0 else 'failed'
   except subprocess.TimeoutExpired:status='timed_out_checkpoint_retained'
  jobs.append({'job':name,'status':status,'wall_seconds':time.time()-began,'command':command})
  Path('logs/campaign_status.json').write_text(json.dumps(jobs,indent=2))
  print(name,status,flush=True)
  if status!='completed':raise SystemExit('Job stopped. Read its log and resolve the failure before scaling.')
 if not jobs:raise SystemExit('No jobs started within wall-time budget.')
 print('Campaign bounded run finished; rerun resumes compatible completed phases.')

if __name__=='__main__':main()
