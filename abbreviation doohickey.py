import keyboard,time,threading,json,os
from tkinter import filedialog #will be used to substitute the JSON file later

VER="3.1" #there were a lot of iterations before uploading to github ok

#JSON file setup

PATH=os.path.split(os.path.abspath(__file__))[0]
FILE=os.path.join(PATH,'abbreviations.json')
shorthands_file=open(FILE)
shorthands=json.loads(shorthands_file.read())
del shorthands['_shortcut']
shorthands_file.close()

#Setting up abbreviations from json file (please dont crucify me for editing constants, hitting ctrl+h is hard)

FUNC_LIST=shorthands['text_functions']
add_list=[]
for i in FUNC_LIST:
    add_list.append(i+'()')
FUNC_LIST+=add_list
del shorthands['text_functions']

SPACE_LIST=[]
END_LETTER_LIST=[]
ABBREVIATION_LIST=[]

for x in shorthands:
    i=shorthands[x]
    ABBREVIATION_LIST+=[x]
    if i[2]:
        SPACE_LIST+=[x]
    else:
        END_LETTER_LIST+=[x]

END_LETTERS=[]
for x in END_LETTER_LIST:
    if x[-1] not in END_LETTERS: END_LETTERS+=[x[-1]]

TOTAL_SPACE_LIST=SPACE_LIST+FUNC_LIST
TOTAL_SPACE_LIST.reverse()

longest=0
for x in ABBREVIATION_LIST:
    if len(x)>longest:longest=len(x)

class global_class: #Used to share variables between threads.
    is_on=True
    is_google_doc=False
    is_writing=False
    can_alert=True
    key_list=[]
    letter_list=[]
    spaces=-1

g=global_class

def check_on(): 
    if not g.is_on: 
        if g.can_alert: os.system('msg * Abbreviation Doohickey not enabled! Activate them with Ctrl+Shift+Q!')
        return False
    return True

def switch_alerts():
    g.can_alert=not g.can_alert

def switch_on():
    g.is_on=not g.is_on
    if g.is_on: os.system("msg * Abbreviation Doohickey activated!")
    else: os.system("msg * Abbreviation Doohickey deactivated!")

def enclose(func:str): #time.sleep() used here because it seems to break without them?
    if not check_on(): return
    keyboard.write("\\begin{"+f"{func}"+"}\n")
    time.sleep(0.16)
    keyboard.write("\n\\end{"+f"{func}"+"}")
    time.sleep(0.16)
    keyboard.send('up')
    time.sleep(0.16)
    keyboard.write('    ')

def shortcut_list(): #for help command only
    shortcuts="""Commands:
help -> Shows this message
ver -> Displays version number
switch -> Switches abbreviations on or off.
active -> Prints 'True' if LaTeX shortcuts are active
alert -> Switches inactive reminders on or off
exit -> Leaves the program

Hotkeys:
Ctrl+Shift+Q -> Switches abbreviations on or off. Identical to 'switch'
Ctrl+Shift+1 -> Auto-writes an align* section."""
    print("Press SPACE to continue.")
    for x in shortcuts.splitlines():
        print(x)
        if x=="": continue
        keyboard.wait('space')
    print('\nSupported text functions:')
    print(', '.join(FUNC_LIST))
    print('\nAbbreviations:')
    for x in ABBREVIATION_LIST:
        expansion=shorthands[x][0].replace('\n','\\n')
        left_text=f", presses left {shorthands[x][1]} time{'' if shorthands[x][1]==1 else 's'}" if shorthands[x][1]>0 else ""
        print(f"{x} -> \'{expansion}\'"+left_text+".")
        if x=="": continue
        keyboard.wait('space')
        
def text_func(function:str,has_brackets=False,sub=None,sup=None): #Subs function into \text{function} with optional \left(\right).
    left=0
    if function[-1:].isdigit(): function=function[:-1]
    keyboard.write("\\text{"+function+"}")
    if sub is not None:
        keyboard.write("_{"+str(sub)+"}")
        if sub == "": left += 1
    if sup is not None:
        keyboard.write("^{"+str(sup)+"}")
        if sup == "": left += 1
        if sub == "": left += 2
    if has_brackets:
        keyboard.write("\\left(\\right)")
        left=7
    return left

def abbreviate(x:str,has_space:bool): #Activates when an abbreviation is typed, substitutes the abbreviation with it's expansion.
    if not check_on() or g.is_writing: return
    g.is_writing=True
    left=0

    length=len(x)
    if has_space: length+=1

    for i in range (length):
        keyboard.press_and_release('backspace')
    
    if x in FUNC_LIST:
        sub=None
        sup=None
        if x[-1].isdigit(): 
            sup=x[-1]
        if len(x)>2 and x[-3].isdigit(): 
            sup=x[-3]
        if x[-2:]=="()": left=text_func(x[:-2],True,sub,sup)
        else: left=text_func(x,False,sub,sup)
    
    for i in shorthands:
        if x==i:
            keyboard.write(shorthands[i][0])
            left=shorthands[i][1]
    
    for i in range (left):
                keyboard.send('left')
    g.is_writing=False

def on_key(): #dummy function for daemon thread so the console is usable
    keyboard.on_press(append)

def append(event:keyboard.KeyboardEvent): #logs the last keys and calls word listener function on every key down
    g.key_list+=[event.name]
    if event.name == 'backspace' and len(g.letter_list)>0: del g.letter_list[-1]
    if event.name not in ['backspace','shift','space']:
        g.letter_list+=[event.name]
        g.letter_list=g.letter_list[-longest:]
    g.key_list=g.key_list[-longest:]
    listener()

def listener(): #checks for abbreviations, calls abbreviate() if abbreviation is found
    last_keys="".join(g.letter_list)
    if len(g.key_list)>0 and g.key_list[-1] in END_LETTERS:
        for x in END_LETTER_LIST:
            if len(g.key_list)>0 and last_keys.endswith(x):
                abbreviate(x,False)
                g.key_list=[]
                g.letter_list=[]
                break
    if len(g.key_list)>0 and g.key_list[-1]=='space':
        for x in TOTAL_SPACE_LIST:
            if last_keys.endswith(x):
                for i in range (g.spaces):
                    keyboard.send('backspace')
                abbreviate(x,True)
                g.key_list=[]
                g.letter_list=[]
                break
        g.spaces=0
        g.key_list=[]

#todo: allow hotkeys to be configured in the JSON file
keyboard.add_hotkey('ctrl+shift+q',switch_on)
keyboard.add_hotkey('ctrl+shift+1',lambda:enclose('align*'))
keyboard.add_hotkey('ctrl+shift+2',lambda:enclose('itemize'))

thread=threading.Thread(target=on_key,daemon=True)
thread.start()

#Basic console, can be subbed for tkinter interface probably. This works fine though.
print(f"Abbreviation Doohickey v{VER} now active!")
print("Find it on GitHub at https://github.com/redstone59/abbreviation-doohickey")
print("Type 'exit' to leave, 'help' for a list of abbrevations, commands, and hotkeys.")
while True:
    p=input(">>> ")
    if p=="exit": break
    if p=="help": shortcut_list()
    if p=="ver": print(f'Current version: Abbreviation Doohickey v{VER}')
    if p=="switch": print(switch_on())
    if p=="active" or p=="on": print(check_on())
    if p=="alert": switch_alerts(); print(g.can_alert)
    if p=="repo" or p=="github": print("https://github.com/redstone59/abbreviation-doohickey")
print("bai bai :3") #i gotta put a :3 somewhere ok
