import io,json,sys,unittest,subprocess,time
from pathlib import Path
label,evidence=sys.argv[1:3]
root=Path.cwd().resolve()
before=subprocess.check_output(['git','status','--porcelain=v1'],text=True,stderr=subprocess.DEVNULL)
started=time.monotonic()
suite=unittest.defaultTestLoader.discover('tests',pattern='static_*test.py')
result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
failures=[{'id':test.id(),'method':getattr(test,'test_case',test).id(),'traceback':trace} for test,trace in result.failures]
errors=[{'id':test.id(),'traceback':trace} for test,trace in result.errors]
record={'root':str(root),'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'tests':result.testsRun,'failures':failures,'errors':errors,'failed_methods':len({r['method'] for r in failures}),'seconds':round(time.monotonic()-started,3),'status_before':before,'status_after':subprocess.check_output(['git','status','--porcelain=v1'],text=True,stderr=subprocess.DEVNULL)}
p=Path(evidence)
data=json.loads(p.read_text());data['results'][label]=record;p.write_text(json.dumps(data,indent=2),encoding='utf-8')
print(json.dumps({'scope':label,'tests':record['tests'],'failures':len(failures),'errors':len(errors),'failed_methods':record['failed_methods'],'seconds':record['seconds'],'status_preserved':record['status_before']==record['status_after']}))
for failure in failures+errors:
    print(failure['id'])
