import sqlite3
from sqlite3 import Error
import random
from functions import rpg_functions
import traceback
import pickle

DATABASE_DIRECTORY = "data/database/database.db"


class Database:
    def __init__(self, file=DATABASE_DIRECTORY):
        self.db = self.create_connection(file)
        self.cursor = self.db.cursor()
        self.create_table("users", {"user_id": "primary key", "balance": "integer", "daily_time": "text",
                                    "command_uses": "integer", "prefix": "text"})

    def new_user(self, user_id, table="users"):
        # adds a new user to the database
        sql_text = f'INSERT INTO {table}(user_id) VALUES ({user_id});'
        self.commit_db(sql_text)
        return True

    def get_db(self, text, args=tuple()):
        # executes a select
        try:
            result = self.cursor.execute(text, args)
            return result
        except Exception as e:
            self.error_handler(e)

    def commit_db(self, text, args=tuple()):
        # executes a commit
        try:
            self.cursor.execute(text, args)
            self.db.commit()
            return True
        except Exception as e:
            self.error_handler(e)

    def get_value(self, value, user_id, table="users"):
        # returns the specified value or None
        self.check_if_exists(user_id)
        result = self.get_db(f'SELECT {value} FROM {table} WHERE user_id=?;', (user_id, ))
        if result is not None:
            return result.fetchone()
        return None

    def get_whole_db(self, table):
        # returns the whole database or None
        result = self.get_db(f"SELECT * FROM {table}")
        if result is not None:
            dblist = result.fetchall()
            columnNames = list(map(lambda x: x[0], result.description))  # students table column names list
            studentsAssoc = {}  # Assoc format is dictionary similarly
            # THIS IS ASSOC PROCESS
            for lineNumber, student in enumerate(dblist):
                studentsAssoc[lineNumber] = {}

                for columnNumber, value in enumerate(student):
                    studentsAssoc[lineNumber][columnNames[columnNumber]] = value
            return studentsAssoc
        return None

    @staticmethod
    def create_connection(db_file):
        # creates a connection to the database file
        try:
            conn = sqlite3.connect(db_file)
            return conn
        except Error as e:
            print(e)
        return None

    def create_table(self, table, entries: dict):
        # checks if the table exists, if no creates it
        try:
            text_ = ""
            for key in entries.keys():
                text_ += f"{key} {entries[key]}, "
            sql_text = f"CREATE TABLE IF NOT EXISTS {table} ({text_[:-2]});"
        except Exception as e:
            return self.error_handler(e)
        return self.commit_db(sql_text)

    def set_value(self, entry, value, user_id, table="users"):
        # sets a value
        self.check_if_exists(user_id)
        return self.commit_db(f'UPDATE {table} SET [{entry}]=? WHERE user_id=?;', (value, user_id))

    def command_use(self, user_id):
        # adds 1 to the total command uses - used for things like achievements
        self.check_if_exists(user_id)
        result = self.cursor.execute(f'SELECT command_uses FROM users WHERE user_id={user_id};')
        if result is None:
            self.set_value("command_uses", 1, user_id)
        else:
           return self.commit_db(f"UPDATE users SET command_uses = command_uses + 1 WHERE user_id=?;", (user_id, ))

    def check_if_exists(self, user_id):
        # checks if the user is already registered, if not it registers the user
        result = self.get_db(f"SELECT user_id FROM users WHERE user_id=?;", (user_id, )).fetchone()
        if result is None:
            self.new_user(user_id)
            return
        if result[0] is None:
            self.new_user(user_id)
            return

    @staticmethod
    def error_handler(error):
        print("An error occurred:")
        traceback.print_exception(type(error), error, error.__traceback__)
        return False


