from datetime import datetime


def get_streak_days(user):
    return (datetime.utcnow() - user.streak_start).days

def reset_counter(user):
    user.streak_start = datetime.now()
    

