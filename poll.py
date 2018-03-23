import random
import html

class Poll(object):
    def __init__(self, message={}, user_votes={}):
        self._slack_msg = message # the return value of slack_format.build_vote_message
        self._user_votes = user_votes # key=user id, value=button value, a cached value in the flask app
        self._votes = {} # key=restaurant name (the value of the button), value=total votes for the restaurant as integer
        
        self._calculate_votes()
        self._update_attachments()
    
    def _calculate_votes(self):
        for res_name in self._user_votes.values():
            if res_name in self._votes:
                self._votes[res_name] += 1
            else:
                self._votes[res_name] = 1
    
    def _update_attachments(self):
-        displayed_res_names = []
-        actual_stored_names = []
         if "attachments" in self._slack_msg:
             for att in self._slack_msg["attachments"]:
-                restaurant_name = att["actions"][0]["value"]
-                displayed_res_names.append(restaurant_name)
-                if restaurant_name in self._votes:
-                    att["fields"][2]["value"] = self._votes.get(restaurant_name)
-                elif restaurant_name.replace("&", "&amp;") in self._votes:
-                    att["fields"][2]["value"] = self._votes.get(restaurant_name.replace("&", "&amp;"))
-                else:
-                    att["fields"][2]["value"] = 0
-                    
-        print("displayed_res_names:",displayed_res_names,"\nactual_stored_names:", self._votes.keys())             
    
    def get_updated_attachments(self):
        return self._slack_msg
    
    def get_votes(self):
        return self._votes
    
    @staticmethod
    def get_restaurant_votes(user_votes={}):
        if len(user_votes) == 0:
            return {}
        votes = {}
        for res_name in user_votes.values():
            if res_name in votes:
                votes[res_name] += 1
            else:
                votes[res_name] = 1
        return votes
    
    @staticmethod
    def get_probabilities(user_votes={}):
        votes = Poll.get_restaurant_votes(user_votes)
        total = sum(votes.values())
        for k, v in votes.items():
            votes[k] = round(v * 1.0 / total, 2)
        return votes
    
    @staticmethod
    def get_winner(user_votes={}):
        restaurant_votes = Poll.get_restaurant_votes(user_votes)
        winners = [k for k in restaurant_votes.keys() if restaurant_votes[k] == max(restaurant_votes.values())]
        random.shuffle(winners)
        r = random.randint(0, len(winners)-1)
        return winners[r]
    
    @staticmethod
    def spin_roulette(user_votes={}):
        restaurant_votes = Poll.get_restaurant_votes(user_votes)
        candidates = [[k]*restaurant_votes[k] for k in restaurant_votes.keys() if restaurant_votes[k] > 0]
        if len(candidates) == 0:
            return "No one voted!"
        candidates = [item for sublist in candidates for item in sublist] # flatten the list of lists
        random.shuffle(candidates)
        r = random.randint(0, len(candidates)-1)
        return candidates[r]
    
class Finalize(object):    
    @staticmethod
    def conclude(user_votes={}):
        if len(user_votes) == 0:
            return "No one voted!"
        probs = Poll.get_probabilities(user_votes)
        winner = Poll.get_winner(user_votes)
        s = ""
        for k,v in probs.items():
            s += "{0} has probability of {1}% to be chosen\n".format(k, v*100)
        return s+"""The Chosen restaurant is: {0}""".format(winner)

    
class ReRoll(object):
    def __init__(self, list_of_ids):
        self._id_list = list_of_ids
    
    def shuffle(self):
        random.shuffle(self._id_list)
        
    def _get_rolls(self):
        self.shuffle()
        new_rolls = []
        if len(self._id_list) >= 3:
            new_rolls = self._id_list[0:3]
            self._id_list = self._id_list[3:]
        else:
            new_rolls = self._id_list
            self._id_list = []
        return new_rolls
    def _get_updated_list(self):
        return self._id_list
    
    def reroll(self):
        return self._get_rolls(), self._get_updated_list()
