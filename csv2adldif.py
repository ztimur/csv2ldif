# -*- coding:utf-8 -*-
import base64
import csv
import string
import random
from jinja2 import Template
from transliterate import translit, get_available_language_codes


def random_password():
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    size = random.randint(8, 8)
    return ''.join(random.choice(chars) for x in range(size))


def unicode_csv_reader(utf8_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf8_data, dialect=dialect, **kwargs)
    for row in csv_reader:
        yield [unicode(cell, 'utf-8') for cell in row]


def get_uid(last_name, first_name):
    s = u'{}{}'.format(first_name[0], last_name).lower()
    print type(s)
    print s.replace(
        '\xd3', 'о').replace('\xd0', 'н')  # .replace('ү', 'у')
    return translit(s, 'ru', reversed=True).lower()


def get_common_name(last_name, first_name, sure_name):
    return u"{}{}{}".format(first_name, ' ' if not sure_name else ' ' + sure_name[0] + '. ', last_name)


def encode(str):
    # return base64.b64encode(str.encode("utf-16le"))
    return str


def main():
    print "Csv2ldif started.."
    print get_available_language_codes()
    reader = unicode_csv_reader(open("users.csv"), delimiter=';')
    i = iter(reader)
    # skip csv header
    i.next()
    for row in i:
        user = {}
        org = row[0]
        dep = row[1]
        last_name = row[2]
        first_name = row[3]
        sure_name = row[4]
        password = random_password()
        uid = get_uid(last_name, first_name)
        cn = get_common_name(last_name, first_name, sure_name)
        dn_str = u"CN={},OU={},OU={},OU=Пользователи,DC=edu,dc=knu,dc=kg".format(
            cn, org, dep)
        user["cn"] = encode(cn)
        user["dn"] = encode(dn_str)
        user["sn"] = encode(last_name)
        user["givenName"] = encode(first_name)
        user["displayName"] = encode(u"{} {} {}".format(
            last_name, first_name, sure_name))
        user["name"] = encode("user_name")
        user["uid"] = uid
        user["unicodePwd"] = encode(password)
        template = Template(open("template.jinja2").read())
        print template.render(user)
    print "Csv2ldif finished."


if __name__ == "__main__":
    main()
