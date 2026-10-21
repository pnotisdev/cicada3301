import sys,concurrent.futures as cf
sys.path.insert(0,__import__('os').path.join(__import__('os').path.dirname(__file__),'..','chanscreen','v2','step4'))
import null_scan_mid as S
if __name__=='__main__':
    todo=[(0,ci) for ci in range(13,1,-1) if not (S.DEST/f'mid_w0_c{ci:02d}.json').exists()]
    with cf.ProcessPoolExecutor(max_workers=2,initializer=S.init) as ex:
        for f in [ex.submit(S.task,a) for a in todo]: print(f.result(),flush=True)
