from dataclasses import dataclass

from beet import Context

from mecha import Mecha
from mecha.api import export


def beet_default(ctx: Context):
    mc = ctx.inject(Mecha)

    # Relative and absolute paths

    with mc.function("foo"):
        mc.say("hello")

    with mc.function("foo/bar") as func_name:
        mc.say("hello")
        mc.say(func_name)

    with mc.function("absolute:path/to/function"):
        mc.say("foo")

    # Reopening is ok

    with mc.function("absolute:path/to/function"):
        mc.say("add more")

    # Local override

    with mc.override(path="thingy"):
        with mc.function("dope"):
            mc.say("hey")

    # Nested functions

    with mc.function("foo"):
        mc.say("before")
        with mc.function("bar"):  # This inserts a /function command in the parent
            mc.say("inside")
        mc.say("after")

    # The name can be parametrized

    with mc.function("zprivate/generated_{}") as func_name:
        mc.say(func_name)

    # Parametrized name can't be reopened and instead will create a new one

    with mc.function("zprivate/generated_{}") as func_name:
        mc.say(func_name)

    # You can still reopen functions explicitly

    with mc.function(func_name):
        mc.say("add more")

    # Auto-generated path (default arg is "generated_{index}")

    with mc.function() as generated_path:
        mc.say(generated_path)

    # Use python functions, these 3 do the same thing

    def do_thing(mc: Mecha):
        mc.say("hey")

    with mc.function("do_thing"):
        do_thing(mc)

    mc.function("do_thing", do_thing)
    mc.function(do_thing)

    # No auto-generated path since when the path is omitted the path is derived from
    # the function name but you can still parametrize the path

    mc.function("do_thing_{}", do_thing)

    # You can't reopen functions once they're created

    mc.function(do_thing)  # define and run do_thing
    mc.function(do_thing)  # only run do_thing

    ctx.require(plugin1)
    ctx.require(plugin2)
    ctx.require(plugin3)
    ctx.require(Dope4)
    ctx.require(Dope5)
    ctx.require(Dope6)
    ctx.require(plugin77)
    ctx.require(Dope7)


class Dope1:
    def __init__(self, ctx: Context):
        mc = ctx.inject(Mecha)
        mc.function(self.do_thing)
        mc.function(self.do_stuff)

    def do_thing(self, mc: Mecha):
        mc.say("thing")

    def do_stuff(self, mc: Mecha):
        mc.say("stuff")
        mc.function(self.do_other)

    def do_other(self, mc: Mecha):
        mc.say("other")


def plugin1(ctx: Context):
    ctx.inject(Dope1)


@dataclass
class Dope2:
    ctx: Context

    def __post_init__(self):
        mc = self.ctx.inject(Mecha)
        mc.function(self.do_thing)
        mc.function(self.do_stuff)

    def do_thing(self, mc: Mecha):
        mc.say("thing")

    def do_stuff(self, mc: Mecha):
        mc.say("stuff")


def plugin2(ctx: Context):
    ctx.inject(Dope2)


class Dope3(Mecha):
    def __init__(self, ctx: Context):
        super().__init__(ctx, namespace="ding_dong")
        self.function(self.do_thing)
        self.function(self.do_stuff)

    def do_thing(self):
        self.say("thing")

    def do_stuff(self, mc: Mecha):
        mc.say("stuff")


def plugin3(ctx: Context):
    ctx.inject(Dope3)


# When you subclass Mecha it sets the default path based on
# the name of the class. Path and namespace are customizable through
# init_subclass kwargs.


class Dope4(Mecha):
    def __init__(self, ctx: Context):
        super().__init__(ctx)
        self.function(self.do_thing)  # namespace:dope4/do_thing

    def do_thing(self):
        self.say("thing")


class Dope5(Mecha, namespace=__name__, path="maki"):
    def __init__(self, ctx: Context):
        super().__init__(ctx)
        self.function(self.do_thing)  # foo:maki/do_thing

    def do_thing(self):
        self.say("thing")


class Dope6(Mecha, namespace=__name__):
    @export
    def do_thing(self, mc: Mecha):
        mc.say("thing")

    @export
    def do_stuff(self, mc: Mecha, ayy: str = ""):
        mc.say("stuff")
        mc.function(self.do_other)

    def do_other(self, mc: Mecha):
        mc.say("other")

    print("HEY", do_stuff.__defaults__)


@export
def yoo(mc: Mecha):
    mc.say("thing")


def plugin77(ctx: Context):
    mc = ctx.inject(Mecha)
    mc.scan(__name__)
    mc.scan(Dope7)


class Dope7(Mecha):
    @export
    def thing(self):
        self.say("hey")
