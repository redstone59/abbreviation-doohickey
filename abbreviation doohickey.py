VER="3.2"
import keyboard,time,threading,json,os,requests
import tkinter as tk #JSON substition done, just need an editor now, although this might be slow now.
from tkinter import filedialog
from tkinter import messagebox

PATH=os.path.split(os.path.abspath(__file__))[0]

#update checking

update_available=True
try:
    #checking the first 9 characters of line 4, probably a far better way to do this but who knows!
    with requests.Session() as s:
        p = s.get('https://raw.githubusercontent.com/redstone59/abbreviation-doohickey/main/abbreviation%20doohickey.py')
        web_ver = p.text.splitlines()[0]
        if web_ver==f'VER="{VER}"': update_available=False
except:
    print('Unable to check for updates.')
    update_available=False

#JSON file setup, called for the most recent file near the end.

def open_json_abbreviations(directory):
    with open(directory) as shorthands_file:
        g.shorthands=json.loads(shorthands_file.read())
        try:
            del g.shorthands['_shortcut']
        except NameError:
            pass

    #Setting up abbreviations from json file (please dont crucify me for editing constants, hitting ctrl+h is hard)

    g.func_list=g.shorthands['text_functions']
    add_list=[]
    for i in g.func_list:
        add_list.append(i+'()')
    g.func_list+=add_list
    del g.shorthands['text_functions']

    for x in g.shorthands:
        i=g.shorthands[x]
        g.abbreviation_list+=[x]
        if i[2]:
            g.space_list+=[x]
        else:
            g.end_letter_list+=[x]

    for x in g.end_letter_list:
        if x[-1] not in g.end_letters: g.end_letters+=[x[-1]]

    g.total_space_list=g.space_list+g.func_list
    g.total_space_list.reverse() #prevents clashes with similar shortcuts if placed in order ('sect','ssect','sssect')

    g.longest=0
    for x in g.abbreviation_list:
        if len(x)>g.longest: g.longest=len(x)

class global_class: #Used to share variables between threads. If there's a better way to do this, please inform me!
    is_on=True
    is_google_doc=False
    is_writing=False
    can_alert=True
    key_list=[]
    letter_list=[]
    spaces=-1
    
    #JSON file stuffs
    shorthands={}
    func_list=[]
    space_list=[]
    total_space_list=[]
    end_letters=[]
    end_letter_list=[]
    abbreviation_list=[]
    longest=0
    
    #tkinter queue
    tk_queue=[]
    
    #ini stuff
    recent=""

g=global_class

#check for doohickey.ini, create if not there

with open(os.path.join(PATH,'doohickey.ini'),"w+") as f:
    if f.read() == "":
        f.write(f"""[recent_files]

recent1={os.path.join(PATH,"abbreviations.json")}
recent2=
recent3=
recent4=
recent5=""")
        g.recent=os.path.join(PATH,"abbreviations.json")
    else:
        most_recent_file=f.readlines()[2][8:]
        default_file=False
        try:
            open(most_recent_file)
            default_file=False
        except:
            default_file=True
        if not default_file:
            g.recent=most_recent_file
        else:
            g.recent=os.path.join(PATH,"abbreviations.json")

def check_on(): 
    if not g.is_on: 
        if g.can_alert: g.tk_queue+=[('error',["Not active!","Abbreviation Doohickey is not active!\nActivate it with Ctrl+Shift+Q, or alternatively turn off this message with 'alert' in the console."])]
        return False
    return True

def switch_alerts():
    g.can_alert=not g.can_alert
    return g.can_alert

def switch_on():
    g.is_on=not g.is_on
    if g.is_on: g.tk_queue+=[('info',["Activated!","Abbreviation Doohickey activated!"])]
    else: g.tk_queue+=[('info',["Deactivated!","Abbreviation Doohickey deactivated!"])]
    return g.is_on

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
repo -> Sends the link to the GitHub repo
load -> Opens a new .json file for abbreviations
file -> Prints the open file
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
    print(', '.join(g.func_list))
    print('\nAbbreviations:')
    for x in g.abbreviation_list:
        expansion=g.shorthands[x][0].replace('\n','\\n')
        left_text=f", presses left {g.shorthands[x][1]} time{'' if g.shorthands[x][1]==1 else 's'}" if g.shorthands[x][1]>0 else ""
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
    
    if x in g.func_list:
        sub=None
        sup=None
        if x[-1].isdigit(): 
            sup=x[-1]
        if len(x)>2 and x[-3].isdigit(): 
            sup=x[-3]
        if x[-2:]=="()": left=text_func(x[:-2],True,sub,sup)
        else: left=text_func(x,False,sub,sup)
    
    for i in g.shorthands:
        if x==i:
            keyboard.write(g.shorthands[i][0])
            left=g.shorthands[i][1]
    
    for i in range (left):
                keyboard.send('left')
    g.is_writing=False

