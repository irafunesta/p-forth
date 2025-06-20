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
# top_of_stack = 0 #maybe
# word_pointer = 0
skip_stack = []
skip_top = 0

vars_stack = []
vars_top = 0

return_stack = []
return_top = 0

string_print_flag = False
string_delimiter = '"'

# isp = 0

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

def enter_string_mode():
    global string_print_flag
    string_print_flag = True

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

# def ex_loop(stack, word_pointer):
#     print("do branch")
#     global jump_flag
#     jump_flag = True
#     print("jump_flag :", jump_flag)
#     return 0

# def cond_branch(stack, word_pointer):
#     print("do cond branch")
#     global jump_flag
#     if len(stack) > 0:
#         cond = stack.pop()
#         if cond == 1:
#             jump_flag = True
#         return 0
#     return -1

# def save_pointer(stack, word_pointer):
#     return_stack.append(word_pointer)
#     return 0

# def ex_if(stack, word_pointer):
#     global jump_flag
#     if len(stack) > 0:
#         condition = stack.pop()
#         if condition != 1:
#             jump_flag = True
#         return 0
#     return -1

# def ex_else(stack, word_pointer):
#     #if i reach an else, i need to skip 
#     #seek the end and jump there ?
#     global jump_flag
#     jump_flag = True
#     return 0

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

def ex_eq_top():
    global jump_flag
    #top of stack is equal to 0
    if len(integer_stack) > 0:
        num1 = integer_stack.pop()
        if num1 != 0:
            jump_flag = True
        return 0
    return -1

def ex_nt():
    return ex_comparison(integer_stack, '!=')

def drop():
    if len(integer_stack) > 0:
        integer_stack.pop()
        return 0
    return -1

def swap():
    if len(integer_stack) > 1:
        num1 = integer_stack.pop()
        num2 = integer_stack.pop()
        integer_stack.append(num1)
        integer_stack.append(num2)
        return 0
    return -1

def dup():
    if len(integer_stack) > 0:
        num1 = integer_stack.pop()
        integer_stack.append(num1)
        integer_stack.append(num1)
        return 0
    return -1

def over(): # 1 2 3 -> 1 2 3 2
    if len(integer_stack) > 1:
        num1 = integer_stack[len(integer_stack)-2]
        integer_stack.append(num1)
        return 0
    return -1

def rot(): # ( n1 n2 n3 — n2 n3 n1 )
    if len(integer_stack) > 2:
        num1 = integer_stack.pop() #3
        num2 = integer_stack.pop() #2
        num3 = integer_stack.pop() #1
        integer_stack.append(num2)
        integer_stack.append(num1)
        integer_stack.append(num3)
        return 0
    return -1

def rotl(): # ( a b c ) to ( c a b )
    if len(integer_stack) > 1:
        num1 = integer_stack.pop() #c
        num2 = integer_stack.pop() #b
        num3 = integer_stack.pop() #a
        integer_stack.append(num1)
        integer_stack.append(num3)
        integer_stack.append(num2)
        return 0
    return -1

def increment(value):
    if len(integer_stack) > 0:
        integer_stack[len(integer_stack)-1] += value
        return 0
    return -1

def decrement(value):
    if len(integer_stack) > 0:
        integer_stack[len(integer_stack)-1] -= value
        return 0
    return -1

def incl():
    increment(1)

def incl4():
    increment(4)

def decl():
    decrement(1)

def decl4():
    decrement(4)

def subtract():
    if len(integer_stack) > 1:
        num1 = integer_stack.pop()
        num2 = integer_stack.pop()
        integer_stack.append(num1-num2)
        return 0
    return -1

def mul():
    if len(integer_stack) > 1:
        num1 = integer_stack.pop()
        num2 = integer_stack.pop()
        integer_stack.append(num1*num2)
        return 0
    return -1

def mod_primitive():
    if len(integer_stack) > 1:
        num1 = integer_stack.pop() #3
        num2 = integer_stack.pop() #5
        quot_rem = divmod(num2, num1)
        integer_stack.append(quot_rem[1])
        integer_stack.append(quot_rem[0])
        return 0
    return -1

def ex_mod():
    if len(integer_stack) > 1:
        num1 = integer_stack.pop() #3
        num2 = integer_stack.pop() #5
        if num2 == 0:
            return -1
        quot_rem = num2 % num1
        integer_stack.append(quot_rem)
        return 0
    return -1

