class StepTracker(Component):
    """Component that tracks steps.

    The component emits a `step_on_block` signal each time the attached
    entity steps on a block. The signal is only triggered once and will
    not be triggered if the entity is in the air.
    """

    # Component fields are stored in scoreboards. Here we set the
    # default values to 0.
    prev_x = Field(0)
    prev_y = Field(0)
    prev_z = Field(0)

    # Signals use function tags to call other functions.
    step_on_block = Signal()

    def update(self):
        """Emit the `step_on_block` signal if the player moved.

        The `update` method runs every tick. The type of `self` is an
        entity set. Entity sets use selectors and entity tags to make it
        possible to treat a collection of entities as a data structure.
        `self` is an entity set containing only the current entity.
        """

        # Entity sets can be bound to nbt paths. This would be
        # equivalent to `data get`.
        x, y, z = (self.nbt["Pos"][i] for i in range(3))

        # You can execute code conditionally by filtering entity sets.
        # The `filter` method only keeps entities that match all the
        # given conditions and the `reject` method discards entities
        # that match all the given conditions. Here we only execute the
        # code block if the current entity has moved since the last call
        # to `update`.
        with self.reject(x == self.prev_x, y == self.prev_y, z == self.prev_z):

            # Instances of the `Coordinates` class support arithmetic
            # operations and can be compared to block tags and block ids.
            # `Coordinates.BELOW * 0.5` represents `~ ~-0.5 ~`. Here we
            # make sure that the entity is not above an air block. This
            # would be equivalent to `execute if block`.
            with self.filter(Coordinates.BELOW * 0.5 != "air"):

                # The `emit` method is synchronous and runs all the
                # functions subscribed to the signal.
                self.step_on_block.emit()

        # Assigning to fields is equivalent to `execute store`. Here we
        # set the previous coordinates to the current coordinates.
        self.prev_x = x
        self.prev_y = y
        self.prev_z = z


class LoudFootsteps(Component):
    """Show a message in the chat when stepping on certain blocks."""

    @StepTracker.step_on_block
    def be_loud(self):
        """Display an appropriate message depending on the block below.

        Component methods can subscribe to signals by using them as
        decorators. Here the function will be called whenever the
        `StepTracker` component emits the `step_on_block` signal. This
        also makes the `StepTracker` component a dependency of the
        `LoudFootsteps` component, meaning that attaching `LoudFootsteps`
        to an entity will also automatically attach `StepTracker`.
        """

        # Normal python loops and conditions are executed at build time
        # whereas using entity sets in context managers result in
        # runtime conditions. Therefore it's possible to combine the two
        # to seamlessly use python as a code generator.
        for block_type in ["note_block", "#planks"]:

            # Here the for loop will generate one `execute if block`
            # for each block type.
            with self.filter(Coordinates.BELOW * 0.5 == block_type):
                if block_type == "note_block":
                    self.log("Your upstairs neighbors playing music")
                else:
                    self.log("They're walking around at night again")


class Main(Module):
    """Attach the `LoudFootsteps` component to players.

    Modules are global components that are only instantiated once.
    They're not attached to any entities but components and modules still
    have the same lifecycle methods:
      - setup
      - update
      - teardown
      - load

    The `load` method is called when databacks are reloaded.
    """

    def update(self):
        """Attach the `LoudFootsteps` component to everyone.

        In components and modules you can use selectors to create entity
        sets relative to the execution context:
          - each
          - nearest
          - furthest
          - random

        The `attach` method attaches a given component to each individual
        entity in an entity set. The method ignores entities where the
        component is already attached. The `Player` component is defined
        by the framework and is implicitly attached to all players.
        """
        self.each(Player).attach(LoudFootsteps)

    def teardown(self):
        """Remove all `LoudFootsteps` components."""
        self.each(LoudFootsteps).detach()
