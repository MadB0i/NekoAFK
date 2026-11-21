# Preserved optional character work

`character/` preserves all previous VRoid, VRM, GLB, Blender, animation, render,
and validation assets. `prototype/` preserves the earlier browser labs and tests.
These are historical optional character-support resources, not product runtime
dependencies. Modeling and character refinement are stopped.

`inventory.json` records original paths, sizes, and SHA-256 hashes before moving
the files. Replace the original `assets/character/` or `prototype/` prefix with
the corresponding archive directory to validate a file. Dependencies and Python
caches were preserved but omitted from hashing. Nothing was deleted.
