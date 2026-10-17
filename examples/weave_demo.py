"""Python AOP-style external runtime weaving, not Spring/AspectJ or an IDE plugin."""
from contextlib import contextmanager
from functools import wraps
import json,time
import student_program

@contextmanager
def weave(module,name,sink):
    original=getattr(module,name)
    @wraps(original)
    def around(*args,**kwargs):
        start=time.perf_counter()
        try:
            result=original(*args,**kwargs)
        except Exception as exc:
            sink({'probe':'exception','function':name,'type':type(exc).__name__})
            raise
        else:
            sink({'probe':'return','function':name})
            return result
        finally:
            sink({'probe':'duration','function':name,'seconds':time.perf_counter()-start})
    setattr(module,name,around)
    try:yield
    finally:setattr(module,name,original)

def main():
    original=student_program.mean
    trace=[]
    with weave(student_program,'mean',trace.append):
        assert student_program.mean([2,4])==3
        try:student_program.mean([])
        except ZeroDivisionError:pass
        else:raise AssertionError('Exception was swallowed')
    assert student_program.mean is original
    print(json.dumps({'status':'passed','source_modified':False,'probe_events':trace},indent=2))
if __name__=='__main__':main()
