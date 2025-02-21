import os
import click
from services import CostService
from repository import AWSCostRepository
from formatter import CostFormatter
from settings import COST_PROFILES

@click.command()
@click.option('--days', default=7, help='Number of days to fetch AWS costs.')
@click.option('--aws-profile', default=None, help='AWS profile name to use.')
@click.option('--cost-profile', default="all", type=click.Choice(COST_PROFILES.keys()), help='Cost profile filter.')
@click.option('--output', default=None, help='Save output as a CSV file (e.g., outputs/aws_costs.csv).')
@click.option('--db-instances', 'db_instances_flag', is_flag=True, help='Retrieve details about RDS database instances.')
def cli(days, aws_profile, cost_profile, output, db_instances_flag):
    """
    CLI to fetch AWS costs for the last N days.
    Implements Dependency Inversion Principle (DIP) by injecting repository dependency.
    """

    # Dependency Injection: Use AWSCostRepository
    repository = AWSCostRepository(profile_name=aws_profile)
    service = CostService(repository)

    # Fetch AWS cost data
    costs = service.get_costs_last_days(days, cost_profile)

    # Fetch and display database instances if requested
    if db_instances_flag:
        db_data = repository.get_database_instances()
        table = CostFormatter.format_as_table(db_data)
        click.echo("📊 **RDS Database Instances:**")
        click.echo(table)

    # Ensure output is correctly handled
    if output:
        output_path = os.path.abspath(output)  # Ensure absolute path
        CostFormatter.save_as_csv(costs, output_path)
        click.echo(f"✅ Cost data saved to {output_path}")
    else:
        # Format and display results in the terminal
        table = CostFormatter.format_as_table(costs)
        click.echo(table)

if __name__ == '__main__':
    cli()