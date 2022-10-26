from beet import Context
from beet.library.data_pack import Function


def beet_default(ctx: Context):
    ctx.inject(GameController)
    ctx.data["foo:bar"] = Function("say hello")


class Component:
    def __init__(self, ctx: Context):
        self.ctx = ctx


class Signal:
    def __call__(self, f):
        pass


class GameController(Component):
    def update(self):
        self.each(Player).attach(FooBar)

    def teardown(self):
        self.each(FooBar).detach()


class Other(Component):
    on_stuff = Signal()

    def setup(self):
        with self.filter(...):
            self.on_stuff.dispatch()


class FooBar(Component):
    def setup(self):
        pass

    def update(self):
        with self.filter(Coordinates.BELOW * 0.5 == "stone"):
            self.remove()

    @Other.on_stuff
    def hello(self):
        self[Other].something()

    def teardown(self):
        self.say("bye bye")
