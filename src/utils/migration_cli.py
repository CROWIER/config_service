import os
import sys
import argparse
from datetime import datetime


class MigrationCLI:
    def __init__(self):
        self.migrations_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'validators'
        )

    def create_migrations_dir(self):
        if not os.path.exists(self.migrations_dir):
            os.makedirs(self.migrations_dir)
            print(f"Created validators directory: {self.migrations_dir}")

    def get_next_migration_number(self):
        if not os.path.exists(self.migrations_dir):
            return "001"

        migration_files = [
            f for f in os.listdir(self.migrations_dir)
            if f.endswith('.sql') and f[:3].isdigit()
        ]

        if not migration_files:
            return "001"

        numbers = [int(f[:3]) for f in migration_files]
        next_num = max(numbers) + 1
        return f"{next_num:03d}"

    def create_migration(self, name, description=""):
        self.create_migrations_dir()

        migration_number = self.get_next_migration_number()
        filename = f"{migration_number}_{name}.sql"
        filepath = os.path.join(self.migrations_dir, filename)

        template = f"-- Migration {migration_number}: {name}\n\n"

        with open(filepath, 'w') as f:
            f.write(template)

        print(f"Created migration: {filepath}")
        return filepath

    def list_migrations(self):
        if not os.path.exists(self.migrations_dir):
            print("No validators directory found")
            return

        migration_files = sorted([
            f for f in os.listdir(self.migrations_dir)
            if f.endswith('.sql')
        ])

        if not migration_files:
            print("No migration files found")
            return

        print("Migration files:")
        for migration_file in migration_files:
            print(f"  - {migration_file}")


def main():
    parser = argparse.ArgumentParser(description='Configuration Service Migration Tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    create_parser = subparsers.add_parser('create', help='Create a new migration')
    create_parser.add_argument('name', help='Migration name (snake_case)')
    create_parser.add_argument('--description', '-d', help='Migration description')

    list_parser = subparsers.add_parser('list', help='List all validators')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = MigrationCLI()

    if args.command == 'create':
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', args.name):
            print("Error: Migration name should contain only letters, numbers, and underscores")
            sys.exit(1)

        cli.create_migration(args.name, args.description)

    elif args.command == 'list':
        cli.list_migrations()


if __name__ == '__main__':
    main()
