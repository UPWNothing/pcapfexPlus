import re

class EmailScan:
    regex = re.compile(("([a-z0-9!#$%&'*+\/=?^_`{|}-~]+(?:\.[a-z0-9!#$%&'*+\/=?^_`"
                        "{|}-~]+)*(@|\sat\s)(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(\.|"
                        "\sdot\s))+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)"))

    def __init__(self):
        self.emaildic = {}
        self.emaillist = []
