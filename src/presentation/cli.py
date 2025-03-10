import click
from datetime import datetime
import os
from ..application.cost_analyzer import CostAnalyzer
from ..infrastructure.aws.aws_cost_repository import AWSCostRepository
from ..infrastructure.formatters.csv_formatter import CSVFormatter
from ..infrastructure.formatters.table_formatter import TableFormatter
from ..config.settings import Settings

@click.command()
@click.option('--days', default=7, help='Number of days to fetch AWS costs.')
@click.option('--aws-profile', default=None, help='AWS profile name to use.')
@click.option('--category', default="all", 
              type=click.Choice(Settings.COST_PROFILES.keys()), 
              help='Cost category to analyze.')
@click.option('--output', default='/app/outputs', 
              help='Output directory name for CSV files.')
def cli(days: int, aws_profile: str, category: str, output: str):
    """AWS Cost Analysis CLI"""
    repository = AWSCostRepository(profile_name=aws_profile)
    analyzer = CostAnalyzer(repository)
    
    # Get service filter for category
    service_filter = Settings.get_services_for_profile(category)
    
    # Analyze costs
    costs = analyzer.analyze_costs(days, service_filter)
    
    # Generate timestamp for files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Format and display general costs
    if output:
        costs_filepath = os.path.join(output, f"aws_{category}_costs_{timestamp}.csv")
        CSVFormatter.save_to_file(costs, costs_filepath)
        click.echo(f"✅ Costs saved to {costs_filepath}")

    # Display costs in terminal
    costs_table = TableFormatter.format_table(costs)
    click.echo("\n📊 AWS Services Costs:")
    click.echo(costs_table)

    # Special handling for databases category
    if category == "databases":
        db_instances = analyzer.analyze_databases(days)
        
        if db_instances:
            # Save database details if output is specified
            if output:
                db_filepath = os.path.join(output, f"aws_{category}_instances_{timestamp}.csv")
                CSVFormatter.save_to_file(db_instances, db_filepath)
                click.echo(f"✅ Database instances details saved to {db_filepath}")

            # Display database details in terminal
            db_table = TableFormatter.format_table(db_instances, add_total=False)
            click.echo("\n📊 RDS Database Instances:")
            click.echo(db_table)

if __name__ == '__main__':
    cli() 