
# coding: utf-8

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
        if "attachments" in self._slack_msg:
            for att in self._slack_msg["attachments"]:
                restaurant_name = att["actions"][0]["value"]
                att["fields"][2]["value"] += self._votes.get(restaurant_name) if restaurant_name in self._votes else 0
    
    def get_updated_attachments(self):
        return self._slack_msg
    
    def get_votes(self):
        return self._votes
    
    @staticmethod
    def get_winner(user_votes={}):
        winners = [k for k in user_votes.keys() if user_votes[k] == max(user_votes.values())]
        r = random.randint(0, len(winners)-1)
        return winners[r]
    
    @staticmethod
    def spin_roulette(user_votes={}):
        candidates = [[k]*user_votes[k] for k in user_votes.keys() if user_votes[k] > 0]
        if len(candidates) == 0:
            return "No one voted!"
        candidates = [item for sublist in candidates for item in sublist] # flatten the list of lists
        r = random.randint(0, len(candidates)-1)
        return candidates[r]
