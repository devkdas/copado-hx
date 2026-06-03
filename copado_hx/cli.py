from copado_hx._app import app

import copado_hx.commands.version_cmd as _v
import copado_hx.commands.auth_cmds as _a
import copado_hx.commands.story_cmds as _s
import copado_hx.commands.pipeline_cmds as _p
import copado_hx.commands.test_cmds as _t
import copado_hx.commands.ai_cmds as _ai
import copado_hx.commands.workflow_cmds as _wf
import copado_hx.commands.env_cmds as _e
import copado_hx.commands.mcp_cmd as _mcp
import copado_hx.commands.config_cmd as _cfg
import copado_hx.commands.demo_cmd as _demo
import copado_hx.commands.guide_cmds as _guide
_ = (_v, _a, _s, _p, _t, _ai, _wf, _e, _mcp, _cfg, _demo, _guide)

if __name__ == "__main__":
    app()
