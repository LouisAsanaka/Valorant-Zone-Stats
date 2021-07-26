from playhouse.migrate import *


def main():
    db = SqliteDatabase('matches.db')
    migrator = SqliteMigrator(db)

    stats_field = CharField(default=None, null=True)

    migrate(
        migrator.drop_column('matchmodel', 'stats'),
        migrator.add_column('matchmodel', 'stats', stats_field)
    )


if __name__ == '__main__':
    main()
