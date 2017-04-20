import operator
import json
try:
    import simplekml
    from requests import get
    ENABLE_KML = True
except:
    ENABLE_KML = False
    print "[Warning] KML file generation DISABLED. Install simplekml and package to enable this function."

class IPScan:

    def __init__(self):
        self.ip_dict = {}
        if ENABLE_KML:
            self.kml = simplekml.Kml()

    def add_ip(self,ip):
        if ip in self.ip_dict.keys():
            self.ip_dict[ip] += 1
        else:
            self.ip_dict[ip] = 1

    def output_result(self,outputdir):
        sorted_list = sorted(self.ip_dict.items(), key=operator.itemgetter(1), reverse=True)
        with open(outputdir+'/ip.txt',"w") as f:
            f.write("{:<20}\tIP:\n".format('Num:'))
            f.write("="*20+"\t"+"="*20+'\n')
            for ip,count in sorted_list:
                f.write("{:<20}\t{}\n".format(count,ip))
        if ENABLE_KML:
            self.generate_kml(outputdir+'/geo.kml')

    def generate_kml(self,outputdir):
        for ip in self.ip_dict.keys():
            geo = self.get_geo(ip)
            if geo:
                self.kml.newpoint(name=ip, coords=[(geo['longitude'],geo['latitude'])])
        self.kml.save(outputdir)

    def get_geo(self,ip):
        '''
        retrive host's geolocation using http://freegeoip.net API    
        Use after get_ip()

        result is stored as JSON in self.geo_json

        '''
        # send request
        try:
            url = 'http://freegeoip.net/json/{}'.format(ip)
            res = get(url)
            return res.json()
        except:
            print "[*] Failed to get Geolocation of {}({})".format(url,ip)
            return None