class RPGDatabase:
    def __init__(self, file="data/db15.db"):
        db = Database()
        db.create_table("monsters", {"monster_name": "text", "image": "text", "rarity": "integer",
                                     "average_lvl": "integer", "source": "text", "class": "text"})
        self.db = db.create_connection(file)
        self.cursor = self.db.cursor()
        # HEALTH_CALC = "base_health + (level // 10)"
        # DMG_CALC = "base_damage + (level // 10)"

    def get_monster(self, user_level: int):
        # creates the monster
        monster = self.best_encounter(user_level)
        level = monster[0]
        name = monster[1]
        class_ = self.get_class(name)
        image = self.get_img(name).pick
        rarity = self.get_rarity(name)
        return rpg_functions.Monster(name, level, rarity)

    def best_encounter(self, user_level: int):
        # gets the monster out of a list which would be the best to fight against
        monsters = self.all_monsters()
        monster = min(monsters, key=lambda x: abs(x[0] - user_level))
        return monster[1], self.level_gen(monster[0])

    def all_monsters(self):
        # returns a complete list of all monsters
        monsters = self.cursor.execute("SELECT average_lvl, monster_name FROM monsters")
        return monsters.fetchall()

    @staticmethod
    def level_gen(average_lvl: int):
        # calculates the level of the monsters
        return average_lvl + random.randint(-2, 3)

    def get_img(self, name):
        # returns the image of a monster
        try:
            image = self.cursor.execute("SELECT image FROM monsters WHERE name=?", (name, )).fetchone()[0]
            return image
        except Exception as e:
            print(e)
            return None

    def get_rarity(self, name):
        # returns the rarity of a monster
        try:
            rarity = self.cursor.execute("SELECT rarity FROM monsters WHERE name=?", (name, )).fetchone()[0]
            return rarity
        except Exception as e:
            print(e)
            return None

    def new_monster(self, *args):
        # creates a new monster
        try:
            self.cursor.execute("INSERT INTO monsters VALUES (?, ?, ?, ?, ?, ?)", args)
            return True
        except Exception as e:
            print(e)
            return False

    def get_class(self, *name):
        try:
            class_ = self.cursor.execute("SELECT class FROM monsters WHERE name=?", name)
            return class_
        except Exception as e:
            print(e)
            return None


class ServerDatabase(Database):
    def __init__(self, file=DATABASE_DIRECTORY):
        super(ServerDatabase, self).__init__(file)
        self.create_table("servers", {"server_id": "primary key", "prefix": "text", "join_log": "integer",
                                      "join_msg": "text", "leave_msg": "text", "bot_role": "integer",
                                      "giveaway_channel": "INTEGER", "giveaway_donations": "INTEGER",
                                      "giveaway_log": "INTEGER"})

    def new_server(self, server_id):
        # adds a new server to the database
        return self.commit_db(f"INSERT OR IGNORE INTO servers(server_id) VALUES (?);", (server_id, ))

    def get_prefix(self, server_id):
        # returns the servers prefix
        self.check_if_exists(server_id)
        result = self.get_db(f'SELECT prefix FROM servers WHERE server_id=?;', (server_id, )).fetchone()
        return result

    def check_if_exists(self, server_id):
        # checks if the server is already registered, if not it registers the servers
        result = self.get_db('SELECT * FROM servers WHERE server_id=?;', (server_id, ))
        if result is None:
            return self.new_server(server_id)
        result = result.fetchone()
        if result is None:
            self.new_server(server_id)

    def set_prefix(self, server_id, prefix):
        # changes the server prefix
        self.check_if_exists(server_id)
        return self.commit_db(f"UPDATE servers SET prefix=? WHERE server_id=?;", (prefix, server_id))

    def set_join_log(self, server_id, channel_id):
        # set the join log channel
        self.check_if_exists(server_id)
        return self.commit_db("UPDATE servers SET join_log=? WHERE server_id=?;", (channel_id, server_id))

    def get_join_log(self, server_id):
        # get the join log channel
        self.check_if_exists(server_id)
        try:
            result = self.get_db("SELECT join_log FROM servers WHERE server_id=?;", (server_id, ))
            return result.fetchone()
        except Exception as e:
            return self.error_handler(error=e)

    def set_join_msg(self, server_id, msg):
        # set a join message
        self.check_if_exists(server_id)
        return self.commit_db("UPDATE servers SET join_msg=? WHERE server_id=?;", (msg, server_id))

    def get_join_msg(self, server_id):
        # get a join message
        self.check_if_exists(server_id)
        try:
            result = self.get_db("SELECT join_msg FROM servers WHERE server_id=?;", (server_id, ))
            return result.fetchone()
        except Exception as e:
            return self.error_handler(error=e)

    def get_leave_msg(self, server_id):
        # get a leave message
        self.check_if_exists(server_id)
        try:
            result = self.get_db("SELECT leave_msg FROM servers WHERE server_id=?;", (server_id, ))
            return result.fetchone()
        except Exception as e:
            return self.error_handler(error=e)

    def set_leave_msg(self, server_id, msg):
        # set a leave message
        self.check_if_exists(server_id)
        try:
            self.get_db("UPDATE servers SET leave_msg=? WHERE server_id=?;", (msg, server_id))
            self.db.commit()
            return True
        except Exception as e:
            return self.error_handler(error=e)

    def set_bot_role(self, server_id, role_id):
        # set the bot role
        self.check_if_exists(server_id)
        return self.commit_db("UPDATE servers SET bot_role=? WHERE server_id=?;", (role_id, server_id))

    def get_bot_role(self, server_id):
        # get the bot role
        self.check_if_exists(server_id)
        try:
            result = self.get_db("SELECT bot_role FROM servers WHERE server_id=?;", (server_id, ))
            return result.fetchone()
        except Exception as e:
            return self.error_handler(error=e)

    def set_giveaway_channel(self, server_id, channel_id):
        # set the giveaway channel
        self.check_if_exists(server_id)
        return self.commit_db("UPDATE servers SET giveaway_channel=? WHERE server_id=?;", (channel_id, server_id))

    def get_giveaway_channel(self, server_id):
        # get the giveaway channel
        self.check_if_exists(server_id)
        try:
            result = self.get_db("SELECT giveaway_channel FROM servers WHERE server_id=?;", (server_id,))
            print(result)
            return result.fetchone()
        except Exception as e:
            return self.error_handler(error=e)

    def set_donation_status(self, server_id, status):
        # set if the server is currently accepting donations or not. Because of the database true/false gets changed to
        # an integer (1/0)
        status = {"disable": 0, "disabled": 0, "false": 0, "enable": 1, "enabled": 1, "true": 1}.get(status.lower(), 0)
        return self.commit_db("UPDATE servers SET giveaway_donations=? WHERE server_id=?;", (status, server_id))

    def get_donation_status(self, server_id):
        # get the servers donation status (gets changed to a boolean)
        try:
            status = self.get_db("SELECT giveaway_donations FROM servers WHERE server_id=?;", (server_id, ))
            if not status: return status
            else:
                status = status.fetchone()
                if status is None: status = 0
                return {1: True, 0: False}.get(status[0], False)
        except Exception as e:
            return self.error_handler(e)

    def set_giveaway_log(self, server_id, channel_id):
        # set the giveaway log channel
        return self.commit_db("UPDATE servers SET giveaway_log=? WHERE server_id=?;", (channel_id, server_id))

    def get_giveaway_log(self, server_id):
        # get the giveaway log channel
        try:
            result = self.get_db("SELECT giveaway_log FROM servers WHERE server_id=?;", (server_id, ))
            return result.fetchone()
        except Exception as e:
            return self.error_handler(e)


