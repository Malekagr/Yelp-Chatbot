# coding: utf-8
import ast

# Table names in query must be surrounded by double quotation marks "TABLE_NAME"
class AccessVotes(object):
    def __init__(self, channel_id, conn):
        self._channel = str(channel_id)
        self._conn = conn
        self._cur = self._conn.cursor()
        self._insert_query = '''
        INSERT INTO "Votes_Info"(votes_channel, user_votes, votes_timestamp, msg_attachments)
        VALUES (%s, %s, %s, %s)
        '''
        self._delete_query = '''DELETE FROM "Votes_Info" WHERE votes_channel = %s'''

        self._update_row_values()
        self._update_existing_channel_list()

        self._user_votes_pos = 1
        self._votes_timestamp_pos = 2
        self._msg_attachments_pos = 4

    def _update_row_values(self):
        self._cur.execute('''SELECT * FROM "Votes_Info" WHERE votes_channel = %s''', (self._channel,))
        self._values = self._cur.fetchall()

    def _update_existing_channel_list(self):
        self._cur.execute('''SELECT votes_channel FROM "Votes_Info"''')
        self._existing_channel_names = self._cur.fetchall()
        self._existing_channel_names = list(c[0] for c in self._existing_channel_names)

    def create_votes_info(self, ts, msg_attachments):
        if self._channel not in self._existing_channel_names:
            try:
                self._cur.execute(self._insert_query, (self._channel, "{}", str(ts), str(msg_attachments)))
                self._conn.commit()
                self._update_row_values()
                self._update_existing_channel_list()
            except:
                self._conn.rollback()
        else:
            # set new values
            self.set_msg_attachments(msg_attachments)
            self.set_votes_ts(ts)
            #print("channel name already exists", "updated ts:", ts, "\nmsg_attachments", msg_attachments)

    def set_msg_attachments(self, msg_attachments):
        if self._values:
            # if the list is not empty, i.e. row exists
            self._cur.execute('''UPDATE "Votes_Info" SET "msg_attachments" = %s WHERE votes_channel = %s''' , (str(msg_attachments), self._channel))
            self._conn.commit()
            self._update_row_values()

    def get_msg_attachments(self):
        if self._values:
            return ast.literal_eval(self._values[0][self._msg_attachments_pos])
        else:
            return ""

    def set_votes_ts(self, votes_timestamp):
        if self._values:
            # if the list is not empty, i.e. row exists
            self._cur.execute('''UPDATE "Votes_Info" SET "votes_timestamp" = %s WHERE votes_channel = %s''' , (str(votes_timestamp), self._channel))
            self._conn.commit()
            self._update_row_values()

    def get_votes_ts(self):
        if self._values:
            # if timestamp has trailing values like
            # 1523317315.000010, if pass this to ts to delete
            # as a float, it would end up like 1523317315.00001
            # which is an incorrect timestamp
            # so only pass to it as a string
            return str(self._values[0][self._votes_timestamp_pos]) 
        else:
            return -1

    def set_user_votes(self, user_id, user_selection):
        if self._values:
            # change the votes only if the row exists
            votes = ast.literal_eval(self._values[0][self._user_votes_pos])
            votes[user_id] = user_selection
            self._cur.execute('''UPDATE "Votes_Info" SET "user_votes" = %s WHERE votes_channel = %s''', (str(votes), self._channel, ))
            self._conn.commit()
            self._update_row_values()

    def get_user_votes(self):
        if self._values:
            #print("Success")
            return ast.literal_eval(self._values[0][self._user_votes_pos])
        else:
            #print("Failed")
            return {}

    def reset_user_votes(self):
        if self._values:
            self._cur.execute('''UPDATE "Votes_Info" SET "user_votes" = %s WHERE votes_channel = %s''', (str({}), self._channel, ))
            self._conn.commit()
            self._update_row_values()

    def delete(self):
        if self._values:
            self._cur.execute(self._delete_query, (self._channel,))
            self._conn.commit()
            self._update_row_values()
            self._update_existing_channel_list()

