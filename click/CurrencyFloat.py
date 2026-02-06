import click
import re

class CurrencyFloat(click.ParamType):
    """
    A custom Click parameter type that converts currency strings (e.g., $300,000)
    into a standard Python float (e.g., 300000.0).
    """
    name = "currency_float"

    def convert(self, value, param, ctx):
        # If the value is already a float or int, just return it
        if isinstance(value, (int, float)):
            return float(value)

        try:
            # 1. Remove currency symbols ($, £, etc.) and commas
            # 2. Strip any leading/trailing whitespace
            clean_value = re.sub(r'[^\d.]', '', value)
            
            # Convert to float
            return float(clean_value)
            
        except ValueError:
            self.fail(
                f"'{value}' is not a valid currency amount. "
                f"Example formats: $300,000, 300,000, or 300000",
                param,
                ctx,
            )

# --- Usage Example ---

@click.command()
@click.option(
    "--amount", 
    type=CurrencyFloat(), 
    help="Target asset amount (e.g., $300,000)"
)
def check_balance(amount):
    if amount:
        click.echo(f"Successfully converted!")
        click.echo(f"Raw Input Value -> Internal Float: {amount}")
        click.echo(f"Type: {type(amount)}")
    else:
        click.echo("Please provide an amount using --amount.")

if __name__ == "__main__":
    check_balance()