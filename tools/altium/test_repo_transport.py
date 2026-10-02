"""Verify repo launchers through real MCP stdio, with optional read-only live probe."""
import asyncio
import hashlib
import json
from pathlib import Path
import sys
import tomllib

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[1]
EXPECTED = {'altium_inspect_library_component','altium_format_library_pins','altium_repartition_library_component'}

async def check(params,live=False):
    async with stdio_client(params) as (reader,writer):
        async with ClientSession(reader,writer) as session:
            await asyncio.wait_for(session.initialize(),timeout=35)
            tools = [t.name for t in (await session.list_tools()).tools]
            assert len(tools)==12 and EXPECTED.issubset(tools),tools
            async def call(name,args):
                response = await session.call_tool(name,args)
                assert not response.isError,response
                return json.loads(response.content[0].text)
            status = await call('altium_status',{'live':live})
            assert Path(status['state_dir']).resolve()==BASE/'runtime',status
            if live:
                assert status['live_check']['success'],status
            project=await call('altium_read_project',{'path':str(REPO/'ARTIX/ARTIX/ARTIX.PrjPcb')})
            assert len(project['sheets'])==6 and not project['missing_sheets'],project
            saved=await call('altium_read_saved_schematic',{'path':str(REPO/'ARTIX/ARTIX/CodexGenerated/Clock_Flash_Verified.SchDoc')})
            assert len(saved['components'])==8 and len(saved['pins'])==24,saved
            return {'tools':tools,'status':status,'project_sheets':len(project['sheets']),
                    'saved_components':8,'saved_pins':24,'saved_sha256':saved['sha256']}

async def main():
    library = REPO/'ARTIX/ARTIX/libraries/X7/XC7A50T-2FGG484I.SchLib'
    before = hashlib.sha256(library.read_bytes()).hexdigest()
    project_config=tomllib.loads((REPO/'.codex/config.toml').read_text(encoding='utf-8'))['mcp_servers']['altium_local']
    result={}
    for name,cwd in [('project_root',REPO),('project_subdirectory',REPO/'ARTIX/ARTIX')]:
        params=StdioServerParameters(command=project_config['command'],args=project_config['args'],cwd=str(cwd))
        result[name]=await check(params,live='--live' in sys.argv and name=='project_root')
    await asyncio.sleep(0.2)  # Allow Windows subprocess pipe callbacks to finish.
    result['original_library_unchanged']=hashlib.sha256(library.read_bytes()).hexdigest()==before
    assert result['original_library_unchanged']
    result['success']=True
    dest=REPO/'output/altium/repository-mcp-test.json'
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'success':True,'tools':12,'launch_locations':list(result)[:2],
                      'original_library_unchanged':True,'report':str(dest)}))

if __name__=='__main__':
    asyncio.run(main())
