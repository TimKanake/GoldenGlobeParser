import re

class Award:
    def __init__(self, host=None, award_name=None, nominees=None, winner=None, presenters=None, potential_presenters=None):
        self.host = host
        self.award_name = award_name
        self.nominees = nominees
        self.winner = winner
        self.presenters = presenters
        self.potential_presenters = potential_presenters


    def print_award(self):
        host_string = "Hosted By: "
        award_string = "Award Name: "
        nominee_string = "Nominees: "
        winner_string = "Winner: "
        presenter_string = "Presented By: "

        try:
            host_string += self.host
        except:
            pass
        try:
            award_string += self.award_name
        except:
            pass
        try:
            for i in range(len(self.nominees)):
                if i != len(self.nominees) - 1:
                    nominee_string = nominee_string + self.nominees[i] + ", "
                else:
                    nominee_string = nominee_string + self.nominees[i] + " "
        except:
            pass
        try:
            winner_string += self.winner
        except:
            pass
        for i in range(len(self.presenters)):
            if i != len(self.presenters) - 1:
                presenter_string = presenter_string + self.presenters[i] + ", "
            else:
                presenter_string = presenter_string + self.presenters[i]

        print award_string.encode('utf-8')
        print host_string.encode('utf-8')
        print nominee_string.encode('utf-8')
        print winner_string.encode('utf-8')
        print presenter_string.encode('utf-8')
        print ""