class GiveawayDatabase(Database):
    def __init__(self, file=DATABASE_DIRECTORY):
        super(GiveawayDatabase, self).__init__(file)
        self.create_table("donations", {"donator": "INTEGER", "giveaway_id": "INTEGER PRIMARY KEY",
                                        "winners": "INTEGER", "accepted_by": "INTEGER", "giveaway_text": "TEXT",
                                        "prizes": "BLOB", "donation_type": "TEXT"})

    def giveaway_donation(self, donator: int, winners: int, giveaway_text: str, prizes: [tuple, list], donation_type):
        prizes = sqlite3.Binary(pickle.dumps(prizes))
        try:
            self.commit_db("INSERT OR IGNORE INTO donations(donator, winners, giveaway_text, prizes, donation_type) "
                           "VALUES (?, ?, ?, ?, ?)", (donator, winners, giveaway_text, prizes, donation_type))
            return True, self.cursor.lastrowid
        except Exception as e:
            return self.error_handler(e)

    def get_prizes(self, giveaway_id: int):
        # gets the prize for a giveaway
        result = self.get_db("SELECT prizes FROM donations WHERE giveaway_id=?;", (giveaway_id, ))
        bprizes = result.fetchone()
        if bprizes[0] is not None:
            return pickle.loads(bprizes[0])
        else:
            return None

    def accept_giveaway(self, accepter_id: int, giveaway_id: int):
        # accepts the giveaway (mainly for logging reasons)
        try:
            self.commit_db("UPDATE donations SET accepted_by=? WHERE giveaway_id=?;", (accepter_id, giveaway_id))
            return True
        except Exception as e:
            return self.error_handler(e)

    def get_giveaway_information(self, giveaway_id: int):
        result = self.get_db("SELECT donator, winners, giveaway_text, donation_type FROM donations "
                             "WHERE giveaway_id=?;", (giveaway_id, )).fetchone()
        return result

    def update_keys(self, giveaway_id, keys):
        keys = sqlite3.Binary(pickle.dumps(keys))
        try:
            self.commit_db("UPDATE donations SET prizes=? WHERE giveaway_id=?;", (keys, giveaway_id))
        except Exception as e:
            return self.error_handler(e)