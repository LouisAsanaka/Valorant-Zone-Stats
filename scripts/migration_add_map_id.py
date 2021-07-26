from playhouse.migrate import *


def main():
    db = SqliteDatabase('matches.db')
    migrator = SqliteMigrator(db)

    map_id_field = CharField(default='')

    migrate(
        migrator.add_column('matchmodel', 'map_id', map_id_field)
    )


if __name__ == '__main__':
    main()
