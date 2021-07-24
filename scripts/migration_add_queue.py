from playhouse.migrate import *


def main():
    db = SqliteDatabase('matches.db')
    migrator = SqliteMigrator(db)

    queue_field = CharField(default='competitive')

    migrate(
        migrator.add_column('matchmodel', 'queue', queue_field)
    )


if __name__ == '__main__':
    main()
