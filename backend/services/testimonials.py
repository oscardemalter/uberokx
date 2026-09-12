import random

TESTIMONIALS = [
    {"id":1,"text_fr":"Le but d'un trader reussi est de faire les meilleurs trades. L'argent est secondaire.","text_en":"The goal of a successful trader is to make the best trades. Money is secondary.","author":"Alexander Elder","meta":"Trading for a Living"},
    {"id":3,"text_fr":"Les elements du bon trading : (1) couper les pertes, (2) couper les pertes, (3) couper les pertes.","text_en":"The elements of good trading are: (1) cutting losses, (2) cutting losses, (3) cutting losses.","author":"Ed Seykota","meta":"Market Wizards"},
    {"id":5,"text_fr":"Discipline is the edge. Every indicator is trying to give you an edge. Discipline makes you take it.","text_en":"Discipline is the edge.","author":"ProTrader Mike","meta":"Mojo Code"},
    {"id":7,"text_fr":"Ce n'est pas d'avoir raison ou tort qui compte, mais combien tu gagnes quand tu as raison.","text_en":"It is not whether you're right or wrong, but how much you make when you are right.","author":"George Soros","meta":"Legend"},
    {"id":8,"text_fr":"Le risque vient de ne pas savoir ce que l'on fait.","text_en":"Risk comes from not knowing what you are doing.","author":"Warren Buffett","meta":"Value Investing"},
]

def get_all():
    """Retourne tous les témoignages"""
    return TESTIMONIALS

def get_random():
    """Retourne un témoignage aléatoire"""
    return random.choice(TESTIMONIALS)

def get_random_testimonial():
    """Alias de get_random pour compatibilité"""
    return get_random()