def on_key(): #dummy function for daemon thread so the console is usable
    keyboard.on_press(append)

def append(event:keyboard.KeyboardEvent): #logs the last keys and calls word listener function on every key down
    g.key_list+=[event.name]
    if event.name == 'backspace' and len(g.letter_list)>0: del g.letter_list[-1]
    if event.name not in ['backspace','shift','space',None]:
        g.letter_list+=[event.name]
        g.letter_list=g.letter_list[-g.longest:]
    g.key_list=g.key_list[-g.longest:]
    listener()

def listener(): #checks for abbreviations, calls abbreviate() if abbreviation is found
    last_keys="".join(g.letter_list)
    if len(g.key_list)>0 and g.key_list[-1] in g.end_letters:
        for x in g.end_letter_list:
            if len(g.key_list)>0 and last_keys.endswith(x):
                abbreviate(x,False)
                g.key_list=[]
                g.letter_list=[]
                break
    if len(g.key_list)>0 and g.key_list[-1]=='space':
        for x in g.total_space_list:
            if last_keys.endswith(x):
                for i in range (g.spaces):
                    keyboard.send('backspace')
                abbreviate(x,True)
                g.key_list=[]
                g.letter_list=[]
                break
        g.spaces=0
        g.key_list=[]

#tkinter window setup so notifications appear on top and allow for file switching

def gui_function():   
    while True:
        if g.tk_queue != []:
            tk_master=tk.Tk() #master window, all other tk widgets will depend on this window
            tk_master.attributes("-topmost",True)
            tk_master.withdraw()
            
            command=g.tk_queue[0][0]
            args=g.tk_queue[0][1]
            match command:
                case "error":
                    if len(args) != 2: break
                    messagebox.showerror(args[0],args[1])
                case "info":
                    if len(args) != 2: break
                    messagebox.showinfo(args[0],args[1])
                case "load_file":
                    ini_file=os.path.join(PATH,'doohickey.ini')
                    file=filedialog.askopenfile(initialdir=PATH)
                    if file.name[-5:] != ".json": break
                    with open(ini_file,"r") as f:
                        recent_file_list=[file.name]
                        file_lines=f.read().split('\n')
                        for x in range (4):
                            recent_file_list+=[file_lines[2+x][8:]]
                            file_lines[2+x]=f"recent{x+1}={recent_file_list[x]}"
                    with open(ini_file,"w") as f:
                        for x in file_lines:
                            f.write(str(x)+'\n')
                    open_json_abbreviations(file.name)
                    g.recent=file.name
                    messagebox.showinfo('Loaded!',f'Loaded file {os.path.split(file.name)[1]}!')
            del g.tk_queue[0]
            tk_master.destroy()

#actually starting the damn thing

open_json_abbreviations(g.recent)

#todo: allow hotkeys to be configured in the JSON file
keyboard.add_hotkey('ctrl+shift+q',switch_on)
keyboard.add_hotkey('ctrl+shift+1',lambda:enclose('align*'))
keyboard.add_hotkey('ctrl+shift+2',lambda:enclose('itemize'))

thread=threading.Thread(target=on_key,daemon=True)
thread.start()

gui_thread=threading.Thread(target=gui_function,daemon=True)
gui_thread.start()

#Basic console, can be subbed for tkinter interface probably. This works fine though.
print(f"Abbreviation Doohickey v{VER} now active!")
if update_available: print("There is an update available! Download it at https://github.com/redstone59/abbreviation-doohickey")
else: print("Find it on GitHub at https://github.com/redstone59/abbreviation-doohickey")
print("Type 'exit' to leave, 'help' for a list of abbrevations, commands, and hotkeys.")
while True:
    p=input(">>> ")
    if p=="exit": break
    if p=="help": shortcut_list()
    if p=="ver": print(f'Current version: Abbreviation Doohickey v{VER}')
    if p=="switch": print(switch_on())
    if p=="active" or p=="on": print(check_on())
    if p=="alert": print(switch_alerts())
    if p=="repo" or p=="github": print("https://github.com/redstone59/abbreviation-doohickey")
    if p=="load": g.tk_queue+=[('load_file',None)]
    if p=="file": print(g.recent)
print("bai bai :3") #i gotta put a :3 somewhere ok