def branch(): #always jump to the next value on top of stack

    #get the value to change from the stack, last pointed
    global skip_top
    global skip_stack
    # global jump_flag

    
    if len(integer_stack) > 0:
        jump_len = integer_stack.pop()
        skip_stack[skip_top - 1] += jump_len
        return 0
    return -1

def cond_branch(): #if top of stack is 1, jump to the next value on top of stack
    #this need a flag cause if the jump need to be done is managed by another function
    global skip_top
    global skip_stack
    global jump_flag

    if len(integer_stack) > 0:
        jump_len = integer_stack.pop()
        # cond = integer_stack.pop()
        if jump_flag:
            skip_stack[skip_top - 1] += jump_len #i want to skip the prev stack execution
            jump_flag = False
        return 0
    return -1

def ex_do():
    global vars_stack
    global vars_top
    global return_stack

    if len(integer_stack) > 1:
        starting = integer_stack.pop() #0
        end = integer_stack.pop() #10
        # print("starting:",starting)
        # print("end:", end)
        # print("skip_stack[skip_top]:",skip_stack[skip_top-1]) #can use this to set the loop skipping ?

        vars_stack[skip_top-1]["i"] = starting
        vars_stack[skip_top-1]["count"] = end
        return_stack[skip_top-1] = skip_stack[skip_top-1]

        # no, cause i need to have the loop position
        # but if we make the do, olny set variables for i, count and ip, then the loop word actually do the check and jump
        return 0
    return -1

def ex_loop():
    global vars_stack
    global return_stack

    current_i = vars_stack[skip_top-1]["i"] #0
    end = vars_stack[skip_top-1]["count"]

    # print("current_i:",current_i)
    # print("end:", end)
    # print("skip_stack[skip_top]:",skip_stack[skip_top-1])
    # print("return_stak[skip_top]:",return_stack[skip_top-1])

    current_i +=1
    if current_i < end:
        skip_stack[skip_top-1] = return_stack[skip_top-1] #jump back to the do word
        vars_stack[skip_top-1]["i"] = current_i

    return 0

def ex_i():
    global vars_stack
    global return_stack

    current_i = vars_stack[skip_top-1]["i"] #0
   
    # print("starting:",current_i)
    # print("skip_stack[skip_top]:",skip_stack[skip_top-1])
    # print("return_stak[skip_top]:",return_stack[skip_top-1])

    integer_stack.append(current_i)

    return 0  

def ex_dup():
    if len(integer_stack) > 0:
        top_of_stack = integer_stack.pop() #0
        integer_stack.append(top_of_stack) #0
        integer_stack.append(top_of_stack) #0
        return 0
    return -1

def ex_and():
    if len(integer_stack) > 1:
        num1 = integer_stack.pop() #0
        num2 = integer_stack.pop() #0

        bool_1 = convert_to_bool(num1)
        bool_2 = convert_to_bool(num2)

        res = 1 if bool_1 and bool_2 else 0

        integer_stack.append(res) #0
        return 0
    return -1

def ex_or():
    if len(integer_stack) > 1:
        num1 = integer_stack.pop() #0
        num2 = integer_stack.pop() #0

        bool_1 = convert_to_bool(num1)
        bool_2 = convert_to_bool(num2)

        integer_stack.append(convert_to_num(bool_1 or bool_2)) #0
        return 0
    return -1

def ex_invert():
    if len(integer_stack) > 0:
        top_of_stack = integer_stack.pop() #0

        bool_1 = convert_to_bool(top_of_stack)

        integer_stack.append(convert_to_num(not bool_1)) #0
        return 0
    return -1


# ------------------------------------------- END WORDS ---------------------------------------------------

def convert_to_bool(num):
    return True if num == 1 else False

def convert_to_num(bool1):
    return 1 if bool1 == True else 0

def seek(words, word, word_pointer = 0):
    try:
        return words.index(word, word_pointer)
    except ValueError:
        return -1

def execute(instruction):
    #maybe i can use a local (on stack) skip counter
    #TODO we do not return an error here, so how do we fails
    # {'link': 26, 'name': 'buzz', 'flags': 0, 'code': [{'ptr': 25, 'f': None, 'lit': None, 'str': 'print buzz string '}]}
    global skip_top
    global skip_stack
    global return_stack
    global vars_stack

    if instruction != None:
        func_to_call = None
        dict_index = instruction["ptr"]
        if dict_index != None:

            skip_top += 1
            skip_stack[skip_top] = 0
            return_stack[skip_top] = 0
            vars_stack[skip_top] = {}

            dict_entry = linked_dict[dict_index]

            word_pointer = skip_stack[skip_top] #alias for top of call stack
            while word_pointer < len(dict_entry["code"]):
                instruction = dict_entry["code"][word_pointer]
                execute(instruction)
                skip_stack[skip_top] += 1
                word_pointer += skip_stack[skip_top]
            
            skip_top -= 1

        elif instruction["f"] != None:
            return instruction["f"]()
        elif instruction["lit"] != None:
            integer_stack.append(instruction["lit"])
        elif instruction["str"] != None:
            print(instruction["str"])
    

