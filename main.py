#!/usr/bin/python3

debugMessages = True

from scripts import *
import scripts

backendScripts = sorted(scripts.__all__)

print("Which program do you want to run?")

for i,script in enumerate(backendScripts):
    print("{}. {}".format(str(i), script))

try:
    scriptNumber = int(input("Write a number: "))
except:
    print("It doesn't look like you entered a number.")
    exit()

try:
    backendScripts[scriptNumber]
except IndexError:
    print("The number you entered doesn't correspond to a script, it should be between 0 and {}".format(len(backendScripts) - 1))

eval("scripts.{}.main()".format(backendScripts[scriptNumber]))

