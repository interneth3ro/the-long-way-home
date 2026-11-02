import io,json,sys,unittest,subprocess,hashlib
from pathlib import Path
scope,evidence=sys.argv[1:3]
root=Path.cwd().resolve();p=Path(evidence)
record=json.loads(p.read_text(encoding='utf-8'))
files=record['candidate_manifest_lf_sha256']
start={name:hashlib.sha256((root/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for name in files}
assert start==files
status=subprocess.check_output(['git','status','--porcelain=v1'],text=True,stderr=subprocess.DEVNULL)
suite=unittest.defaultTestLoader.discover('tests',pattern='static_*test.py')
result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
failures=[{'id':test.id(),'method':getattr(test,'test_case',test).id(),'traceback':trace} for test,trace in result.failures]
errors=[{'id':test.id(),'traceback':trace} for test,trace in result.errors]
focused=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','static_native_terrain_47_test.py'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
end={name:hashlib.sha256((root/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for name in files}
assert start==end
end_status=subprocess.check_output(['git','status','--porcelain=v1'],text=True,stderr=subprocess.DEVNULL)
assert status==end_status
out={'root':str(root),'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'tree':subprocess.check_output(['git','rev-parse','HEAD^{tree}'],text=True).strip(),'tests':result.testsRun,'failure_records':failures,'errors':errors,'failed_methods':len({r['method'] for r in failures}),'focused_exit_code':focused.returncode,'focused_output':focused.stdout.decode('utf-8',errors='replace'),'status_unchanged':True,'candidate_hashes_unchanged':True,'status':status}
record=json.loads(p.read_text(encoding='utf-8'));record['results'][scope]=out;p.write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps({'scope':scope,'tests':result.testsRun,'failures':len(failures),'errors':len(errors),'focused_exit_code':focused.returncode,'status_unchanged':True}))
for failure in failures+errors:print(failure['id'])