class AccessInvoker(object):
    def __init__(self, channel_id, conn):
        self._channel = str(channel_id)
        self._conn = conn
        self._cur = self._conn.cursor()
        self._insert_query = '''
        INSERT INTO "invoker__info"(invoked_channel, invoker_id, invoked_ts)
        VALUES (%s, %s, %s)
        '''
        self._delete_query = '''DELETE FROM "invoker__info" WHERE invoked_channel = %s'''

        self._update_row_values()
        self._update_existing_channel_list()

        self._invoker_id_pos = 1
        self._invoked_ts_pos = 3

    def _update_row_values(self):
        self._cur.execute('''SELECT * FROM "invoker__info" WHERE invoked_channel = %s''', (self._channel,))
        self._values = self._cur.fetchall()

    def _update_existing_channel_list(self):
        self._cur.execute('''SELECT invoked_channel FROM "invoker__info"''')
        self._existing_channel_names = self._cur.fetchall()
        self._existing_channel_names = list(c[0] for c in self._existing_channel_names)

    def create_invoker_info(self, invoker_id, invoked_ts):
        if self._channel not in self._existing_channel_names:
            try:
                self._cur.execute(self._insert_query, (self._channel, str(invoker_id), str(invoked_ts)))
                self._conn.commit()
                self._update_row_values()
                self._update_existing_channel_list()
            except:
                self._conn.rollback()
        else:
            self.set_invoker_id(invoker_id)
            self.set_invoker_ts(invoked_ts)
            #print("channel name already exists")

    def set_invoker_id(self, invoker_id):
        if self._values:
            self._cur.execute('''UPDATE "invoker__info" SET "invoker_id" = %s WHERE invoked_channel = %s''', (str(invoker_id), self._channel, ))
            self._conn.commit()
            self._update_row_values()

    def set_invoker_ts(self, invoked_ts):
        if self._values:
            self._cur.execute('''UPDATE "invoker__info" SET "invoked_ts" = %s WHERE invoked_channel = %s''', (str(invoked_ts), self._channel, ))
            self._conn.commit()
            self._update_row_values()

    def get_invoker_id(self):
        if self._values:
            return self._values[0][self._invoker_id_pos]
        else:
            return "None"

    def get_invoker_ts(self):
        if self._values:
            return self._values[0][self._invoked_ts_pos]
        else:
            return -1

    def delete(self):
        if self._values:
            self._cur.execute(self._delete_query, (self._channel,))
            self._conn.commit()
            self._update_row_values()
            self._update_existing_channel_list()

class AccessBusinessIDs(object):
    def __init__(self, channel_id, conn):
        self._channel = str(channel_id)
        self._conn = conn
        self._cur = self._conn.cursor()
        self._insert_query = '''
        INSERT INTO "Business_IDs"(bid_channel, business_ids)
        VALUES (%s, %s)
        '''
        self._delete_query = '''DELETE FROM "Business_IDs" WHERE bid_channel = %s'''

        self._update_row_values()
        self._update_existing_channel_list()

        self._business_ids_pos = 2

    def _update_row_values(self):
        self._cur.execute('''SELECT * FROM "Business_IDs" WHERE bid_channel = %s''', (self._channel,))
        self._values = self._cur.fetchall()

    def _update_existing_channel_list(self):
        self._cur.execute('''SELECT bid_channel FROM "Business_IDs"''')
        self._existing_channel_names = self._cur.fetchall()
        self._existing_channel_names = list(c[0] for c in self._existing_channel_names)

    def create_business_ids(self, business_ids):
        if self._channel not in self._existing_channel_names:
            try:
                self._cur.execute(self._insert_query, (self._channel, str(business_ids)))
                self._conn.commit()
                self._update_row_values()
                self._update_existing_channel_list()
            except:
                self._conn.rollback()
        else:
            self.set_business_ids(business_ids)
            #print("channel name already exists")

    def set_business_ids(self, business_ids):
        if self._values:
            self._cur.execute('''UPDATE "Business_IDs" SET "business_ids" = %s WHERE bid_channel = %s''', (str(business_ids), self._channel, ))
            self._conn.commit()
            self._update_row_values()

    def get_business_ids(self):
        if self._values:
            return ast.literal_eval(self._values[0][self._business_ids_pos])
        else:
            return []

    def delete(self):
        if self._values:
            self._cur.execute(self._delete_query, (self._channel,))
            self._conn.commit()
            self._update_row_values()
            self._update_existing_channel_list()

