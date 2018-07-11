from functions import database
import bot_settings


class PrefixFunc:
    def __init__(self):
        self.db = database.Database()
        self.sdb = database.ServerDatabase()

    def get_prefix(self, user_id, server_id):
        prefix = self.db.get_value("prefix", user_id)
        prefixes = tuple(bot_settings.prefix)
        if prefix is not None and prefix[0] is not None:
            prefixes = (*prefixes, prefix[0])
        prefix = self.sdb.get_prefix(server_id)[0]
        if prefix is not None:
            prefixes = (*prefixes, prefix)
        return prefixes

    def set_prefix(self, prefix, table, id_):
        return self.db.set_value("prefix", prefix, id_, table)

    def get_user_prefix(self, user_id):
        prefix = self.db.get_value("prefix", user_id)
        return prefix
