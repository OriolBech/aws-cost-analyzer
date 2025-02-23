import os
import click
from services import CostService
from repository import AWSCostRepository
from formatter import CostFormatter
from settings import COST_PROFILES


@click.command()
@click.option('--days', default=7, help='Number of days to fetch AWS costs.')
@click.option('--aws-profile', default=None, help='AWS profile name to use.')
@click.option('--category', required=True, type=click.Choice(COST_PROFILES.keys()), help='Cost category to analyze.')
@click.option('--output', default=None, help='Save output as a CSV file (e.g., outputs/aws_costs.csv).')
def cli(days, aws_profile, category, output):
    """
    CLI to fetch AWS costs based on selected category.
    """

    repository = AWSCostRepository(profile_name=aws_profile)
    service = CostService(repository)

    # Fetch AWS cost data based on category
    costs = service.get_costs_last_days(days, category)

    # Special handling for "databases" category
    if category == "databases":
        db_instances = repository.get_database_instances()
        if db_instances:
            db_table = CostFormatter.format_as_table(db_instances, add_total=False)
            click.echo("📊 RDS Database Instances:")
            click.echo(db_table)

    # Save output if requested
    if output:
        output_path = os.path.abspath(output)
        CostFormatter.save_as_csv(costs, output_path)
        click.echo(f"✅ Cost data saved to {output_path}")

    # Display cost data
    cost_table = CostFormatter.format_as_table(costs, add_total=True)
    click.echo(cost_table)


if __name__ == '__main__':
    cli()