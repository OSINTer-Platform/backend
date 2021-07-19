#!/usr/bin/python3

debugMessages = True

from Scripts import *
import Scripts

scripts = Scripts.__all__

print("Which program do you want to run?")

for i,script in enumerate(scripts):
    print("{}. {}".format(str(i), script))

try:
    scriptNumber = int(input("Write a number: "))
except:
    print("It doesn't look like you entered a number.")

try:
    test = scripts[scriptNumber]
except:
    print("The number you entered doesn't correspond to a script, it should be between 1 and {}".format(len(scripts)))

eval("Scripts.{}.main()".format(scripts[scriptNumber]))
