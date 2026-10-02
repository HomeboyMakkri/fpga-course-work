"""Exercise actual MCP initialize/list/call over stdio, without editing CAD."""
import asyncio
import json
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

BASE = Path(__file__).resolve().parent

async def main():
    params = StdioServerParameters(command=str(BASE / '.venv/Scripts/python.exe'), args=[str(BASE / 'cad_bridge.py'), 'serve'])
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            info = await session.initialize()
            listing = await session.list_tools()
            status = await session.call_tool('altium_status', {'live': False})
            project = await session.call_tool('altium_read_project', {'path': str(BASE.parents[1]/'ARTIX/ARTIX/ARTIX.PrjPcb')})
            saved = await session.call_tool('altium_read_saved_schematic', {'path': str(BASE.parents[1]/'artix_expansion_board/Prototype.SchDoc')})
            data = json.loads(saved.content[0].text) if not saved.isError else None
            report = {'server': info.serverInfo.model_dump(), 'tools': [t.name for t in listing.tools], 'status': status.model_dump(), 'project': project.model_dump(),
                      'saved_file_check': {'isError':saved.isError,'sha256':data.get('sha256') if data else None,'component_count':len(data['components']) if data else None,'pin_count':len(data['pins']) if data else None}}
            if '--live' in sys.argv:
                live = await session.call_tool('altium_status', {'live':True})
                assert not live.isError
                live_data = json.loads(live.content[0].text)
                assert live_data['live_check']['success'], live_data
                compiled = await session.call_tool('altium_compile_project', {'path':str(BASE.parents[1]/'ARTIX/ARTIX/CodexGenerated/ARTIX_Codex_Verified.PrjPcb')})
                assert not compiled.isError, compiled
                compiled_data=json.loads(compiled.content[0].text)
                assert compiled_data['success'], compiled_data
                report['live_roundtrip']=live_data
                report['compile_result']=compiled_data
                manifest=json.loads((Path(__file__).parent/'manifests/clock_flash.json').read_text())
                actual={(p['ref'],p['pin']):p['net'] for p in compiled_data['result']['pins']}
                expected={(c['ref'],str(p['number'])):p['net'] for c in manifest['components'] for p in c['pins'] if p.get('net')}
                assert all(actual[k]==v for k,v in expected.items()), (actual,expected)
                report['compiled_pin_net_matches']=len(expected)
                final_path=str(BASE.parents[1]/'ARTIX/ARTIX/CodexGenerated/Clock_Flash_Verified.SchDoc')
                inspected=await session.call_tool('altium_inspect_schematic', {'path':final_path})
                assert not inspected.isError, inspected
                native=json.loads(inspected.content[0].text)
                assert native['success'], native
                assert next(c for c in native['result']['components'] if c['ref']=='J2')['value']=='W25Q128JVSIQTR'
                disk=await session.call_tool('altium_read_saved_schematic', {'path':final_path})
                assert not disk.isError, disk
                disk_data=json.loads(disk.content[0].text)
                assert len(disk_data['components'])==8 and len(disk_data['pins'])==24
                report['final_native_readback']={'success':True,'job_dir':native['job_dir'],'comment_restored':True}
                report['final_disk_readback']={'sha256':disk_data['sha256'],'components':8,'pins':24}
            print(json.dumps(report, indent=2))
            (BASE / 'runtime/mcp-transport-test.json').write_text(json.dumps(report,indent=2),encoding='utf-8')

asyncio.run(main())
