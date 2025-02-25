import copy
import os
import click
from services import CostService
from repository import AWSCostRepository
from formatter import CostFormatter
from settings import COST_PROFILES
import datetime

@click.command()
@click.option('--days', default=7, help='Number of days to fetch AWS costs.')
@click.option('--aws-profile', default=None, help='AWS profile name to use.')
@click.option('--category', default="all", type=click.Choice(COST_PROFILES.keys()), help='Cost category to analyze.')
@click.option('--output', default='/app/outputs', help='Output directory name for CSV files.')
def cli(days, aws_profile, category, output):
    """
    CLI to fetch AWS costs and optionally save details into separate CSV files.
    """

    repository = AWSCostRepository(profile_name=aws_profile)
    service = CostService(repository)

    # Fetch AWS cost data based on category
    costs = service.get_costs_last_days(days, category)

    if output:
        # Ensure output directory exists
        output_dir = os.path.abspath(output)
        os.makedirs(output_dir, exist_ok=True)
        
        # Add timestamp to filenames to avoid overwrites
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save general costs CSV
        costs_output_path = os.path.join(output_dir, f"aws_{category}_costs_{timestamp}.csv")
        CostFormatter.save_as_csv(copy.deepcopy(costs), costs_output_path)
        click.echo(f"✅ Costs data saved to {costs_output_path}")

    # Special handling for "databases" category
    if category == "databases":
        db_instances = repository.get_database_instances(total_days=days)
        if db_instances:
            if output:
                db_output_path = os.path.join(output_dir, f"aws_{category}_instances.csv")
                CostFormatter.save_as_csv(copy.deepcopy(db_instances), db_output_path)
                click.echo(f"✅ RDS instance details saved to {db_output_path}")

            # Display RDS details in CLI
            db_table = CostFormatter.format_as_table(copy.deepcopy(db_instances), add_total=True)
            click.echo("📊 RDS Database Instances:")
            click.echo(db_table)

    # Display general costs in CLI
    cost_table = CostFormatter.format_as_table(copy.deepcopy(costs), add_total=True)
    click.echo("📊 AWS Services Costs:")
    click.echo(cost_table)

if __name__ == '__main__':
    cli()