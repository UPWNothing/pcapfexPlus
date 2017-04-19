import operator

class DomainScan:
    
    def __init__(self):
        self.domain_dict = {}

    def add_domain(self,domain):
        if domain in self.domain_dict.keys():
            self.domain_dict[domain] += 1
        else:
            self.domain_dict[domain] = 1

    def output_result(self,outputdir):
        
        sorted_list = sorted(self.domain_dict.items(), key=operator.itemgetter(1), reverse=True)
        with open(outputdir+'/domain.txt',"w") as f:
            f.write("{:<20}\tDomains:\n".format('Num:'))
            f.write("="*20+"\t"+"="*20+'\n')
            for domain,count in sorted_list:
                f.write("{:<20}\t{}\n".format(count,domain))
