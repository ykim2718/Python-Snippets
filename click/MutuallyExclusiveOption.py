import click

class MutuallyExclusiveOption(click.Option):
    def __init__(self, *args, **kwargs):
        # Pop the mutually_exclusive list from kwargs
        self.mutually_exclusive = set(kwargs.pop("mutually_exclusive", []))
        help = kwargs.get("help", "")
        if self.mutually_exclusive:
            excl_str = ", ".join(self.mutually_exclusive)
            # Append mutual exclusivity info to the help text
            kwargs["help"] = help + f" [Mutually exclusive with: {excl_str}]"
        super().__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self.name in opts:
            for other_opt in self.mutually_exclusive:
                if other_opt in opts:
                    # Raise an error if both mutually exclusive options are provided
                    raise click.UsageError(
                        f"Illegal usage: '{self.name}' is mutually exclusive with '{other_opt}'."
                    )
        return super().handle_parse_result(ctx, opts, args)

@click.command()
# Define mutually exclusive options using the custom class
@click.option("--id", cls=MutuallyExclusiveOption, mutually_exclusive=["name"], help="User ID")
@click.option("--name", cls=MutuallyExclusiveOption, mutually_exclusive=["id"], help="User Name")
def hello(id, name):
    click.echo(f"ID: {id}, Name: {name}")

if __name__ == "__main__":
    hello()