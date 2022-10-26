import json

commands = json.load(open("commands.json"))



def generate_api(parent):
    for name, node in parent.get("children", {}).items():
        if node["type"] == "argument":
            key = ()
            args = (name,)
        else:
            key = (name,)
            args = ()

        if node.get("executable"):
            yield key, args

        for child_key, child_args in generate_api(node):
            yield key + child_key, args + child_args



for name, args in generate_api(commands):
    print('_'.join(name), args)