def interpret(word): # return code, message
    code = None
    link = latest

    global skip_top
    global skip_stack
    global return_stack
    global vars_stack
    
    skip_top += 1
    skip_stack[skip_top] = 0
    return_stack[skip_top] = 0
    vars_stack[skip_top] = {}


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
        skip_top -= 1
        return -1, f"{word} code not found"
    


    #actual execution, we need a deeper pointer even here
    #if we use the skip_top stack as a instruction pointer, we should archive it at all levels
    word_pointer = skip_stack[skip_top]

    while word_pointer < len(code):
        instruction = code[word_pointer]
        error = execute(instruction)
        if error == -1:
            skip_top -= 1
            return -1, "Error"
        skip_stack[skip_top] += 1
        word_pointer = skip_stack[skip_top]
    skip_top -= 1
    return 0, "Ok"

def search_word(word): #return the link of a word that is present
    link = latest

    while link != None:
        dict_entry = linked_dict[link]
        # print(dict_entry)
        # if dict_entry["link"] == None: #dict_entry can't be None, but the link yes reached the end of the dictionary
        #     return -1
        if dict_entry["name"] == word:
            return link
        link = dict_entry["link"]
    
    return -1 #moved all the list and not foud

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
    # global word_pointer
    global skip_top
    global skip_stack
    global string_print_flag
    global return_stack
    global vars_stack

    for i in range(0, 100):
        skip_stack.append(0)
        return_stack.append(0)
        vars_stack.append({})
        

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
        # print(words)

        #execution one word at a time
        #can i just expand all the code and have it in a single list ?

        # run = True
        text_result = "Ok"
        
        skip_top = 0
        skip_stack[skip_top] = 0
        return_stack[skip_top] = 0
        vars_stack[skip_top] = {}

        word_pointer = skip_stack[skip_top]

        while word_pointer < len(words):
        # for word_pointer in range(0, len(words)):
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

                pt = 1
                while pt < len(to_compile) :
                    
                    code = to_compile[pt]

                    link = None
                    func_call = None
                    lit = None
                    str = ""

                    if isNumber(code):
                        lit = int(code)
                    elif code == "if":
                        #seek to the else then -> [cond n ?branch]
                        relative_jump = seek(to_compile, "else", 0)
                        if relative_jump == -1:
                            relative_jump = seek(to_compile, "then", 0)
                            if relative_jump == -1:
                                text_result = f"Error misisng else"
                                break #this will be a good time where the label on the loops is good
                        compiled.append(make_instruction(None, None, relative_jump - i))
                        link = search_word("?branch")
                        compiled.append(make_instruction(link, None, None))
                        pt += 1
                        continue
                    elif code == "else":
                        #seek to the then -> [n branch]
                        relative_jump = seek(to_compile, "then", 0)
                        if relative_jump == -1:
                            text_result = f"Error misisng then"
                            break #this will be a good time where the label on the loops is good
                        compiled.append(make_instruction(None, None, relative_jump - i))
                        link = search_word("branch")
                        compiled.append(make_instruction(link, None, None))
                        pt += 1
                        continue
                    elif code == "then":
                        #skip
                        link = 99 #TODO this may cause some problem
                        pt += 1
                        continue
                    else:
                        link = search_word(code)

                        if link == -1:
                            text_result = f"Error word not found"
                            break #this will be a good time where the label on the loops is good

                        #read here the flags ? or understand what the word does eg. ."
                        if code == '."': #TODO this is a hack, need to read something else of the word, or execute it
                            link = None
                            pt += 1
                            delimiter = to_compile[pt]
                            while delimiter != string_delimiter:
                                str += delimiter + " "
                                pt += 1
                                if pt > len(to_compile):
                                    text_result = f"Error misisng string delimiter"
                                    break
                                delimiter = to_compile[pt]
                    
                    compiled.append(make_instruction(link, func_call, lit, str))
                    pt += 1
                
                if link == -1:
                    text_result = f"Error word {code} not found"
                    break
                
                add_dict_entry(function_name, 0, compiled)
                print("last dictionary entry:", linked_dict[latest])
                compile_flag = False
                text_result = "Ok"
                break 
            else:
                # print("word_pointer:",word_pointer)
                word = words[word_pointer]
                # print("word:",word)
                if isNumber(word):
                    number = int(word)
                    integer_stack.append(number)
                elif string_print_flag:
                    string = ""
                    delimiter = word
                    while delimiter != string_delimiter:
                        string += delimiter + " "
                        word_pointer +=1
                        skip_stack[skip_top] += 1
                        delimiter = words[word_pointer]
                    print(string)
                    string_print_flag = False
                else:
                    code, text_result = interpret(word)
                    if code == -1:
                        break
            
            skip_stack[skip_top] += 1
            word_pointer = skip_stack[skip_top]
            
            # print("next word, pointer:", word_pointer)
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

