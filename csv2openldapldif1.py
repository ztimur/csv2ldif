# -*- coding:utf-8 -*-
import base64
import csv
import string
import random
import codecs
import hashlib
from jinja2 import Template
from ldap3 import Server, Connection
from sets import Set


def unicode_csv_reader(utf8_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf8_data, dialect=dialect, **kwargs)
    for row in csv_reader:
        yield [unicode(cell, 'utf-8') for cell in row]


def encode(str):
    return base64.b64encode(str.encode("utf-8"))
    # return str


def get_distinguish_name(uid, org, dep):
    return u"cn={},ou={},ou={},ou=students,ou=users,dc=knu,dc=kg".format(uid, dep, org)


def get_display_name(last_name, first_name, sure_name):
    return u"{} {} {}".format(
        last_name, first_name, sure_name)


def get_ou_list():
    server = Server("ldap.knu.kg")
    conn = Connection(
        server, user="uid=ldap-user,dc=knu,dc=kg", password="q1wqgzk")
    conn.bind()
    conn.start_tls()
    result = conn.search('ou=students,ou=users,dc=knu,dc=kg',
                         '(objectClass=OrganizationalUnit)')
    result = Set()
    for entry in conn.response:
        # print u"{} {}".format(entry, entry['dn'])
        result.add(entry['dn'])
    return result


def get_student_enrollment_list():
    server = Server("ldap.knu.kg")
    conn = Connection(
        server, user="uid=ldap-user,dc=knu,dc=kg", password="q1wqgzk")
    conn.bind()
    conn.start_tls()
    result = conn.search('ou=StudentEnrollment,ou=moodle,dc=knu,dc=kg',
                         '(objectClass=posixGroup)')
    result = Set()
    for entry in conn.response:
        # print u"{} {}".format(entry, entry['dn'])
        result.add(entry['dn'])
    return result


def get_ou_distinguish_names(org, dep):
    result = []

    result.append(u"ou={},ou=students,ou=users,dc=knu,dc=kg".format(org))
    result.append(
        u"ou={},ou={},ou=students,ou=users,dc=knu,dc=kg".format(dep, org))
    return result


def main():
    print ("Csv2openldapldif started..")
    student_enrollment_list = get_student_enrollment_list()
    used_student_enrollment_list = Set()
    ou_list = get_ou_list()
    reader = unicode_csv_reader(open("students.csv"), delimiter=';')
    i = iter(reader)
    # skip csv header
    i.next()
    ou_file = codecs.open("ou.ldif", "w", encoding="utf-8")
    users_file = codecs.open("users.ldif", "w", encoding="utf-8")
    # group_enrollment_file = codecs.open(
    #     "group-enrollment.ldif", "w", encoding="utf-8")
    student_enrollment_file = codecs.open(
        "student-enrollment.ldif", "w", encoding="utf-8")
    user_template = Template(open("template-user-openldap.jinja2").read())
    ou_template = Template(open("template-ou-openldap.jinja2").read())
    create_student_enrollment_template = Template(
        open("template-student-enrollment-create-openldap.jinja2").read())
    clean_student_enrollment_template = Template(
        open("template-student-enrollment-clean-openldap.jinja2").read())
    enroll_student_template = Template(
        open("template-student-enrollment-openldap.jinja2").read())
    for row in i:
        user = {}
        uid_number = row[0]
        org = row[1]
        dep = row[2]
        last_name = row[3]
        first_name = row[4]
        sure_name = row[5]
        spec = row[6]
        kurs = row[7]
        form = row[8]
        uid = row[9]
        password = row[10]
        mail = row[11]
        spec_code = spec.split(" ")[0]
        # course = u"{}-{}-{}-{}".format(org, spec_code, kurs, form)
        course = u"{}-{}".format(org, form)
        course_dn = u'cn={},ou=StudentEnrollment,ou=moodle,dc=knu,dc=kg'.format(
            course)
        dn = get_distinguish_name(uid, org, dep)
        user["dn"] = encode(dn)
        user["organization"] = encode(org)
        user["department"] = encode(dep)
        user["sn"] = encode(last_name)
        user["givenName"] = encode(first_name)
        user["displayName"] = encode(
            get_display_name(last_name, first_name, sure_name))
        user["mail"] = mail
        user["uid"] = uid
        user["uidNumber"] = uid_number
        sha = hashlib.sha1()
        sha.update(password)
        sha_password = base64.b64encode(sha.digest())
        # print(sha_password)
        user["password"] = encode(u"{{SHA}}{}".format(sha_password))

        # print user_template.render(user)
        users_file.write("{}\n".format(user_template.render(user)))
        ou_names = get_ou_distinguish_names(org, dep)
        if ou_names[0] not in ou_list:
            print (u"{} not in LDAP. adding {}".format(org, ou_names[0]))
            ou_list.add(ou_names[0])
            ou_file.write(u"{}\n".format(ou_template.render(
                {'dn': encode(ou_names[0]), 'name': encode(org)})))

        if ou_names[1] not in ou_list:
            print (u"{} -> {} not in LDAP. adding {}".format(dep,
                                                             org, ou_names[1]))
            ou_list.add(ou_names[1])
            ou_file.write(u"{}\n".format(ou_template.render(
                {'dn': encode(ou_names[1]), 'name': encode(dep)})))

        if course_dn in student_enrollment_list and course_dn not in used_student_enrollment_list:
            student_enrollment_list.add(course_dn)
            # delete entry
            student_enrollment_file.write("{}\n-\n\n".format(clean_student_enrollment_template.render(
                {'dn': encode(course_dn)})))

        if course_dn not in used_student_enrollment_list:
            # create entry
            description = u'Срез знаний {}. {} курс ({}).'.format(
                spec, kurs, form)
            student_enrollment_file.write("{}\n".format(create_student_enrollment_template.render(
                {'dn': encode(course_dn), 'cn': encode(course), 'description': encode(description)})))

        if course_dn not in used_student_enrollment_list:
            used_student_enrollment_list.add(course_dn)

        student_enrollment_file.write("{}\n-\n\n".format(enroll_student_template.render(
            {'dn': encode(course_dn), 'uid': uid})))

    ou_file.close()
    users_file.close()
    student_enrollment_file.close()
    # group_enrollment_file.close()
    print ("Csv2ldif finished.")


if __name__ == "__main__":
    main()
