import random
TESTIMONIALS = [
    {"id":1,"text_fr":"Le but d'un trader reussi est de faire les meilleurs trades. L'argent est secondaire.","text_en":"The goal of a successful trader is to make the best trades. Money is secondary.","author":"Alexander Elder","meta":"Trading for a Living"},
    {"id":3,"text_fr":"Les elements du bon trading : (1) couper les pertes, (2) couper les pertes, (3) couper les pertes.","text_en":"The elements of good trading are: (1) cutting losses, (2) cutting losses, (3) cutting losses.","author":"Ed Seykota","meta":"Market Wizards"},
    {"id":5,"text_fr":"Discipline is the edge. Every indicator is trying to give you an edge. Discipline makes you take it.","text_en":"Discipline is the edge.","author":"ProTrader Mike","meta":"Mojo Code"},
    {"id":7,"text_fr":"Ce n'est pas d'avoir raison ou tort qui compte, mais combien tu gagnes quand tu as raison.","text_en":"It is not whether you're right or wrong, but how much you make when you are right.","author":"George Soros","meta":"Legend"},
    {"id":8,"text_fr":"Le risque vient de ne pas savoir ce que l'on fait.","text_en":"Risk comes from not knowing what you are doing.","author":"Warren Buffett","meta":"Value Investing"},
    {"id":101,"text_fr":"Ce n'est pas parce que les choses sont difficiles que nous n'osons pas ; c'est parce que nous n'osons pas qu'elles sont difficiles.","text_en":"It is not because things are difficult that we do not dare.","author":"Seneque","meta":"Stoicien"},
    {"id":102,"text_fr":"Nous sommes ce que nous repetons chaque jour. L'excellence est une habitude.","text_en":"We are what we repeatedly do. Excellence is a habit.","author":"Aristote","meta":"Ethique"},
    {"id":103,"text_fr":"La victoire appartient au plus patient.","text_en":"Victory belongs to the most patient.","author":"Sun Tzu","meta":"Art de la guerre"},
    {"id":104,"text_fr":"Tu as pouvoir sur ton esprit, pas sur les evenements.","text_en":"You have power over your mind, not outside events.","author":"Marc Aurele","meta":"Pensees"},
    {"id":107,"text_fr":"Ce que le sage fait au debut, le fou le fait a la fin.","text_en":"What the wise man does in the beginning, the fool does in the end.","author":"Daniel Kahneman","meta":"Nobel"},
    {"id":108,"text_fr":"Survivre = gerer le risque de ruine.","text_en":"Survival = managing ruin risk.","author":"Nassim Taleb","meta":"Incertitude"},
]
def get_all():
    return TESTIMONIALS
def get_random():
    return random.choice(TESTIMONIALS)