def make_instruction(link, func_call, lit = None, str = None):
    return {
        "ptr" : link,
        "f" : func_call,
        "lit": lit,
        "str": str
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
    add_dict_entry("0=", 0, [make_instruction(None, ex_eq_top)])


    add_dict_entry(":", 0, [make_instruction(None, enter_compilation)])
    add_dict_entry("Drop", 0, [make_instruction(None, drop)])
    add_dict_entry("Swap", 0, [make_instruction(None, swap)])
    add_dict_entry("Over", 0, [make_instruction(None, over)])
    add_dict_entry("Rot", 0, [make_instruction(None, rot)])
    add_dict_entry("-Rot", 0, [make_instruction(None, rotl)])
    add_dict_entry("dup", 0, [make_instruction(None, ex_dup)])
    add_dict_entry("1+", 0, [make_instruction(None, incl)])
    add_dict_entry("1-", 0, [make_instruction(None, decl)])
    add_dict_entry("4+", 0, [make_instruction(None, incl4)])
    add_dict_entry("4-", 0, [make_instruction(None, decl4)])
    add_dict_entry("-", 0, [make_instruction(None, subtract)])
    add_dict_entry("*", 0, [make_instruction(None, mul)])
    add_dict_entry("/Mod", 0, [make_instruction(None, mod_primitive)]) #(5 3 -- 2 1)
    add_dict_entry("mod", 0, [make_instruction(None, ex_mod)]) #(5 3 -- 2)
    add_dict_entry("branch", 0, [make_instruction(None, branch)])
    add_dict_entry("?branch", 0, [make_instruction(None, cond_branch)])
    add_dict_entry('."', 0, [make_instruction(None, enter_string_mode)])
    add_dict_entry('do', 0, [make_instruction(None, ex_do)])
    add_dict_entry('loop', 0, [make_instruction(None, ex_loop)])
    add_dict_entry('i', 0, [make_instruction(None, ex_i)])
    add_dict_entry('and', 0, [make_instruction(None, ex_and)])
    add_dict_entry('or', 0, [make_instruction(None, ex_or)])
    add_dict_entry('invert', 0, [make_instruction(None, ex_invert)])

    

    #testing, add precompiled word
    add_dict_entry("is-zero", 0, [
    {'ptr': 9, 'f': None, 'lit': None}, 
    {'ptr': None, 'f': None, 'lit': 3}, 
    {'ptr': 24, 'f': None, 'lit': None}, 
    {'ptr': None, 'f': None, 'lit': 22}, 
    {'ptr': None, 'f': None, 'lit': 3}, 
    {'ptr': 23, 'f': None, 'lit': None}, 
    {'ptr': None, 'f': None, 'lit': 33}])

    #testing fizz-buzz #TODO this is not compile correctly
    add_dict_entry("fizz?", 0, [
    {'ptr': None, 'f': None, 'lit': 3, 'str': ''},
    {'ptr': 24, 'f': None, 'lit': None, 'str': ''}, 
    {'ptr': 9, 'f': None, 'lit': None, 'str': ''}, 
    {'ptr': None, 'f': None, 'lit': -91, 'str': None}, 
    {'ptr': 26, 'f': None, 'lit': None, 'str': None}, 
    {'ptr': None, 'f': None, 'lit': None, 'str': 'Fizz '}])
    

    interpreter(inputfile, outputfile, table_name, split, separator)

    # end = time.perf_counter()
    # elapsed = end - start
    # print(f'Time taken: {elapsed:.6f} seconds')

if __name__ == "__main__":
   main(sys.argv[1:])

#TODO Strings
# For the strings we need a better way, some code is duplicated
# we are manually checking for the word ." , instead of using the flags or other methods, same for if else then
# the delimiter for the string must be separated by a space, also need to check for the delimiter in words
#   can i do something like ." ". just wondering
# 
