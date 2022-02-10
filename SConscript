Import('env')
Import('selected_platform')

import methods
import os
import glsl_builders

sconscript_env = env.Clone()

apnames = env['active_platforms']['names']
ap = env['active_platforms']['ids']

targets = []
sources = []
for x in ap:
    names = ["logo"]
    if os.path.isfile(sconscript_env.File("#" + x + "/run_icon.png").abspath):
        names.append("run_icon")
    for name in names:
        targets += [x + "/" + name + ".gen.h"]
        sources += [env.File('#' + x + "/" + name + ".png")]

sconscript_env.Command(
    targets,
    sources,
    methods.save_active_platforms
)

# Build subdirs, the build order is dependent on link order.
sconscript_env.SConscript("core/SCsub", duplicate=0)
sconscript_env.SConscript("servers/SCsub", duplicate=0)
sconscript_env.SConscript("scene/SCsub", duplicate=0)
sconscript_env.SConscript("editor/SCsub", duplicate=0)
sconscript_env.SConscript("drivers/SCsub", duplicate=0)

sconscript_env.SConscript("platform/SCsub", duplicate=0)
sconscript_env.SConscript("modules/SCsub", duplicate=0)
if env["tests"]:
    sconscript_env.SConscript("tests/SCsub", duplicate=0)
sconscript_env.SConscript("main/SCsub", duplicate=0)

sconscript_env.SConscript("platform/" + selected_platform + "/SCsub", duplicate=0)  # Build selected platform.

