import csv
import json
import sys, getopt
import datetime
import time
import re
from pathlib import Path
from functools import partial

debug = False
integer_stack = []
jump_flag = False
compile_flag = False

isp = 0

latest = None
linked_dict = [] #each entry will be a dict

entry_example = {
    "link" : None, #or latest
    "name" : "NEXT",
    "flags" : 0,
    "code" : [] #of pointer to function, the first is DOCOL, and the last is NEXT
}

#i need a little struct to hold the link or code of a word
{
    "ptr" : None,
    "f": None
}

def enter_compilation():
    global compile_flag
    compile_flag = True    

def check_elements_on_stack(stack, size):
    return len(stack) > size -1

def add():
    if len(integer_stack) > 1:
        num1 = integer_stack.pop() 
        num2 = integer_stack.pop()
        if num1 == None or num2 == None:
            print("None")
        integer_stack.append(num1 + num2)
        return 0
    print("error not enough elements")
    return -1

def emit():
    global integer_stack
    if len(integer_stack) > 0:
        num1 = integer_stack.pop() 
        print(num1)
        return 0
    print(integer_stack)
    return 0

def print_stack():
    print(integer_stack)

def ex_loop(stack, word_pointer):
    print("do branch")
    global jump_flag
    jump_flag = True
    print("jump_flag :", jump_flag)
    return 0

def cond_branch(stack, word_pointer):
    print("do cond branch")
    global jump_flag
    if len(stack) > 0:
        cond = stack.pop()
        if cond == 1:
            jump_flag = True
        return 0
    return -1

def save_pointer(stack, word_pointer):
    return_stack.append(word_pointer)
    return 0

def ex_if(stack, word_pointer):
    global jump_flag
    if len(stack) > 0:
        condition = stack.pop()
        if condition != 1:
            jump_flag = True
        return 0
    return -1

def ex_else(stack, word_pointer):
    #if i reach an else, i need to skip 
    #seek the end and jump there ?
    global jump_flag
    jump_flag = True
    return 0

def ex_comparison(stack, comparator):
    if check_elements_on_stack(stack, 2) :
        num1 = stack.pop()
        num2 = stack.pop()
        if num1 == None or num2 == None:
            print("None error")
            return -1
        match comparator :            
            case "<":
                stack.append(1 if num1 < num2 else 0),
            case ">":
                stack.append(1 if num1 > num2 else 0),
            case "<=":
                stack.append(1 if num1 <= num2 else 0),
            case ">=":
                stack.append(1 if num1 >= num2 else 0),
            case "==":
                stack.append(1 if num1 == num2 else 0),
            case "!=":
                stack.append(1 if num1 != num2 else 0),
            case _:
                print("Error")
        
        return 0
    else:
        return -1

def ex_lt():
    return ex_comparison(integer_stack, '<')

def ex_gt():
    return ex_comparison(integer_stack, '>')

def ex_lte():
    return ex_comparison(integer_stack, '<=')

def ex_gte():
    return ex_comparison(integer_stack, '>=')

def ex_e():
   return ex_comparison(integer_stack, '==')

def ex_nt():
    return ex_comparison(integer_stack, '!=')

def seek(words, word, word_pointer = 0):
    try:
        return words.index(word, word_pointer)
    except ValueError:
        return -1

def execute(instruction):
    if instruction != None:
        func_to_call = None
        dict_index = instruction["ptr"]
        if dict_index != None:
            dict_entry = linked_dict[dict_index]
            for instruction in dict_entry["code"]:
                execute(instruction)
        elif instruction["f"] != None:
            instruction["f"]()
        elif instruction["lit"] != None:
            integer_stack.append(instruction["lit"])

def interpret(word): # return code, message
    code = None
    link = latest

    while link != None:
        dict_entry = linked_dict[link]
        # print(dict_entry)
        if dict_entry == None:
            return -1, f"{word} , ?"

        if dict_entry["name"] == word:
            code = dict_entry["code"]
            break
        else:
            link = dict_entry["link"]
    
    if code == None:
        return -1, f"{word} code not found"
    
    #actual execution
    for instruction in code:
        error = execute(instruction)
        if error == -1:
            return -1, "Error"
    return 0, "Ok"

def search_word(word): #return the link of a word that is present
    link = latest

    while link != None:
        dict_entry = linked_dict[link]
        # print(dict_entry)
        if dict_entry["link"] == None: #dict_entry can't be None, but the link yes reached the end of the dictionary
            return -1
        if dict_entry["name"] == word:
            return link
        link = dict_entry["link"]
    
    # return -1 #moved all the list and not foud

def isNumber(word):
    try: 
        number = int(word)
        return True
    except ValueError:
        return False

