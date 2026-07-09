from berrybrain_api.vault import create_note
from pathlib import Path

create_note(
    Path("/app/vault/permanentes/linux-shell-scripting.md"),
    open("/tmp/note1.md").read(),
)
print("nota 1 criada")
