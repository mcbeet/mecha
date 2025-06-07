"""
Script that downloads all commands trees from the mcmeta repository
"""

if not __name__ == "__main__":
    raise RuntimeError(
        "This script is not meant to be imported, run it directly to download command trees."
    )

URL = "https://raw.githubusercontent.com/misode/mcmeta/refs/tags/{version}-summary/commands/data.json"

from beet.resources.pack_format_registry import pack_format_registry
from beet.core.utils import split_version
import requests
from importlib.resources import files


for version in pack_format_registry:
    if version.type != "release":
        continue
    version_name = "_".join(map(str, split_version(version.id)))
    try:
        r = requests.get(URL.format(version=version.id))
        r.raise_for_status()
        path = files("mecha.resources").joinpath(f"{version_name}.json")

        with path.open("r") as f:
            f.write(r.text)
    except BaseException as e:
        print(f"Failed to download command tree for version {version_name}.")
        print(f"Error: {e}")
        continue