def interpreter(filename, outputfile, table_name, split, separator) :
    global jump_flag
    global isp
    global compile_flag

    now = datetime.datetime.now()
    format_date = now.strftime('%Y-%m-%d_%H-%M-%S')

    # output_path = Path(outputfile)

    # outputName = f'{outputfile}'
    # in_file = open(filename, 'r')
    
    compilation_prog = []
    func_name = None

    end = False
    while not end:
        input_code = input(">> ")
        
        if input_code == "q":
            end = True
            continue
        
        words = input_code.strip().split(" ")
        print(words)

        #execution one word at a time
        # run = True
        text_result = "Ok"
        for word in words:
            if compile_flag :
                #consume and create an entry in the dict
                end_compile = seek(words,";")

                if end_compile < 0:
                    text_result = f"compilation error ; not found"
                    break
                
                to_compile = words[1:end_compile]

                #no numbers
                function_name = to_compile[0]

                if isNumber(function_name):
                    compile_flag = False
                    text_result = f"error number as label, {function_name}"
                    break
                
                compiled = []
                for code in to_compile[1:] :
                    # print("code:", code)
                    link = None
                    func_call = None
                    lit = None
                    if isNumber(code):
                        lit = int(code)
                    else:                        
                        link = search_word(code)
                        # print("code:", code, "link:", link)
                        if link == -1:
                            text_result = f"Error word not found"
                            break #this will be a good time where the label on the loops is good
                    
                    compiled.append(make_instruction(link, func_call, lit))
                
                if link == -1:
                    text_result = f"Error word {code} not found"
                    break
                
                add_dict_entry(function_name, 0, compiled)
                print("last dictionary entry:", linked_dict[latest])
                compile_flag = False
                text_result = "Ok"
                break 
            else:                
                if isNumber(word):
                    number = int(word)
                    integer_stack.append(number)
                else:
                    code, text_result = interpret(word)
                    if code == -1:
                        break
        print(text_result)
        
    print(f'END ------------------------ ')


def add_dict_entry(name, flags, code):
    global latest
    global linked_dict

    tmp = {
        "link" : latest, #or latest
        "name" : name,
        "flags" : 0,
        "code" : code #of pointer to function, the first is DOCOL, and the last is NEXT
    }
    linked_dict.append(tmp)
    latest = len(linked_dict) - 1

def make_instruction(link, func_call, lit = None):
    return {
        "ptr" : link,
        "f" : func_call,
        "lit": lit
    }

def main(argv):
    global latest

    inputfile = ''
    outputfile = ''
    table_name = ''
    split = False
    separator = ';'

    try:
        opts, args = getopt.getopt(argv,"hi:o:t:s:p:",["ifile=","ofile=", "table=", "split=", "sep="])
    except getopt.GetoptError:
        print ('test.py -i <inputfile> -o <outputfile>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print ('test.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
        elif opt in ("-t", "--table"):
            table_name = arg
        elif opt in ("-s", "--split"):
            try:
                print("split:", arg)
                split = int(arg)
            except ValueError:
                print("ERR value not a number")
                split = -1
        elif opt in ("-p", "--sep"):
            separator = arg
    
    # print ('Input file is ', inputfile)
    # print ('Output file is ', outputfile)
    # print ('table_name is ', table_name)
    # print ('split is ', split)
    # print ('separetor is ', separator)

    # start = time.perf_counter()

    # init the dictionary
    # sry using the system stack these are useless
    # add_dict_entry("DOCOL", 0, [docol, nextf]) 
    # add_dict_entry("NEXT", 0, [docol, nextf])

    add_dict_entry(".", 0, [make_instruction(None, emit)])
    add_dict_entry("+", 0, [make_instruction(None, add)])
    add_dict_entry(".s", 0, [make_instruction(None, print_stack)])

    add_dict_entry("<", 0, [make_instruction(None, ex_lt)])
    add_dict_entry(">", 0, [make_instruction(None, ex_gt)])
    add_dict_entry("<=", 0, [make_instruction(None, ex_lte)])
    add_dict_entry(">=", 0, [make_instruction(None, ex_gte)])
    add_dict_entry("==", 0, [make_instruction(None, ex_e)])
    add_dict_entry("!=", 0, [make_instruction(None, ex_nt)])

    add_dict_entry(":", 0, [make_instruction(None, enter_compilation)])

    interpreter(inputfile, outputfile, table_name, split, separator)

    # end = time.perf_counter()
    # elapsed = end - start
    # print(f'Time taken: {elapsed:.6f} seconds')

if __name__ == "__main__":
   main(sys.argv[1:])