import re
import operator

class EmailScan:
    regex = re.compile(("([a-z0-9!#$%&'*+\/=?^_`{|}-~]+(?:\.[a-z0-9!#$%&'*+\/=?^_`"
                        "{|}-~]+)*(@|\sat\s)(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(\.|"
                        "\sdot\s))+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)"))

    def __init__(self,outputdir):
        self.email_dic = {}
        self.email_list = []
        self.outputdir = outputdir

    def scan_emails(self,s):
        """Add matched emails to email_dic"""
        # Removing lines that start with '//' because the regular expression
        # mistakenly matches patterns like 'http://foo@bar.com' as '//foo@bar.com'.
        filtered_emails =  [email[0] for email in re.findall(self.regex, s) if not email[0].startswith('//')]
        for email in filtered_emails:
            if email not in self.email_dic.keys():
                self.email_dic[email] = 1
            else:
                self.email_dic[email]+=1

    def output_result(self,outputdir=None):
        if not outputdir:
            outputdir = self.outputdir
        sorted_list = sorted(self.email_dic.items(), key=operator.itemgetter(1), reverse=True)
        with open(outputdir+'/email.txt',"w") as f:
            for email,count in sorted_list:
                f.write("{:<20}{}".format(count,email))
        
               
