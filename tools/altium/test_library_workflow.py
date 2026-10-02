"""Real MCP forward test against a disposable native SchLib; original is read-only."""
import asyncio
import hashlib
import json
from pathlib import Path
import shutil
import uuid

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

BASE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[2]
ORIGINAL = REPO/'ARTIX/ARTIX/libraries/X7/XC7A50T-2FGG484I.SchLib'
COMP = 'XC7A50T-2FGG484I'


async def main():
    trial = BASE/f'runtime/trials/WorkflowForwardTest-{uuid.uuid4().hex[:8]}.SchLib'
    source = REPO/'output/altium/XC7A50T-before-split.SchLib'
    if trial.exists():
        raise RuntimeError('Trial already exists; inspect previous result before rerunning')
    trial.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,trial)
    original_hash = hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()
    params = StdioServerParameters(command=str(BASE/'.venv/Scripts/python.exe'),args=[str(BASE/'cad_bridge.py'),'serve'])
    report = {}
    async with stdio_client(params) as (reader,writer):
        async with ClientSession(reader,writer) as session:
            await session.initialize()
            report['tools'] = [t.name for t in (await session.list_tools()).tools]
            async def call(name,args):
                response = await session.call_tool(name,args)
                if response.isError:
                    raise RuntimeError(response)
                data = json.loads(response.content[0].text)
                if name != 'altium_status' and not data.get('success'):
                    raise RuntimeError(json.dumps(data))
                return data
            health = await call('altium_status',{'live':True})
            assert health['live_check']['success'],health
            report['live'] = True
            before = await call('altium_inspect_library_component',{'path':str(trial),'component':COMP})
            report['before'] = {'parts':before['result']['part_count'],'pins':before['result']['pin_count'],'job':before['job_dir']}
            assert before['result']['pin_count'] == 484
            report['format_7mm_12pt'] = await call('altium_format_library_pins',{'path':str(trial),'component':COMP,'length_mm':7,'font_name':'GOST Common','font_size':12})
            report['repartition'] = await call('altium_repartition_library_component',{'path':str(trial),'component':COMP,'manifest_path':str(BASE/'manifests/xc7a50t-parts.json'),'replace_body':True})
            report['format_5mm_10pt'] = await call('altium_format_library_pins',{'path':str(trial),'component':COMP,'length_mm':5,'font_name':'GOST Common','font_size':10})
            after = await call('altium_inspect_library_component',{'path':str(trial),'component':COMP})
            assert after['result']['pin_count'] == 484 and after['result']['part_count'] == 10
            assert all(p['length_coord'] == 1968504 and p['name_font'] == 'GOST Common' and p['designator_font'] == 'GOST Common' and p['name_size'] == p['designator_size'] == 10 for p in after['result']['pins'])
            report['after'] = {'parts':10,'pins':484,'job':after['job_dir']}
            # Restore visible original library; this read does not save or mutate it.
            restored = await call('altium_inspect_library_component',{'path':str(ORIGINAL),'component':COMP})
            report['original_readback_pins'] = restored['result']['pin_count']
    report['original_sha256'] = hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()
    assert report['original_sha256'] == original_hash
    report['original_unchanged'] = True
    report['success'] = True
    dest = REPO/'output/altium/library-workflow-mcp-test.json'
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'success':True,'tool_count':len(report['tools']),'before':report['before'],'after':report['after'],'original_unchanged':True,'report':str(dest)}))


if __name__ == '__main__':
    asyncio.run(main())
