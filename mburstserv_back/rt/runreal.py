from perlfunc import perlfunc, perlreq, perl5lib
import os

@perlfunc
@perlreq('runreal.pl')
def runreal(callsign, weight, balloon, parachute, helium):
    pass


def runreal_wrapper(*args, **kwargs):
    print(args)
    print(kwargs)
    callsign = kwargs[u"callsign"]
    weight = kwargs[u"weight"]
    balloon = kwargs[u"balloon"]
    parachute = kwargs[u"parachute"]
    helium = kwargs[u"helium"]

    print("calling runreal")
    #runreal(callsign, weight, balloon, parachute, helium)
    
    os.chdir('rt')
    os.system("perl runreal.pl -callsign={0} -weight={1} -balloon={2} -parachute={3} -helium={4}".format(callsign,                                                                       weight,                                                                         balloon,																		 parachute,																		 helium))
