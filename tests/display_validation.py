"""Validate the real native windows against available Windows display modes.

No browser viewport or device-scale emulation is used. Display changes are
temporary and restored in finally; unsupported modes are reported as blockers.
Run with --inspect to inventory modes without changing anything.
"""
import argparse
import ctypes
from ctypes import wintypes as w
import json
import pathlib
import time
from playwright.sync_api import sync_playwright, expect

ROOT = pathlib.Path(__file__).resolve().parents[1]
ART = ROOT/'.artifacts/premium-validation'

class Mode(ctypes.Structure):
    _fields_ = [('device',w.WCHAR*32),('spec',w.WORD),('driver',w.WORD),
                ('size',w.WORD),('extra',w.WORD),('fields',w.DWORD),
                ('display',ctypes.c_byte*16),('color',w.SHORT),('duplex',w.SHORT),
                ('yres',w.SHORT),('tt',w.SHORT),('collate',w.SHORT),('form',w.WCHAR*32),
                ('logpixels',w.WORD),('bpp',w.DWORD),('width',w.DWORD),('height',w.DWORD),
                ('flags',w.DWORD),('frequency',w.DWORD),('icm_method',w.DWORD),
                ('icm_intent',w.DWORD),('media',w.DWORD),('dither',w.DWORD),
                ('reserved1',w.DWORD),('reserved2',w.DWORD),('pan_width',w.DWORD),('pan_height',w.DWORD)]

def mode(index):
    value=Mode(); value.size=ctypes.sizeof(Mode)
    return value if ctypes.windll.user32.EnumDisplaySettingsW(None,index,ctypes.byref(value)) else None

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--inspect',action='store_true')
    parser.add_argument('--port',type=int,default=9335)
    args=parser.parse_args()
    original=mode(-1)
    if original is None: raise RuntimeError('Cannot read current Windows display mode')
    modes=[]; index=0
    while (value:=mode(index)) is not None:
        modes.append(value); index+=1
    available=sorted(set((m.width,m.height) for m in modes))
    report={'original':[original.width,original.height], 'available_modes':available, 'tested':[], 'blockers':[]}
    if args.inspect:
        print(json.dumps(report,indent=2)); return
    ART.mkdir(parents=True,exist_ok=True)
    try:
        with sync_playwright() as p:
            browser=p.chromium.connect_over_cdp(f'http://127.0.0.1:{args.port}')
            pages=[pg for c in browser.contexts for pg in c.pages]
            settings=next(pg for pg in pages if 'surface=settings' in pg.url)
            dock=next(pg for pg in pages if 'surface=telemetry' in pg.url)
            def invoke(command,args=None):
                return settings.evaluate('async ([c,a])=>await window.__TAURI_INTERNALS__.invoke(c,a)',[command,args or {}])
            for width,height in [(1920,1080),(1366,768)]:
                candidates=[m for m in modes if m.width==width and m.height==height and m.bpp==original.bpp]
                if not candidates:
                    report['blockers'].append(f'{width}x{height} is not exposed by the display driver'); continue
                chosen=min(candidates,key=lambda m:abs(m.frequency-original.frequency))
                if (mode(-1).width,mode(-1).height)!=(width,height):
                    result=ctypes.windll.user32.ChangeDisplaySettingsW(ctypes.byref(chosen),0)
                    if result!=0:
                        report['blockers'].append(f'{width}x{height} mode change rejected: {result}'); continue
                deadline=time.time()+10
                while True:
                    diag=invoke('desktop_diagnostics')
                    if any(m['size']=={'width':width,'height':height} for m in diag['monitors']): break
                    if time.time()>deadline: raise AssertionError('Native monitor dimensions did not update')
                    settings.wait_for_timeout(100)
                invoke('window_action',{'action':'settings'})
                invoke('window_action',{'action':'recover'})
                if invoke('get_snapshot')['settings']['dock_collapsed']:
                    dock.get_by_role('button',name='Expand dock',exact=True).click()
                    expect(dock.locator('#app')).to_have_attribute('data-collapsed','false')
                for title in ['Agent connections','Verification','Appearance','Character','Desktop behavior']:
                    settings.get_by_role('button',name=title,exact=True).click()
                    expect(settings.locator('#save')).to_be_in_viewport()
                    assert settings.evaluate('document.documentElement.scrollWidth<=innerWidth')
                    assert settings.evaluate('document.body.scrollHeight<=innerHeight')
                    settings.screenshot(path=str(ART/f'{width}x{height}-settings-{title.split()[0].lower()}.png'),animations='disabled')
                assert dock.evaluate('document.documentElement.scrollWidth<=innerWidth')
                # Native dock resizing/recovery must retain usable primary controls.
                expect(dock.locator('#verify')).to_be_in_viewport()
                dock.screenshot(path=str(ART/f'{width}x{height}-dock.png'),animations='disabled')
                report['tested'].append({'resolution':[width,height],'native_diagnostics':invoke('desktop_diagnostics'),
                                        'settings_css':settings.evaluate('({width:innerWidth,height:innerHeight,devicePixelRatio})')})
            monitors=invoke('desktop_diagnostics')['monitors']
            if len(set(m['scale_factor'] for m in monitors))<2:
                report['blockers'].append('Physical mixed-DPI monitor transition requires a second monitor with a different scale')
            browser.close()
    finally:
        current=mode(-1)
        if current and (current.width,current.height)!=(original.width,original.height):
            result=ctypes.windll.user32.ChangeDisplaySettingsW(ctypes.byref(original),0)
            if result!=0: raise RuntimeError(f'Failed to restore original display mode: {result}')
        (ART/'display-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
