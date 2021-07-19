#!/usr/bin/python3

debugMessages = True

from scripts import *
import scripts

backendScripts = scripts.__all__

print("Which program do you want to run?")

for i,script in enumerate(backendScripts):
    print("{}. {}".format(str(i), script))

try:
    scriptNumber = int(input("Write a number: "))
except:
    print("It doesn't look like you entered a number.")

try:
    test = scripts[scriptNumber]
except:
    print("The number you entered doesn't correspond to a script, it should be between 1 and {}".format(len(backendScripts)))

eval("scripts.{}.main()".format(backendScripts[scriptNumber]))