class AccessGeneral(object):
    def __init__(self, channel_id, conn):
        self._channel = str(channel_id)
        self._conn = conn
        self._cur = self._conn.cursor()
        self._insert_query = '''
        INSERT INTO "General"(channel_id, message_ts)
        VALUES (%s, %s)
        '''
        self._delete_query = '''DELETE FROM "General" WHERE channel_id = %s'''

        self._update_row_values()
        self._update_existing_channel_list()

        self._message_ts_pos = 2

    def _update_row_values(self):
        self._cur.execute('''SELECT * FROM "General" WHERE channel_id = %s''', (self._channel,))
        self._values = self._cur.fetchall()

    def _update_existing_channel_list(self):
        self._cur.execute('''SELECT channel_id FROM "General"''')
        self._existing_channel_names = self._cur.fetchall()
        self._existing_channel_names = list(c[0] for c in self._existing_channel_names)

    def create_general_info(self, message_ts):
        if self._channel not in self._existing_channel_names:
            try:
                self._cur.execute(self._insert_query, (self._channel, str(message_ts)))
                self._conn.commit()
                self._update_row_values()
                self._update_existing_channel_list()
            except:
                self._conn.rollback()
        else:
            self.set_ts(message_ts)
            #print("channel name already exists")

    def set_ts(self, message_ts):
        if self._values:
            self._cur.execute('''UPDATE "General" SET "message_ts" = %s WHERE channel_id = %s''', (str(message_ts), self._channel, ))
            self._conn.commit()
            self._update_row_values()

    def get_ts(self):
        if self._values:
            return float(self._values[0][self._message_ts_pos])
        else:
            return -1

    def delete(self):
        if self._values:
            self._cur.execute(self._delete_query, (self._channel,))
            self._conn.commit()
            self._update_row_values()
            self._update_existing_channel_list()

    def validate_timestamp(self, cur_ts):
        cur_ts = float(cur_ts)
        past = float(self.get_ts())
        print('PAST:', past,'CURRENT:',cur_ts)
        if int(cur_ts) < int(past):
            return False
        return True

class AccessPoll(object):
    def __init__(self, channel_id, conn):
        self._channel = str(channel_id)
        self._conn = conn
        self._cur = self._conn.cursor()
        self._insert_query = '''
        INSERT INTO "Poll_Info"(poll_channel, terms, locations)
        VALUES (%s, %s, %s)
        '''
        self._delete_query = '''DELETE FROM "Poll_Info" WHERE poll_channel = %s'''

        self._update_row_values()
        self._update_existing_channel_list()

        self._terms_pos = 2
        self._locations_pos = 3

    def _update_row_values(self):
        self._cur.execute('''SELECT * FROM "Poll_Info" WHERE poll_channel = %s''', (self._channel,))
        self._values = self._cur.fetchall()

    def _update_existing_channel_list(self):
        self._cur.execute('''SELECT poll_channel FROM "Poll_Info"''')
        self._existing_channel_names = self._cur.fetchall()
        self._existing_channel_names = list(c[0] for c in self._existing_channel_names)

    def create_poll_info(self, terms="", locations=""):
        if self._channel not in self._existing_channel_names:
            self._cur.execute(self._insert_query, (self._channel, str(terms), str(locations)))
            self._conn.commit()
            self._update_row_values()
            self._update_existing_channel_list()
        else:
            self.set_terms(terms)
            self.set_locations(locations)
            #print("channel name already exists")

    def set_terms(self, terms=""):
        if not terms.rstrip():
            return
        if self._values:
            # if the list is not empty, i.e. row exists
            self._cur.execute('''UPDATE "Poll_Info" SET "terms" = %s WHERE "poll_channel" = %s''' , (str(terms), self._channel))
            self._conn.commit()
            self._update_row_values()

    def get_terms(self):
        if self._values:
            return self._values[0][self._terms_pos]
        else:
            return ""

    def set_locations(self, locations=""):
        if not locations.rstrip():
            return
        if self._values:
            # if the list is not empty, i.e. row exists
            self._cur.execute('''UPDATE "Poll_Info" SET "locations" = %s WHERE "poll_channel" = %s''' , (str(locations), self._channel))
            self._conn.commit()
            self._update_row_values()

    def get_locations(self):
        if self._values:
            return self._values[0][self._locations_pos]
        else:
            return ""

    def delete(self):
        if self._values:
            self._cur.execute(self._delete_query, (self._channel,))
            self._conn.commit()
            self._update_row_values()
            self._update_existing_channel_list()
